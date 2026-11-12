#!/usr/bin/env python3
r"""Show what the bots said on a PR or issue, as a short readable thread.

Usage:
  python show_thread.py <pr-or-issue-url> [--full] [--since <comment-id>]

Reads the thread's comments with `gh` and keeps the bot voices (comments whose first line is the
pr-conversation signature, `**<brand> <role> · <agent> (<model>)** · head \`<sha>\``) plus
PR-Agent's review, from bot accounts and people with write access only. For each it prints the
time, the voice, the head it covers, and its gist: the findings (P0/P1/P2), the author's
fixed/dismissed answers, a vote or tally, or the first sentence.
--full prints each body instead. --since prints only comments newer than that id, so a
coordinator can show the user each new turn as it lands.

As a module, `voices(url)` returns the same comments as dicts (arena.py draws them).
"""

import argparse
import html
import itertools
import json
import re
import subprocess
import sys

MAX_LINE = 2000
CONTROLS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
ROLES = r"(?:author|reviewer|verifier \d|panel|coordinator|trunk check)"
SIGNATURE = re.compile(rf"^\*\*\S+ ({ROLES}\b[^*]*)\*\*\s*·\s*(.*)$")
THREAD_URL = re.compile(r"^https://github\.com/([\w.-]+/[\w.-]+)/(pull|issues)/(\d+)(?:[/?#].*)?$")
FINDING = re.compile(r"^\s*[-*]?\s*\**(P[012])\b[^—\n]*—\s*(.+)$")
VERDICT = re.compile(r"(VERDICT:\s*(?:NOT )?DONE|^`?(?:panel|conversation):\s*[^\n]+)", re.I)
# An author's prose answers (threads without the JSON reply): "3. **Empty pane: fixed.** ...",
# "| <finding> | **fixed**: ... |", "| <finding> | **fixed in `<sha>`**. ... |" or "... is **fixed**: ..."
ANSWER_ITEM = re.compile(r"^\s*(?:\d+[.)]|[-*])\s*\*\*(.+?)[:.]?\s+(fixed|dismissed)\.?\*\*\s*(.*)$", re.I)
ANSWER_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*\*\*(fixed|dismissed)(?: in `?[0-9a-f]{7,40}`?)?\*\*[:.]?\s*(.*?)\s*\|?$", re.I)
ANSWER_INLINE = re.compile(r"\*\*(fixed|dismissed)(?: in `?[0-9a-f]{7,40}`?)?\*\*", re.I)
MODELED = re.compile(r"^(\S+) \((.+)\)$")
# acpx agent names, and bot.py, which signs the panel and coordinator; any other label is a review lens.
AGENTS = {"omp", "claude", "codex", "gemini", "cursor", "copilot", "opencode", "qwen", "kimi", "droid",
          "kiro", "pi", "iflow", "auggie", "goose", "amp", "bot.py"}


class GhError(RuntimeError):
    pass


def parse_url(url: str):
    """(owner/repo, number, "pr" | "issue") for a GitHub PR or issue URL, else None."""
    match = THREAD_URL.match(url.strip())
    if not match:
        return None
    repo, kind, number = match.groups()
    return repo, int(number), "pr" if kind == "pull" else "issue"


def gh_json(path: str, paginate: bool = False):
    """`gh api <path>` parsed; paginated arrays come back as one list."""
    cmd = ["gh", "api", *(["--paginate", "--jq", ".[]"] if paginate else []), path]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise GhError("the GitHub CLI `gh` is not installed or not on PATH") from None
    if out.returncode:
        raise GhError(f"gh api {path} failed: {out.stderr.strip()[-400:]}")
    if paginate:
        return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]
    return json.loads(out.stdout)


def comments(repo: str, number: int) -> list[dict]:
    return gh_json(f"repos/{repo}/issues/{number}/comments", paginate=True)


def parse_signature(line: str):
    """The voice in a signature line: role, kind, verifier number, lens, agent, model and head; else None."""
    sig = SIGNATURE.match(line.strip())
    if not sig:
        return None
    voice = sig.group(1).strip()
    head = sig.group(2).replace("head", "").replace("`", "").strip()
    role, *labels = [part.strip() for part in voice.split("·")]
    kind = "verifier" if role == "trunk check" else role.split()[0]
    number = int(role.split()[1]) if kind == "verifier" and role != "trunk check" else None
    lens = agent = model = None
    for label in filter(None, labels):
        modeled = MODELED.match(label)
        if modeled:
            agent, model = modeled.groups()
        elif label in AGENTS:
            agent = label
        else:
            lens = label
    return {"role": role, "voice": voice, "kind": kind, "number": number, "lens": lens,
            "agent": agent, "model": model, "head": head}


# Its "Persistent review updated" notices only point at the edited review, so they are not turns.
PR_AGENT_MARKERS = ("PR Reviewer Guide", "PR Code Suggestions")
# Without an app the bots and PR-Agent post as the repo's owner; with one, as the app's bot account.
WRITERS = {"OWNER", "MEMBER", "COLLABORATOR"}


def is_pr_agent(body: str) -> bool:
    """PR-Agent's own headings; a person merely mentioning pr-agent is not its turn."""
    return any(marker in body for marker in PR_AGENT_MARKERS)


def may_speak(comment: dict) -> bool:
    """A bot account or someone with write access; a signature from anyone else is a person posing as a bot."""
    return (comment.get("user") or {}).get("type") == "Bot" or comment.get("author_association") in WRITERS


def clean(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    # Inline code is text the bot meant literally (`<url>`, `<!--`): set it aside before stripping markup.
    spans: list[str] = []
    def keep(m: re.Match) -> str:
        spans.append(m.group(0))
        return f"\x00{len(spans) - 1}\x00"
    text = re.sub(r"`[^`\n]+`", keep, text.replace("\x00", ""))
    # An unclosed comment runs to the end: one pass, where a lone "<!--" would rescan the rest each time.
    text = re.sub(r"<!--.*?(?:-->|\Z)", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)
    # A numeric entity is cut to 7 digits: Python refuses to parse an integer string over 4,300.
    return html.unescape(re.sub(r"&#(x?)(\d{8,})", lambda m: f"&#{m.group(1)}{m.group(2)[:7]}", text))


def records(data: dict, key: str) -> list[dict]:
    """The objects under `key`; a bot can write null, a string or a mixed list there."""
    items = data.get(key)
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def clip(text: str, limit) -> str:
    return text if limit is None else text[:limit]


def json_objects(body: str) -> list[dict]:
    """The objects in ```json (or bare ```) blocks, the way bot.py reads them: a fence is a line that starts
    with ```, so backticks inside a JSON string never end the block."""
    out, current, lang = [], None, ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("```"):
            if current is not None:
                current.append(line)
        elif current is None:
            current, lang = [], stripped[3:].strip().lower()
        else:
            block, current = "\n".join(current).strip(), None
            if lang not in ("", "json") or not block.startswith("{"):
                continue
            try:
                data = json.loads(block)
            except (ValueError, RecursionError):  # malformed, or nested deeper than Python parses
                continue
            if isinstance(data, dict):
                out.append(data)
    return out


def json_gist(objects: list[dict], limit=140) -> list[str]:
    """Findings, answers or a vote from the fenced JSON. Each text cut at `limit` (None: whole)."""
    out = []
    for data in objects:
        for f in records(data, "findings"):
            out.append(f"{f.get('severity', '?')}: {f.get('file', '')}:{f.get('line', '')} — {clip(str(f.get('claim', '')), limit)}")
        for r in records(data, "responses"):
            where = f" in {str(r['sha'])[:8]}" if r.get("sha") else ""
            out.append(f"{r.get('action', '?')} {r.get('id', '')}{where} — {clip(str(r.get('reason', '')), limit)}")
        if "vote" in data:
            out.append(f"vote: {data['vote']} — {clip(str(data.get('evidence', '')), limit)}")
        if not out and "findings" in data:
            out.append("no findings")
    return list(dict.fromkeys(out))  # a reply that repeats its JSON block counts once


def finding_texts(objects: list[dict]) -> dict[str, str]:
    """Each P0-P2 finding's id and claim; an id that is missing is numbered F1, F2... as bot.py numbers them."""
    out = {}
    for data in objects:
        for i, f in enumerate(records(data, "findings"), 1):
            if str(f.get("severity", "")).upper() in ("P0", "P1", "P2"):
                out.setdefault(str(f.get("id") or f"F{i}"), f"{f.get('file', '')} {f.get('claim', '')}")
    return out


def prose_answers(lines: list[str], limit=140) -> list[str]:
    """An author's fixed/dismissed answers written as prose, in the JSON answers' `<action> <id> — <reason>` form."""
    out = []
    for line in lines:
        item = ANSWER_ITEM.match(line) or ANSWER_ROW.match(line)
        if item:
            title, action, rest = item.groups()
            out.append(f"{action.lower()} {title.replace('**', '').strip()} — {clip(rest.replace('**', ''), limit)}")
            continue
        inline = ANSWER_INLINE.search(line)
        if inline:
            sentence = next(s for s in re.split(r"(?<=[.!?])\s+", line) if ANSWER_INLINE.search(s))
            out.append(f"{inline.group(1).lower()} — {clip(sentence.replace('**', ''), limit)}")
    return out


def gist(body: str, kind: str = "", limit=140, objects=None) -> list[str]:
    if kind == "pr-agent" and "PR Reviewer Guide" in body:  # its focus-area titles, or its all-clear line
        if "Recommended focus areas" in body:
            section = body.split("Recommended focus areas", 1)[1].split("</table>", 1)[0]
            titles = re.findall(r"<strong>([^<]{3,80})</strong>", section)
            if titles:
                return ["focus: " + "; ".join(dict.fromkeys(t.strip() for t in titles))]
        clear = re.search(r"No major issues detected[^<\n]*", body)
        return [clear.group(0).strip() if clear else "No major issues detected"]
    structured = json_gist(json_objects(body) if objects is None else objects, limit)
    if structured:
        return structured
    # Lines are cut to MAX_LINE: the answer patterns backtrack quadratically on a long run of spaces.
    lines = [line.strip()[:MAX_LINE] for line in clean(body).splitlines() if line.strip()]
    found = [f"{m.group(1)}: {clip(m.group(2).replace('**', ''), limit)}" for line in lines if (m := FINDING.match(line))]
    verdict = next((m.group(1) for line in lines if (m := VERDICT.search(line))), None)
    if found:
        return ([verdict] if verdict else []) + found
    if verdict:
        return [verdict]
    first = next((line for line in lines[1:] if not line.startswith("#")), "")
    answers = prose_answers(lines[1:], limit) if kind == "author" else []
    if answers:  # the opening line, up to its own first answer
        first = "" if ANSWER_ITEM.match(first) or ANSWER_ROW.match(first) else " ".join(
            itertools.takewhile(lambda s: not ANSWER_INLINE.search(s), re.split(r"(?<=[.!?])\s+", first)))
    first = clip(first.replace("**", ""), limit and limit + 60)
    return ([first] if first else []) + answers


def voice(comment: dict, limit=140):
    """One comment as a bot voice, or None when no bot or PR-Agent wrote it."""
    body = comment.get("body") or ""
    if not may_speak(comment):
        return None
    first = body.strip().splitlines()[0] if body.strip() else ""
    who = parse_signature(first)
    if not who:
        if not is_pr_agent(body):
            return None
        who = {"role": "pr-agent", "voice": "pr-agent", "kind": "pr-agent", "number": None, "lens": None,
               "agent": None, "model": None, "head": ""}
    objects = json_objects(body)
    return {"id": comment["id"], "html_url": comment.get("html_url", ""), "time": comment.get("created_at", ""),
            **who, "gist": gist(body, who["kind"], limit, objects), "findings": finding_texts(objects),
            "body": body}


def voices(url: str, limit=140) -> list[dict]:
    """Every bot and PR-Agent comment on the PR or issue at `url`, oldest first; gist texts cut at `limit` (None: whole)."""
    parsed = parse_url(url)
    if not parsed:
        raise ValueError(f"not a GitHub PR or issue URL: {url}")
    repo, number, _ = parsed
    return [v for c in comments(repo, number) if (v := voice(c, limit))]


def printable(line: str) -> str:
    """Thread text bound for a terminal: C0 controls (tabs kept), DEL and C1 dropped, so a comment can't
    write the clipboard, retitle the window or clear the screen."""
    return CONTROLS.sub("", line)


def digest(found: list[dict], full: bool = False) -> list[str]:
    """The text blocks the CLI prints: time, voice, head and id, then the gist (or the body with full=True)."""
    out = []
    for v in found:
        out.append(f"\n{v['time'][11:16]}  {v['voice']}" + (f"  @ {v['head']}" if v["head"] else "") + f"  (#{v['id']})")
        if not full:
            out.extend(f"    {line}" for line in v["gist"])
            continue
        lines = v["body"].strip().splitlines()  # a signed body's first line is the signature printed above
        out.extend(f"    {line}" for line in (lines if v["kind"] == "pr-agent" else lines[1:]))
    return [printable(line) for line in out]


def main() -> int:
    # A pipe on Windows defaults to the locale code page; thread text carries emoji and arrows.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url", metavar="pr-or-issue-url")
    parser.add_argument("--full", action="store_true", help="print each comment's whole body")
    parser.add_argument("--since", type=int, default=0, help="only comments with a larger id")
    opts = parser.parse_args()
    if not parse_url(opts.url):
        sys.exit("show_thread: give a GitHub PR or issue URL, e.g. https://github.com/owner/repo/pull/12")
    try:
        found = voices(opts.url)
    except GhError as err:
        sys.exit(f"show_thread: {err}")
    shown = [v for v in found if v["id"] > opts.since]
    for line in digest(shown, opts.full):
        print(line)
    if not shown:
        print("show_thread: no bot or PR-Agent comments" + (" since that id" if opts.since else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
