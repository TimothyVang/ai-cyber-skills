#!/usr/bin/env python3
"""The bots' GitHub App: create it, and mint installation tokens so bots post as the app.

    py -3 ghapp.py setup [--name <brand>-<login>] [--org <org>] [--no-browser]
    py -3 ghapp.py token --repo <owner/repo>      # prints a 1-hour installation token
    py -3 ghapp.py whoami                          # app slug, bot login, installations

`setup` runs GitHub's app-manifest flow: a page on 127.0.0.1 posts the manifest to GitHub, you click
"Create GitHub App", GitHub redirects back with a one-time code, and the code becomes the app's id and
private key. Both stay in ~/.config/<brand>/ (outside every repo). Then install the app on the repos the
bots may work in; installing is the opt-in, like any review app.

Model calls never go through the app. It is only the bots' GitHub identity. JWTs are signed with the
`openssl` CLI (Git for Windows ships one), so this needs nothing beyond the standard library.
"""
import argparse
import base64
import html
import email.utils
import http.server
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from brand import BRAND, CONFIG_DIR

CONFIG_PATH = CONFIG_DIR / "github-app.json"
TOKEN_CACHE = CONFIG_DIR / "token-cache.json"
API = "https://api.github.com"

PERMISSIONS = {
    "contents": "write",
    "pull_requests": "write",
    "issues": "write",
    "checks": "read",
    "statuses": "read",
    "actions": "read",
    "metadata": "read",
}


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        sys.exit(f"no app configured at {CONFIG_PATH}; run `ghapp.py setup` first")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def app_jwt(config: dict) -> str:
    now = int(time.time())
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    payload = b64url(json.dumps({"iat": now - 60, "exp": now + 540, "iss": str(config["client_id"])}).encode())
    signing_input = f"{header}.{payload}".encode()
    openssl = shutil.which("openssl") or r"C:\Program Files\Git\usr\bin\openssl.exe"
    proc = subprocess.run([openssl, "dgst", "-sha256", "-sign", config["private_key_path"]],
                          input=signing_input, capture_output=True, check=True)
    return f"{header}.{payload}.{b64url(proc.stdout)}"


class RequestError(RuntimeError):
    def __init__(self, method: str, path: str, status: int, detail: str):
        self.status = status
        super().__init__(f"{method} {path} -> {status}: {detail}")


class RateLimited(RuntimeError):
    """A GitHub read budget is unavailable until retry_at (Unix seconds)."""

    def __init__(self, retry_at: float, reason: str):
        self.retry_at, self.reason = retry_at, reason
        super().__init__(f"{reason}; discovery paused until "
                         f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(retry_at))}")


def rate_limit(headers, detail: str):
    now, deadlines, reasons = time.time(), [], []
    if headers.get("X-RateLimit-Remaining") == "0":
        try:
            deadlines.append(float(headers.get("X-RateLimit-Reset", "")))
            reasons.append("GitHub primary rate limit exhausted")
        except ValueError:
            deadlines.append(now + 60)
            reasons.append("GitHub primary rate limit exhausted (no reset supplied)")
    retry = headers.get("Retry-After")
    if retry:
        try:
            deadline = now + float(retry)
        except ValueError:
            try:
                deadline = email.utils.parsedate_to_datetime(retry).timestamp()
            except (TypeError, ValueError, OverflowError):
                deadline = now + 60
        deadlines.append(deadline)
        reasons.append("GitHub secondary rate limit (Retry-After)")
    if not deadlines and ("rate limit" in detail.lower() or "abuse detection" in detail.lower()):
        deadlines.append(now + 60)
        reasons.append("GitHub rate limit (no reset supplied; waiting 60 seconds)")
    return RateLimited(max(now + 1, *deadlines), "; ".join(reasons)) if deadlines else None


def request(method: str, path: str, token: str | None = None, body: dict | None = None, bearer=True):
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", f"{BRAND['name']}-ghapp")
    if token:
        req.add_header("Authorization", f"{'Bearer' if bearer else 'token'} {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")[:400]
        limited = rate_limit(err.headers, detail) if err.code in (403, 429) else None
        if limited:
            raise limited from None
        raise RequestError(method, path, err.code, detail) from None


def installations(config: dict) -> list[dict]:
    token, rows, page = app_jwt(config), [], 1
    while True:
        batch = request("GET", f"/app/installations?per_page=100&page={page}", token) or []
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        page += 1


def installation_for(config: dict, repo: str) -> int:
    return request("GET", f"/repos/{repo}/installation", app_jwt(config))["id"]


def installation_token(config: dict, installation_id: int) -> str:
    cache = json.loads(TOKEN_CACHE.read_text(encoding="utf-8")) if TOKEN_CACHE.is_file() else {}
    hit = cache.get(str(installation_id))
    if hit and hit["expires"] - time.time() > 600:
        return hit["token"]
    reply = request("POST", f"/app/installations/{installation_id}/access_tokens", app_jwt(config), {})
    expires = time.mktime(time.strptime(reply["expires_at"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    cache[str(installation_id)] = {"token": reply["token"], "expires": expires}
    TOKEN_CACHE.write_text(json.dumps(cache), encoding="utf-8")
    try:
        os.chmod(TOKEN_CACHE, 0o600)
    except OSError:
        pass
    return reply["token"]


def repo_token(repo: str) -> str:
    config = load_config()
    return installation_token(config, installation_for(config, repo))


def installation_repos(config: dict, installation_id: int) -> list[str]:
    token = installation_token(config, installation_id)
    names, page = [], 1
    while True:
        reply = request("GET", f"/installation/repositories?per_page=100&page={page}", token, bearer=False)
        names += [r["full_name"] for r in reply["repositories"]]
        if len(names) >= reply["total_count"] or not reply["repositories"]:
            return names
        page += 1


def bot_login(config: dict) -> str:
    return f"{config['slug']}[bot]"


def setup(args) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.is_file() and not args.force:
        sys.exit(f"{CONFIG_PATH} exists (app {load_config()['slug']}); pass --force to create another app")
    login = subprocess.run(["gh", "api", "user", "-q", ".login"], capture_output=True, text=True).stdout.strip()
    name = args.name or f"{BRAND['name']}-{login.lower()}"[:34]
    state = secrets.token_urlsafe(16)
    done = threading.Event()
    result: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, body: str, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode())

        def do_GET(self):
            port = self.server.server_address[1]
            if self.path in ("/", "/start"):
                manifest = {
                    "name": name,
                    "url": BRAND["homepage"],
                    "description": BRAND["description"],
                    "redirect_url": f"http://127.0.0.1:{port}/callback",
                    "public": False,
                    "default_permissions": PERMISSIONS,
                    "default_events": [],
                    "hook_attributes": {"url": "https://example.com/polls-instead", "active": False},
                }
                target = (f"https://github.com/organizations/{args.org}/settings/apps/new" if args.org
                          else "https://github.com/settings/apps/new") + f"?state={state}"
                self.reply(f"""<!doctype html><title>{html.escape(BRAND['name'])} app</title>
<form id=f action="{target}" method=post>
<input type=hidden name=manifest value="{html.escape(json.dumps(manifest))}">
<button>Create the {html.escape(name)} GitHub App</button></form>
<script>document.getElementById('f').submit()</script>""")
                return
            if self.path.startswith("/callback"):
                from urllib.parse import parse_qs, urlparse
                query = parse_qs(urlparse(self.path).query)
                if query.get("state", [""])[0] != state:
                    self.reply("state mismatch", 400)
                    return
                try:
                    result.update(request("POST", f"/app-manifests/{query['code'][0]}/conversions"))
                except RuntimeError as err:
                    self.reply(html.escape(str(err)), 500)
                    result["error"] = str(err)
                    done.set()
                    return
                self.reply(f"<p>Created. Now install it: <a href='{result['html_url']}/installations/new'>"
                           f"{result['html_url']}/installations/new</a></p>")
                done.set()
                return
            self.reply("not found", 404)

    server = http.server.HTTPServer(("127.0.0.1", args.port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    start = f"http://127.0.0.1:{server.server_address[1]}/start"
    print(f"open {start} and click 'Create GitHub App'", flush=True)
    if not args.no_browser:
        webbrowser.open(start)
    if not done.wait(timeout=args.timeout):
        server.shutdown()
        sys.exit("timed out waiting for GitHub's redirect")
    server.shutdown()
    if "error" in result:
        sys.exit(result["error"])
    key_path = CONFIG_DIR / f"{result['slug']}.private-key.pem"
    key_path.write_text(result["pem"], encoding="utf-8")
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass
    # `owner` is the human running the bots (PR and issue authors are people); the app may belong to an org.
    config = {"app_id": result["id"], "client_id": result["client_id"], "slug": result["slug"],
              "html_url": result["html_url"], "owner": login, "app_owner": result["owner"]["login"],
              "private_key_path": str(key_path)}
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(json.dumps({"slug": config["slug"], "bot": bot_login(config),
                      "install": f"{config['html_url']}/installations/new", "config": str(CONFIG_PATH)}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup")
    s.add_argument("--name")
    s.add_argument("--org")
    s.add_argument("--port", type=int, default=0)
    s.add_argument("--timeout", type=int, default=900)
    s.add_argument("--no-browser", action="store_true")
    s.add_argument("--force", action="store_true")
    t = sub.add_parser("token")
    t.add_argument("--repo", required=True)
    sub.add_parser("whoami")
    args = parser.parse_args()
    if args.cmd == "setup":
        setup(args)
    elif args.cmd == "token":
        sys.stdout.buffer.write(repo_token(args.repo).encode() + b"\n")  # bytes: a Windows \r would end up in $(...)
    else:
        config = load_config()
        installs = installations(config)
        print(json.dumps({"slug": config["slug"], "bot": bot_login(config), "installations": [
            {"id": i["id"], "account": i["account"]["login"], "selection": i["repository_selection"]}
            for i in installs]}, indent=2))


if __name__ == "__main__":
    main()
