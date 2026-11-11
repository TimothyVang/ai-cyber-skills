#!/usr/bin/env python3
"""Run PR-Agent locally on a GitHub PR, powered by your OAuth subscriptions, not an API key.

Usage:
  python pr_agent_local.py <pr-url> [review|describe|improve|ask "<question>"]
                           [--backend omp|claude] [--model <model>] [--dry-run]

PR-Agent talks to an OpenAI-compatible endpoint. This script serves one on 127.0.0.1 and answers
each request with a tool-less run of an agent CLI you are already logged in to:
- `omp` (default when installed): uses the OAuth logins from omp's /provider (Anthropic, OpenAI
  Codex, ...). The default model is omp's `modelRoles.default` (`omp config get modelRoles`); pass
  any omp model id, e.g. `--model openai-codex/gpt-6-luna:high`. The run has no built-in tools,
  and a config overlay disables every discovery provider, so no MCP server tools load either.
  It runs in an empty temp directory, so no repo config can add them back.
- `claude`: Claude Code's subscription login; the default model is `sonnet`.
API-key environment variables are removed from the child, so a stray key can't turn this into API
billing. GitHub access uses `gh auth token`. --dry-run prints the output instead of posting it.
Needs: `omp` or `claude` (logged in), `gh` (logged in), and `uvx` (or `pr-agent` on PATH).
"""

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PR_AGENT = "pr-agent[github]==0.50.0"
SYSTEM = ("You are the language model behind PR-Agent, a code review tool. The user message holds the "
          "tool's instructions and the pull request data. Follow those instructions exactly and reply with "
          "only the output they ask for, in the format they ask for.")
# Credential-shaped variables (provider API keys, cloud credentials, provider routing switches) are removed
# from every child, so no model call can fall back to API-key or cloud billing. CLAUDE_CODE_OAUTH_TOKEN is
# Claude Code's subscription login and stays; GitHub tokens stay only for `gh` and PR-Agent.
CREDENTIAL = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIALS)(_ID)?$"
                        r"|^(AWS|AZURE|GOOGLE|GCLOUD|VERTEX|BEDROCK|ANTHROPIC|OPENAI|CLAUDE_CODE_USE)_")
KEEP = {"CLAUDE_CODE_OAUTH_TOKEN"}
GITHUB = {"GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"}
# omp's full discovery-provider registry (omp docs, context-files.md). `--no-tools` only drops built-in
# tools; without this overlay omp still loads MCP servers from these sources. `enabledProviders: []`
# also keeps foreign user sources (opencode, claude, ...) off even if the user opted in to them.
OMP_OVERLAY = "enabledProviders: []\ndisabledProviders:\n" + "".join(f"  - {p}\n" for p in (
    "native", "omp-plugins", "claude", "agent-plugins", "codex", "agents", "claude-plugins", "gemini",
    "opencode", "cursor", "windsurf", "cline", "github", "vscode", "agents-md", "claude-md",
    "custom-context", "mcp-json", "ssh-json", "builtin-defaults"))


def _oauth_env(github: bool = False) -> dict:
    keep = KEEP | GITHUB if github else KEEP
    return {k: v for k, v in os.environ.items() if k.upper() in keep or not CREDENTIAL.search(k.upper())}


def _prompt(messages: list[dict]) -> str:
    parts = []
    for message in messages:
        content = message.get("content") or ""
        if isinstance(content, list):  # OpenAI content parts
            content = "\n".join(p.get("text", "") for p in content if isinstance(p, dict))
        parts.append(f"<{message.get('role', 'user')}>\n{content}\n</{message.get('role', 'user')}>")
    return "\n\n".join(parts)


def omp_default_model() -> str:
    """omp's default model role, the one /provider and /model set (honors omp profiles)."""
    proc = subprocess.run([shutil.which("omp") or "omp", "config", "get", "modelRoles", "--json"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", env=_oauth_env())
    if proc.returncode != 0:
        sys.exit(f"pr_agent_local: `omp config get modelRoles` failed: {(proc.stderr or proc.stdout).strip()[-400:]}")
    try:
        return json.loads(proc.stdout)["value"]["default"]
    except (json.JSONDecodeError, KeyError, TypeError):
        sys.exit("pr_agent_local: omp has no modelRoles.default; pick one with /model in omp or pass --model")


def omp_complete(prompt: str, model: str) -> tuple[str, dict]:
    with tempfile.TemporaryDirectory(prefix="pr-agent-omp-") as work:
        with open(os.path.join(work, "request.md"), "w", encoding="utf-8") as fh:
            fh.write(prompt)
        with open(os.path.join(work, "overlay.yml"), "w", encoding="utf-8") as fh:
            fh.write(OMP_OVERLAY)
        proc = subprocess.run(
            [shutil.which("omp") or "omp", "-p", "--mode", "json", "--no-session", "--no-title", "--no-tools",
             "--no-skills", "--no-rules", "--no-context-files", "--no-extensions", "--no-lsp",
             "--config", "overlay.yml", "--model", model, "--system-prompt", SYSTEM, "@request.md",
             "Answer the attached PR-Agent request."],
            cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace", env=_oauth_env(),
            timeout=900,
        )
    text, prompt_tokens, completion_tokens = "", 0, 0
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        message = event.get("message") if isinstance(event.get("message"), dict) else {}
        if event.get("type") == "message_end" and message.get("role") == "assistant":
            usage = message.get("usage") or {}
            prompt_tokens += (usage.get("input") or 0) + (usage.get("cacheRead") or 0) + (usage.get("cacheWrite") or 0)
            completion_tokens += usage.get("output") or 0
            chunks = [c.get("text", "") for c in message.get("content") or []
                      if isinstance(c, dict) and c.get("type") == "text"]
            if any(c.strip() for c in chunks):
                text = "\n".join(chunks)
    if proc.returncode != 0 or not text.strip():
        raise RuntimeError(f"omp exited {proc.returncode}: {(proc.stderr or 'no assistant text')[-800:]}")
    return text, {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}


def claude_complete(prompt: str, model: str) -> tuple[str, dict]:
    with tempfile.TemporaryDirectory(prefix="pr-agent-claude-") as work:  # no project settings or CLAUDE.md
        proc = subprocess.run(
            [shutil.which("claude") or "claude", "-p", "--model", model, "--output-format", "json", "--tools", "",
             "--strict-mcp-config", "--setting-sources", "user", "--settings", '{"disableAllHooks": true}',
             "--no-session-persistence", "--system-prompt", SYSTEM],
            input=prompt, cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=_oauth_env(), timeout=900,
        )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"claude exited {proc.returncode}: {(proc.stderr or proc.stdout)[-800:]}")
    if data.get("is_error"):
        raise RuntimeError(f"claude error: {str(data.get('result'))[:800]}")
    usage = data.get("usage") or {}
    return data.get("result") or "", {
        "prompt_tokens": (usage.get("input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0)
        + (usage.get("cache_creation_input_tokens") or 0),
        "completion_tokens": usage.get("output_tokens") or 0,
    }


BACKENDS = {"omp": omp_complete, "claude": claude_complete}


def complete(messages: list[dict], backend: str, model: str) -> tuple[str, dict]:
    return BACKENDS[backend](_prompt(messages), model)


def make_handler(backend: str, model: str, log: list, secret: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _json(self, code: int, body: dict) -> None:
            raw = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _authorized(self) -> bool:
            # Only PR-Agent, holding this run's secret, may reach the subscription.
            host = (self.headers.get("Host") or "").split(":")[0]
            if host in ("127.0.0.1", "localhost") and self.headers.get("Authorization") == f"Bearer {secret}":
                return True
            self._json(401, {"error": {"message": "unauthorized"}})
            return False

        def do_GET(self):  # model listing, for clients that probe it
            if self._authorized():
                self._json(200, {"object": "list", "data": [{"id": "subscription", "object": "model"}]})

        def do_POST(self):
            if not self._authorized():
                return
            if not self.path.rstrip("/").endswith("/chat/completions"):
                self._json(404, {"error": {"message": f"unsupported path {self.path}"}})
                return
            try:
                request = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            except (ValueError, TypeError):
                request = None
            messages = request.get("messages", []) if isinstance(request, dict) else None
            if not isinstance(messages, list) or not all(isinstance(m, dict) for m in messages):
                self._json(400, {"error": {"message": "invalid request body"}})
                return
            started = time.monotonic()
            try:
                text, usage = complete(request.get("messages", []), backend, model)
            except Exception as exc:  # reported to PR-Agent as an API error
                self._json(500, {"error": {"message": str(exc), "type": "server_error"}})
                return
            log.append({"seconds": round(time.monotonic() - started, 1), "text": text, **usage})
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            created = int(time.time())
            if request.get("stream"):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                for delta, finish in (({"role": "assistant", "content": text}, None), ({}, "stop")):
                    chunk = {"id": "chatcmpl-local", "object": "chat.completion.chunk", "created": created,
                             "model": request.get("model", "subscription"),
                             "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                self.wfile.write(b"data: [DONE]\n\n")
                return
            self._json(200, {
                "id": "chatcmpl-local", "object": "chat.completion", "created": created,
                "model": request.get("model", "subscription"),
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                "usage": usage,
            })

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pr_url")
    parser.add_argument("command", nargs="?", default="review")
    parser.add_argument("args", nargs="*", help="extra words for the command, e.g. the question for ask")
    parser.add_argument("--backend", choices=sorted(BACKENDS), help="omp (default when installed) or claude")
    parser.add_argument("--model", help="omp: any omp model id (default: omp's modelRoles.default); claude: alias or id (default sonnet)")
    parser.add_argument("--dry-run", action="store_true", help="print the result instead of posting it")
    opts = parser.parse_args()

    backend = opts.backend or ("omp" if shutil.which("omp") else "claude")
    for tool in (backend, "gh"):
        if not shutil.which(tool):
            sys.exit(f"pr_agent_local: `{tool}` is not on PATH")
    model = opts.model or (omp_default_model() if backend == "omp" else "sonnet")
    token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                           env=_oauth_env(github=True)).stdout.strip()
    if not token:
        sys.exit("pr_agent_local: `gh auth token` returned nothing; run `gh auth login`")

    calls: list = []
    secret = secrets.token_urlsafe(32)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(backend, model, calls, secret))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/v1"

    runner = [shutil.which("pr-agent")] if shutil.which("pr-agent") else [shutil.which("uvx") or "uvx", "--from", PR_AGENT, "pr-agent"]
    env = _oauth_env()
    env.update({
        "CONFIG__GIT_PROVIDER": "github",
        "CONFIG__MODEL": "openai/subscription",
        "CONFIG__FALLBACK_MODELS": "[]",
        # PR-Agent caps every model at max_model_tokens (32000 by default) and prunes the diff to fit.
        "CONFIG__CUSTOM_MODEL_MAX_TOKENS": "150000",
        "CONFIG__MAX_MODEL_TOKENS": "150000",
        "CONFIG__PUBLISH_OUTPUT": "false" if opts.dry_run else "true",
        "OPENAI__KEY": secret,
        "OPENAI__API_BASE": base,
        "OPENAI_API_BASE": base,
        "GITHUB__USER_TOKEN": token,
        "PYTHONIOENCODING": "utf-8",
    })
    command = [*runner, "--pr_url", opts.pr_url, opts.command, *opts.args]
    code = subprocess.run(command, env=env).returncode
    server.shutdown()
    spent = sum(c["seconds"] for c in calls)
    print(f"\npr_agent_local: {len(calls)} model call(s) through {backend} ({model}), {spent:.0f}s, "
          f"{sum(c['prompt_tokens'] for c in calls)} in / {sum(c['completion_tokens'] for c in calls)} out tokens",
          file=sys.stderr)
    if not calls and code == 0:
        print("pr_agent_local: PR-Agent made no model calls; check its output above", file=sys.stderr)
    if opts.dry_run:
        # With publishing off PR-Agent prints nothing, so show what the model returned.
        for number, call in enumerate(calls, 1):
            print(f"\n----- model output {number} -----\n{call['text']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
