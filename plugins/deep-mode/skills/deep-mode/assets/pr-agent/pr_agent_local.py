#!/usr/bin/env python3
"""Run PR-Agent locally on a GitHub PR, powered by your Claude subscription through Claude Code.

Usage:
  python pr_agent_local.py <pr-url> [review|describe|improve|ask "<question>"] [--model sonnet] [--dry-run]

PR-Agent talks to an OpenAI-compatible endpoint. This script serves one on 127.0.0.1 and answers
each request by running `claude -p` with no tools, so the calls go through your logged-in Claude
Code subscription (OAuth), not an API key. ANTHROPIC_API_KEY is removed from Claude's environment so
a stray key can't turn this into API billing. GitHub access uses `gh auth token`.
--dry-run prints PR-Agent's output instead of posting it on the PR.
Needs: `claude` (logged in), `gh` (logged in), and `uvx` (or `pr-agent` on PATH).
"""

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PR_AGENT = "pr-agent[github]==0.50.0"
SYSTEM = ("You are the language model behind PR-Agent, a code review tool. The user message holds the "
          "tool's instructions and the pull request data. Follow those instructions exactly and reply with "
          "only the output they ask for, in the format they ask for.")


def claude_complete(messages: list[dict], model: str) -> tuple[str, dict]:
    parts = []
    for message in messages:
        content = message.get("content") or ""
        if isinstance(content, list):  # OpenAI content parts
            content = "\n".join(p.get("text", "") for p in content if isinstance(p, dict))
        parts.append(f"<{message.get('role', 'user')}>\n{content}\n</{message.get('role', 'user')}>")
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    proc = subprocess.run(
        [shutil.which("claude") or "claude", "-p", "--model", model, "--output-format", "json", "--tools", "",
         "--no-session-persistence", "--system-prompt", SYSTEM],
        input="\n\n".join(parts), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
        timeout=900,
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


def make_handler(model: str, log: list, secret: str):
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

        def do_GET(self):  # model listing, for clients that probe it
            self._json(200, {"object": "list", "data": [{"id": "subscription", "object": "model"}]})

        def do_POST(self):
            # Only PR-Agent, holding this run's secret, may spend the subscription.
            host = (self.headers.get("Host") or "").split(":")[0]
            if host not in ("127.0.0.1", "localhost") or self.headers.get("Authorization") != f"Bearer {secret}":
                self._json(401, {"error": {"message": "unauthorized"}})
                return
            if not self.path.rstrip("/").endswith("/chat/completions"):
                self._json(404, {"error": {"message": f"unsupported path {self.path}"}})
                return
            try:
                request = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            except (ValueError, TypeError):
                self._json(400, {"error": {"message": "invalid request body"}})
                return
            started = time.monotonic()
            try:
                text, usage = claude_complete(request.get("messages", []), model)
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
    parser.add_argument("--model", default="sonnet", help="Claude Code model alias or id (default sonnet)")
    parser.add_argument("--dry-run", action="store_true", help="print the result instead of posting it")
    opts = parser.parse_args()

    for tool in ("claude", "gh"):
        if not shutil.which(tool):
            sys.exit(f"pr_agent_local: `{tool}` is not on PATH")
    token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    if not token:
        sys.exit("pr_agent_local: `gh auth token` returned nothing; run `gh auth login`")

    calls: list = []
    secret = secrets.token_urlsafe(32)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(opts.model, calls, secret))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/v1"

    runner = [shutil.which("pr-agent")] if shutil.which("pr-agent") else [shutil.which("uvx") or "uvx", "--from", PR_AGENT, "pr-agent"]
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")}
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
    print(f"\npr_agent_local: {len(calls)} model call(s) through Claude Code ({opts.model}), {spent:.0f}s, "
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
