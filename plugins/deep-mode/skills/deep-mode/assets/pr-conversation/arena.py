#!/usr/bin/env python3
"""Play a bot conversation on a PR or issue as an 8-bit battle screen, in the terminal.

Usage:
  python arena.py <thread-url> [<thread-url> ...] | --repo <owner/repo> [--limit 30] [--ascii]
  python arena.py ... --out <file.html> [--open]          (a static page instead)
  python arena.py ... --serve [--port 8765] [--open]      (a live page on 127.0.0.1 instead)

Each bot voice show_thread.py finds (author, reviewer, verifier 1-3, panel, coordinator, PR-Agent)
becomes a sprite and its turn a few dialog boxes built from its gist. By default it plays full-screen
in the terminal (any shell: PowerShell, cmd, bash, zsh), refetching every 15 s so new turns appear
while the conversation runs. Keys: Enter/Space/Right next, Left/B/Backspace back, A auto, L latest,
Esc threads, R refetch, q quit. Colours follow the terminal: truecolor when COLORTERM or Windows
Terminal says so, 256 colours otherwise, none with NO_COLOR; --ascii draws in plain 7-bit text.
When stdout isn't a terminal it prints show_thread's text digest instead.
--repo loads the repo's recently updated PRs and issues that have at least one bot turn, behind a
thread menu. --out writes one self-contained HTML file. --serve serves that page on 127.0.0.1 with
a JSON endpoint the page polls every 15 s.
"""

import argparse
import concurrent.futures
import copy
import datetime
import http.server
import json
import os
import re
import sys
import threading
import time
import webbrowser
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import show_thread as st  # noqa: E402
import arena_tui as tui  # noqa: E402
from arena_tui import fold  # noqa: E402  (one folding table for the canvas font and the terminal)

TEMPLATE = HERE / "arena.html"
FONT = HERE / "font8x8_basic.hex"  # font8x8_basic by Daniel Hepper, public domain (NOTICE.md); 128 glyphs x 8 rows
CACHE_SECONDS = 15
SHA = re.compile(r"^[0-9a-f]{7,40}$")
EFFECT = {"P0": "A critical hit!", "P1": "It's super effective!"}
ANSWER = re.compile(r"^(fixed|dismissed)\b\s*(.*?)(?:\s+in ([0-9a-f]{7,40}))?\s*—\s*(.*)$", re.I)
VOTE = re.compile(r"^vote:\s*(\S+)(?:\s*—\s*(.*))?$", re.I)
DONE = re.compile(r"^VERDICT:\s*((?:NOT )?DONE)", re.I)
TALLY = re.compile(r"(\d+)/(\d+)\s*(PASS|DONE)?", re.I)

# 16x16 sprites, one per voice plus the thread itself: "." is clear, 0-3 the palette, lightest to darkest.
SPRITES = {
    "author": [  # hard hat, holding a pencil
        "....33333333....",
        "...3222222223...",
        "..333333333333..",
        "...3111111113...",
        "...3133113313...",
        "...3133113313...",
        "...3111111113.3.",
        "...3113333113313",
        "....33333333.313",
        ".....3223....313",
        "...33222233..313",
        "..32222222233313",
        "..32222222223313",
        "..3222222222333.",
        "..322222222223..",
        "...333....333...",
    ],
    "reviewer": [  # goggles, magnifier
        "................",
        "....33333333....",
        "...3111111113...",
        "..333333333333..",
        "..300033330003..",
        "..300033330003..",
        "..333333333333..",
        "...3111111113...",
        "...3113333113...",
        "....33333333.33.",
        "...3322222333003",
        "..32222222223003",
        "..3222222223.33.",
        "..32222222233...",
        "..322222222223..",
        "...333....333...",
    ],
    "verifier": [  # shield with a check
        "..333333333333..",
        ".32222222222223.",
        ".32000000000023.",
        ".32000000033023.",
        ".32000000330023.",
        ".32030003300023.",
        ".32033033000023.",
        ".32003330000023.",
        ".32000300000023.",
        ".32000000000023.",
        "..320000000023..",
        "..322000000223..",
        "...3220000223...",
        "....32222223....",
        ".....322223.....",
        "......3333......",
    ],
    "panel": [  # judge: cap, robe, gavel
        "...3333333333...",
        "..322222222223..",
        "...3333333333...",
        "...3111111113...",
        "...3133113313...",
        "...3111111113...",
        "...3113333113...",
        "....33333333....",
        "3333.30000003...",
        "3223.33000033...",
        ".3..3333033333..",
        ".33.3333033333..",
        "..33333330333...",
        "...3333303333...",
        "...3333333333...",
        "...333....333...",
    ],
    "coordinator": [  # antenna, broadcasting
        "..3....33....3..",
        ".3....3113....3.",
        ".3.....33.....3.",
        "..3....33....3..",
        "....33333333....",
        "...3111111113...",
        "...3133113313...",
        "...3111111113...",
        "...3113333113...",
        "....33333333....",
        "...3322222233...",
        "..322200002223..",
        "..322200002223..",
        "..322222222223..",
        "..322222222223..",
        "...333....333...",
    ],
    "pr-agent": [  # hovering eye drone
        "................",
        ".....333333.....",
        "...3311111133...",
        "..311111111113..",
        ".31111333311113.",
        "3311130000311133",
        "3231300330031323",
        "3231300330031323",
        "3311130000311133",
        ".31111333311113.",
        "..311111111113..",
        "...3311111133...",
        ".....333333.....",
        "......3..3......",
        ".....3....3.....",
        "................",
    ],
    "pr": [  # the change: a page of code with eyes
        "..333333333.....",
        "..3000000033....",
        "..30000000303...",
        "..300000003333..",
        "..300000000003..",
        "..303300003303..",
        "..303300003303..",
        "..300000000003..",
        "..302222222203..",
        "..300000000003..",
        "..302222220003..",
        "..300000000003..",
        "..302222222203..",
        "..300000000003..",
        "..333333333333..",
        "................",
    ],
    "issue": [  # the question: a speech bubble
        "................",
        "..333333333333..",
        ".31111111111113.",
        ".31111133111113.",
        ".31111133111113.",
        ".31111133111113.",
        ".31111133111113.",
        ".31111111111113.",
        ".31111133111113.",
        ".31111111111113.",
        "..331133333333..",
        "...3113.........",
        "...313..........",
        "...33...........",
        "................",
        "................",
    ],
}


def thread_label(kind: str, number: int) -> str:
    return f"{'PR' if kind == 'pr' else 'Issue'} #{number}"


def speaker(v: dict) -> str:
    return "PR-AGENT" if v["kind"] == "pr-agent" else v["role"].upper()


def full_name(v: dict) -> str:
    return speaker(v) + (f" ({v['lens']})" if v.get("lens") else "")


def same_head(a: str, b: str) -> bool:
    return a.startswith(b) or b.startswith(a)


def turn_lines(v: dict, first: bool, prev_head: str = "") -> list[str]:
    """One voice's turn as dialog lines: flavour in the framing, the gist's facts verbatim."""
    name, who = full_name(v), speaker(v)
    lines = [f"{name} appeared!" if first else f"{name} returns!"]
    head = v.get("head") or ""
    if SHA.match(head) and SHA.match(prev_head) and not same_head(head, prev_head):
        lines.append(f"The head moved to {head}.")
    gist = v.get("gist") or []
    if v["kind"] == "panel" and gist and (tally := TALLY.search(" ".join(gist))):
        k, n, word = tally.groups()
        lines.append(f"The panel: {k}/{n}" + (f" {word.upper()}." if word else "."))

    def answer(m):  # (action, finding id, commit, reason); a fix with no commit named landed at this turn's head
        action, ident, sha, reason = m.groups()
        action = action.lower()
        return action, ident, sha or (head if action == "fixed" and SHA.match(head) else ""), reason

    moves = Counter(answer(m)[::2] for g in gist if (m := ANSWER.match(g)))
    for g in gist:
        if (m := re.match(r"^(P[012]):\s*(.*)$", g)):
            lines.append(f"It found a {m.group(1)}: {m.group(2)}")
            if m.group(1) in EFFECT:
                lines.append(EFFECT[m.group(1)])
        elif (m := ANSWER.match(g)):
            action, ident, sha, reason = answer(m)
            if (action, sha) in moves:  # one move line per action and commit, then each answer
                count = moves.pop((action, sha))
                lines.append(f"{who} used {'FIX' if action == 'fixed' else 'DISMISS'}!" + (f" x{count}" if count > 1 else "")
                             + (f" (in {sha})" if sha else ""))
            lines.append(f"{ident} — {reason}" if ident else reason)
        elif (m := VOTE.match(g)):
            lines.append(f"{who} voted {m.group(1).upper()}!")
            if m.group(2):
                lines.append(m.group(2))
        elif (m := DONE.match(g)):
            verdict = m.group(1).upper()
            lines.append(f"{who} voted {verdict}!" if v["kind"] == "verifier" else f"{who}'s verdict: {verdict}!")
        elif g.startswith("focus: "):
            lines.append(f"It points at: {g[len('focus: '):]}")
        elif g == "no findings":
            lines.append("It found no findings!")
        else:
            lines.append(g)
    return [fold(line) for line in lines]


def vote_of(v: dict):
    for g in v.get("gist") or []:
        if (m := VOTE.match(g)):
            return "PASS" if m.group(1).upper() == "PASS" else "FAIL"
        if (m := DONE.match(g)):
            return "PASS" if m.group(1).upper() == "DONE" else "FAIL"
    return None


def is_merge_note(v: dict) -> bool:
    return v.get("head") == "merge note" or any(g.startswith("Merged") for g in v.get("gist") or [])


def battle(meta: dict, found: list[dict]) -> dict:
    """A thread ready to draw: intro, each turn's dialog lines and the score after it, and the outro."""
    label = thread_label(meta["kind"], meta["number"])
    merged = meta["state"] == "merged"
    score = {"open": 0, "peak": 0, "votes": [None, None, None], "merged": False}
    seen, head, panel_seen, merge_said, turns = set(), "", False, False, []
    for v in found:
        lines = turn_lines(v, full_name(v) not in seen, head)
        seen.add(full_name(v))
        if SHA.match(v.get("head") or ""):
            head = v["head"]
        gist = v.get("gist") or []
        if v["kind"] in ("reviewer", "pr-agent"):
            score["open"] += sum(1 for g in gist if re.match(r"^P[012]:", g))
        elif v["kind"] == "author":
            score["open"] = max(0, score["open"] - sum(1 for g in gist if ANSWER.match(g)))
        elif v["kind"] == "verifier" and v.get("number") in (1, 2, 3) and (vote := vote_of(v)):
            if panel_seen:  # a new round of votes after an earlier panel
                score["votes"], panel_seen = [None, None, None], False
            score["votes"][v["number"] - 1] = vote
        elif v["kind"] == "panel":
            panel_seen = True
        score["peak"] = max(score["peak"], score["open"])
        if merged and not merge_said and is_merge_note(v):
            lines.append(f"{label} was merged!")
            merge_said, score["merged"] = True, True
        turn = {k: v.get(k) for k in ("id", "html_url", "time", "role", "voice", "kind", "number", "lens",
                                      "agent", "model", "head", "gist")}
        turns.append({**turn, "name": speaker(v), "lines": lines, "after": copy.deepcopy(score)})
    if merged:
        outro = [] if merge_said else [f"{label} was merged!"]
    elif meta["state"] == "closed":
        outro = [f"{label} was closed."]
    else:
        outro = ["The conversation goes on..."]
    intro = [f"{label} wants to merge!" if meta["kind"] == "pr" else f"{label} was opened!", fold(f'"{meta["title"]}"')]
    return {**meta, "label": label, "intro": intro, "turns": turns, "outro": [fold(line) for line in outro]}


def thread_meta(repo: str, issue: dict) -> dict:
    pull = issue.get("pull_request") or {}
    return {"url": issue["html_url"], "repo": repo, "number": issue["number"],
            "kind": "pr" if issue.get("pull_request") else "issue", "title": issue.get("title") or "",
            "state": "merged" if pull.get("merged_at") else issue.get("state", "open")}


def load_thread(repo: str, issue: dict):
    found = [v for c in st.comments(repo, issue["number"]) if (v := st.voice(c, limit=None))]
    return battle(thread_meta(repo, issue), found) if found else None


def gather(urls: list[str], repo: str, limit: int) -> tuple[list[dict], list[str]]:
    """Threads (in order) and per-thread errors. URLs always load; --repo keeps threads with a bot turn."""
    errors = []
    if repo:
        listed = st.gh_json(f"repos/{repo}/issues?state=all&sort=updated&direction=desc&per_page={limit}")
        jobs = [(repo, issue) for issue in listed if issue.get("comments")]
    else:
        def meta(url):
            r, n, _ = st.parse_url(url)
            return r, st.gh_json(f"repos/{r}/issues/{n}")
        jobs = []
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            for url, fut in [(u, pool.submit(meta, u)) for u in urls]:
                try:
                    jobs.append(fut.result())
                except st.GhError as err:
                    errors.append(f"{url}: {err}")
    threads = []
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        for (r, issue), fut in [(job, pool.submit(load_thread, *job)) for job in jobs]:
            try:
                t = fut.result()
            except Exception as err:  # one thread's gh failure or odd content never sinks the others
                errors.append(f"{issue.get('html_url')}: {err}")
                continue
            if t:
                threads.append(t)
            elif not repo:  # an explicit URL with no bot turn yet still shows, as an empty battle
                threads.append(battle(thread_meta(r, issue), []))
    return threads, errors


def payload(threads: list[dict], errors: list[str], live: bool) -> dict:
    return {"generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "live": live, "threads": threads, "errors": errors, "sprites": SPRITES}


def page(data: dict) -> str:
    # \u003c keeps "</script>" and "<!--" in comment text from ending the data block.
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    font = FONT.read_text(encoding="ascii").strip()
    return TEMPLATE.read_text(encoding="utf-8").replace("__FONT_HEX__", font).replace("__ARENA_DATA__", blob)


class Source:
    """The threads behind the page, refetched at most every CACHE_SECONDS."""

    def __init__(self, urls, repo, limit):
        self.urls, self.repo, self.limit = urls, repo, limit
        self.lock = threading.Lock()
        self.data, self.at = None, 0.0

    def get(self, force: bool = False) -> dict:
        with self.lock:
            if force or self.data is None or time.monotonic() - self.at >= CACHE_SECONDS:
                try:
                    threads, errors = gather(self.urls, self.repo, self.limit)
                    self.data = payload(threads, errors, live=True)
                except st.GhError as err:  # keep serving the last good threads
                    self.data = payload(self.data["threads"] if self.data else [], [str(err)], live=True)
                self.at = time.monotonic()
            return self.data


def serve(source: Source, port: int, open_browser: bool) -> None:
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(http.server.BaseHTTPRequestHandler):
        def send(self, code: int, kind: str, body: str) -> None:
            raw = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):  # noqa: N802
            if self.headers.get("Host") not in hosts:  # refuses DNS-rebound pages
                return self.send(403, "text/plain", "forbidden")
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                return self.send(200, "text/html; charset=utf-8", page(source.get()))
            if path == "/api/threads":
                return self.send(200, "application/json", json.dumps(source.get(), ensure_ascii=False))
            return self.send(404, "text/plain", "not found")

        def log_message(self, *args):
            pass

    class Server(http.server.ThreadingHTTPServer):
        allow_reuse_address = os.name != "nt"  # on Windows SO_REUSEADDR would share a port another server holds
        daemon_threads = True

    try:
        server = Server(("127.0.0.1", port), Handler)
    except OSError as err:
        sys.exit(f"arena: can't listen on 127.0.0.1:{port} ({err.strerror}); pick another --port")
    url = f"http://127.0.0.1:{port}/"
    print(f"arena: serving {url} (Ctrl+C stops)", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def print_digest(threads: list[dict]) -> None:
    for t in threads:
        print(f"{t['label']} · {t['state']} · {t['title']}\n{t['url']}")
        for line in st.digest(t["turns"]):
            print(line)
        print()


def interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # thread titles can leave the code page
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("urls", nargs="*", metavar="thread-url", help="GitHub PR or issue URLs")
    parser.add_argument("--repo", help="owner/repo: load its recently updated PRs and issues with bot turns")
    parser.add_argument("--limit", type=int, default=30, help="with --repo, how many recent PRs and issues to scan")
    parser.add_argument("--out", help="write a self-contained HTML page here")
    parser.add_argument("--serve", action="store_true", help="serve the page live on 127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="open the page in the browser")
    parser.add_argument("--ascii", action="store_true", help="terminal view in plain 7-bit text, no colour")
    opts = parser.parse_args()
    if bool(opts.urls) == bool(opts.repo):
        parser.error("give thread URLs or --repo, not both" if opts.urls else "give thread URLs or --repo")
    if opts.repo and not re.fullmatch(r"[\w.-]+/[\w.-]+", opts.repo):
        parser.error("--repo takes owner/repo")
    if bad := [u for u in opts.urls if not st.parse_url(u)]:
        parser.error(f"not a GitHub PR or issue URL: {bad[0]}")
    browser = bool(opts.out or opts.serve)
    source = Source(opts.urls, opts.repo, max(1, min(opts.limit, 100)))
    if not browser and interactive():
        print("arena: loading...", file=sys.stderr, flush=True)
    try:
        if opts.out and not opts.serve:
            data = payload(*gather(opts.urls, opts.repo, source.limit), live=False)
        else:  # the terminal and --serve keep refetching through the source's cache
            data = source.get()
    except st.GhError as err:
        sys.exit(f"arena: {err}")
    for err in data["errors"]:
        print(f"arena: {err}", file=sys.stderr)
    if not data["threads"] and not opts.serve:
        sys.exit("arena: no thread with a bot turn to show")
    if not browser:
        if not interactive():
            print_digest(data["threads"])
            return 0
        try:
            tui.run(source, data, tui.colour_mode(os.environ, opts.ascii), SPRITES)
        except KeyboardInterrupt:
            return 130
        except OSError as err:  # no VT on this console: the text digest instead
            print(f"arena: {err}; printing the thread instead", file=sys.stderr)
            print_digest(data["threads"])
        return 0
    if opts.out:
        out = Path(opts.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page({**data, "live": False}), encoding="utf-8")
        print(f"arena: wrote {out} ({len(data['threads'])} thread(s))")
        if opts.open and not opts.serve:
            webbrowser.open(out.resolve().as_uri())
    if opts.serve:
        serve(source, opts.port, opts.open)
    return 0


if __name__ == "__main__":
    sys.exit(main())
