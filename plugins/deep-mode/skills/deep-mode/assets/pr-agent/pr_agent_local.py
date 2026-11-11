#!/usr/bin/env python3
"""Run PR-Agent locally on a GitHub PR, powered by the subscription your agent harness is logged into.

Usage:
  python pr_agent_local.py <pr-url> [review|describe|improve|ask "<question>"] [--model M] [--dry-run]

PR-Agent talks to an OpenAI-compatible endpoint. This script serves one on 127.0.0.1 and answers each
request with `omp -p` on omp's current default model (or --model), so the calls draw on the usage limits of
whatever subscription omp is logged into (Claude Max/Pro, ChatGPT/Codex), never an API key. The child has
no tools, MCP servers, plugins, skills or context files, and `@` mentions in PR text are defanged so omp
never attaches a local file. API-key variables (ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, OPENAI_API_KEY)
are removed from its environment so a stray key can't turn this into API billing. GitHub access uses
`gh auth token`. --dry-run prints PR-Agent's output instead of posting it on the PR.
Needs: `omp` (logged in), `gh` (logged in), and `uvx` (or `pr-agent` on PATH).
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


API_KEY_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY")


def flatten(messages: list[dict]) -> str:
    parts = []
    for message in messages:
        content = message.get("content") or ""
        if isinstance(content, list):  # OpenAI content parts
            content = "\n".join(p.get("text", "") for p in content if isinstance(p, dict))
        parts.append(f"<{message.get('role', 'user')}>\n{content}\n</{message.get('role', 'user')}>")
    # omp attaches the file behind any `@path` in the prompt, so PR text like `@~/.ssh/id_ed25519` would hand
    # a local file to the model and onto the PR. A word joiner after `@` reads the same and never matches.
    return re.sub(r"@(?=\S)", "@\u2060", "\n\n".join(parts))


# `--no-tools` drops only built-in tools: MCP servers from omp's config (and from Claude, Codex, Cursor and
# other imported configs) still mount, and a model reading untrusted PR text could call them. This overlay
# turns off every discovery source for the child run, so it has no tools, no MCP and no plugins. Auth and
# the default model come from omp's own settings, which the overlay leaves alone.
NO_DISCOVERY = ("disabledProviders: [native, claude, claude-plugins, codex, gemini, github, opencode, cursor, "
                "windsurf, vscode, agents-md, agent-plugins, omp-plugins, mcp-json]\n")


def omp_complete(messages: list[dict], model: str | None) -> tuple[str, dict]:
    env = {k: v for k, v in os.environ.items() if k not in API_KEY_VARS}
    with tempfile.TemporaryDirectory(prefix="pr-agent-omp-") as work:
        overlay = os.path.join(work, "no-discovery.yml")
        prompt_path = os.path.join(work, "prompt.txt")  # a file, since PR diffs overflow a Windows command line
        with open(overlay, "w", encoding="utf-8") as handle:
            handle.write(NO_DISCOVERY)
        with open(prompt_path, "w", encoding="utf-8") as handle:
            handle.write(flatten(messages))
        command = [shutil.which("omp") or "omp", "-p", "--mode", "json", "--config", overlay, "--no-tools",
                   "--no-skills", "--no-rules", "--no-context-files", "--no-extensions", "--no-session",
                   "--no-title", "--no-lsp", "--system-prompt", SYSTEM]
        if model:
            command += ["--model", model]
        # cwd is the empty work dir, so no project-level config can add tools back.
        proc = subprocess.run([*command, f"@{prompt_path}"], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env, cwd=work, timeout=900)
    reply = None
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "tool_execution_start":
            # Tripwire: the overlay should leave no tools. If one ran anyway, the run is unsafe; drop it.
            raise RuntimeError(f"omp ran a tool ({event.get('toolName')}) despite --no-tools; reply discarded")
        if (event.get("message") or {}).get("role") == "fileMention":
            # Tripwire: flatten() defangs `@path`; an attached file means a mention got through. Drop it.
            raise RuntimeError("omp attached a mentioned file to the prompt; reply discarded")
        if event.get("type") == "message_end" and (event.get("message") or {}).get("role") == "assistant":
            reply = event["message"]
    if reply is None or proc.returncode != 0:
        raise RuntimeError(f"omp exited {proc.returncode}: {(proc.stderr or proc.stdout)[-800:]}")
    if reply.get("stopReason") != "stop":  # length, aborted or error: never hand PR-Agent a partial reply
        raise RuntimeError(f"omp stopped with {reply.get('stopReason')}: {str(reply.get('errorMessage') or '')[:800]}")
    usage = reply.get("usage") or {}
    text = "".join(part.get("text", "") for part in reply.get("content") or [] if part.get("type") == "text")
    return text, {
        "prompt_tokens": (usage.get("input") or 0) + (usage.get("cacheRead") or 0) + (usage.get("cacheWrite") or 0),
        "completion_tokens": usage.get("output") or 0,
    }


def make_handler(model: str | None, log: list, failures: list, secret: str):
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
            if failures:
                # PR-Agent retries a failed call several times; each retry would spend another omp run.
                self._json(500, {"error": {"message": f"an earlier call failed: {failures[0]}", "type": "server_error"}})
                return
            started = time.monotonic()
            try:
                text, usage = omp_complete(request.get("messages", []), model)
                # The model may echo flatten()'s word joiners; they must not reach suggested code.
                text = text.replace("\u2060", "")
            except Exception as exc:  # reported to PR-Agent as an API error
                failures.append(str(exc)[:300])
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
    parser.add_argument("--model", default=None, help="omp model (default: omp's current model)")
    parser.add_argument("--dry-run", action="store_true", help="print the result instead of posting it")
    opts = parser.parse_args()

    for tool in ("omp", "gh"):
        if not shutil.which(tool):
            sys.exit(f"pr_agent_local: `{tool}` is not on PATH")
    token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    if not token:
        sys.exit("pr_agent_local: `gh auth token` returned nothing; run `gh auth login`")

    calls: list = []
    failures: list = []
    secret = secrets.token_urlsafe(32)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(opts.model, calls, failures, secret))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/v1"

    runner = [shutil.which("pr-agent")] if shutil.which("pr-agent") else [shutil.which("uvx") or "uvx", "--from", PR_AGENT, "pr-agent"]
    env = {k: v for k, v in os.environ.items() if k not in API_KEY_VARS}
    env.update({
        "CONFIG__GIT_PROVIDER": "github",
        "CONFIG__MODEL": "openai/subscription",
        "CONFIG__FALLBACK_MODELS": "[]",
        # PR-Agent caps every model at max_model_tokens (32000 by default) and prunes the diff to fit.
        "CONFIG__CUSTOM_MODEL_MAX_TOKENS": "150000",
        "CONFIG__MAX_MODEL_TOKENS": "150000",
        "CONFIG__PUBLISH_OUTPUT": "false" if opts.dry_run else "true",
        # PR-Agent gives up on a model call after 120 s by default and retries at once, while the abandoned omp
        # child keeps spending usage. Keep its timeout above the child's 900 s, so the child always fails first
        # and the failure circuit stops the retry.
        "CONFIG__AI_TIMEOUT": "960",
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
    print(f"\npr_agent_local: {len(calls)} model call(s) through omp ({opts.model or 'default model'}), "
          f"{spent:.0f}s, "
          f"{sum(c['prompt_tokens'] for c in calls)} in / {sum(c['completion_tokens'] for c in calls)} out tokens",
          file=sys.stderr)
    if failures:
        print(f"pr_agent_local: a model call failed, so the run is incomplete: {failures[0]}", file=sys.stderr)
        return code or 1
    if not calls and code == 0:
        print("pr_agent_local: PR-Agent made no model calls; check its output above", file=sys.stderr)
    if opts.dry_run:
        # With publishing off PR-Agent prints nothing, so show what the model returned.
        for number, call in enumerate(calls, 1):
            print(f"\n----- model output {number} -----\n{call['text']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
