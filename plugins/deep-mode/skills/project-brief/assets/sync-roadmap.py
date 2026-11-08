#!/usr/bin/env python3
"""Generate ROADMAP.md from GitHub Issues labeled `help wanted`.

Sections:
  ## Open to claim  - no active claim, no assignee, no open PR referencing it
  ## Claimed        - active claim comment (or assignee), no open PR yet
  ## In review      - an open PR body says closes/fixes/resolves #N

Claim rule (shared with pr-overlap.py): the newest comment containing
`<!-- deep-mode:claim -->` on an open issue is active if its `Expires:` date
is today or later and no newer comment from the same author contains
`<!-- deep-mode:unclaim -->`. An assignee also counts as a claim (files unknown).

Output is deterministic for the same GitHub data and date: no timestamps,
rows sorted by issue number, labels sorted.

Exit codes: 0 ok (or unchanged under --check), 1 file would change (--check),
2 usage or gh error.

Requires Python 3.10+ and an authenticated GitHub CLI (`gh`).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from typing import Any

LABEL = "help wanted"
CLAIM_MARKER = "<!-- deep-mode:claim -->"
UNCLAIM_MARKER = "<!-- deep-mode:unclaim -->"
HEADER = "Generated from GitHub Issues by sync-roadmap.py. Edit issues, not this file."


class GhError(Exception):
    pass


def gh_api(path: str) -> list[Any]:
    """Call `gh api --paginate` and return the merged list of page items."""
    proc = subprocess.run(
        ["gh", "api", "--paginate", "-H", "Accept: application/vnd.github+json", path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise GhError(f"gh api {path} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    # --paginate concatenates page arrays ("[...][...]"); decode them one by one.
    out = proc.stdout
    decoder = json.JSONDecoder()
    items: list[Any] = []
    i = 0
    while True:
        while i < len(out) and out[i].isspace():
            i += 1
        if i >= len(out):
            break
        value, i = decoder.raw_decode(out, i)
        if isinstance(value, list):
            items.extend(value)
        else:
            items.append(value)
    return items


def normalize_path(raw: str) -> str | None:
    p = raw.strip().strip('"').strip("'").strip("`").strip().replace("\\", "/")
    is_dir = p.endswith("/")
    while p.startswith("./"):
        p = p[2:]
    p = p.lstrip("/")
    p = re.sub(r"/{2,}", "/", p)
    if p in ("", "."):
        return "" if is_dir or p == "." else None  # "" = whole repo when given as "/" or "./"
    p = p.rstrip("/")
    return p + "/" if is_dir else p


def parse_paths(text: str) -> list[str]:
    out: list[str] = []
    for part in re.split(r"[,\n]", text or ""):
        norm = normalize_path(part)
        if norm is not None and norm not in out:
            out.append(norm)
    return out


def parse_claim(body: str) -> dict[str, Any]:
    plan = files = expires = ""
    for raw in body.splitlines():
        line = raw.strip()
        key, sep, val = line.partition(":")
        if not sep:
            continue
        k = key.strip().lower()
        if k == "plan" and not plan:
            plan = val.strip()
        elif k == "files" and not files:
            files = val.strip()
        elif k == "expires" and not expires:
            expires = val.strip()
    paths = sorted(parse_paths(files))
    exp_date = None
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", expires)
    if m:
        try:
            exp_date = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            exp_date = None
    return {"plan": plan, "files": paths, "expires": exp_date}


def active_claim(comments: list[dict[str, Any]], today: dt.date) -> dict[str, Any] | None:
    """Apply the shared claim rule to an issue's comments."""
    ordered = sorted(comments, key=lambda c: (c.get("created_at") or "", c.get("id") or 0))
    claim_idx = None
    for idx, c in enumerate(ordered):
        if CLAIM_MARKER in (c.get("body") or ""):
            claim_idx = idx
    if claim_idx is None:
        return None
    c = ordered[claim_idx]
    author = ((c.get("user") or {}).get("login")) or ""
    info = parse_claim(c.get("body") or "")
    if info["expires"] is None or info["expires"] < today:
        return None
    for later in ordered[claim_idx + 1:]:
        if ((later.get("user") or {}).get("login") or "").lower() == author.lower() and UNCLAIM_MARKER in (later.get("body") or ""):
            return None
    info["author"] = author
    return info


def closing_refs(body: str, repo: str) -> set[int]:
    pattern = re.compile(
        r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b\s*:?\s+(?:" + re.escape(repo) + r")?#(\d+)\b",
        re.IGNORECASE,
    )
    return {int(m.group(1)) for m in pattern.finditer(body or "")}


def cell(text: str) -> str:
    text = " ".join((text or "").split())
    return text.replace("|", "\\|") or "-"


def collect(repo: str, today: dt.date) -> list[dict[str, Any]]:
    issues = gh_api(f"repos/{repo}/issues?state=open&per_page=100&labels={LABEL.replace(' ', '%20')}")
    issues = [i for i in issues if "pull_request" not in i]
    prs = gh_api(f"repos/{repo}/pulls?state=open&per_page=100")

    in_review: dict[int, list[dict[str, Any]]] = {}
    for pr in prs:
        for n in closing_refs(pr.get("body") or "", repo):
            in_review.setdefault(n, []).append(pr)

    rows = []
    for issue in issues:
        n = issue["number"]
        assignees = sorted({(a or {}).get("login", "") for a in issue.get("assignees") or []} - {""})
        claim = None
        if issue.get("comments", 0):
            claim = active_claim(gh_api(f"repos/{repo}/issues/{n}/comments?per_page=100"), today)
        claimants = []
        if claim:
            claimants.append(claim["author"])
        claimants += [a for a in assignees if a not in claimants]
        prs_for = sorted(in_review.get(n, []), key=lambda p: p["number"])
        if prs_for:
            section = "review"
        elif claimants:
            section = "claimed"
        else:
            section = "open"
        rows.append({
            "number": n,
            "url": issue.get("html_url") or f"https://github.com/{repo}/issues/{n}",
            "title": issue.get("title") or "",
            "labels": sorted({(l or {}).get("name", "") for l in issue.get("labels") or []} - {""}),
            "claimants": claimants,
            "files": claim["files"] if claim else [],
            "prs": [(p["number"], p.get("html_url") or "", ((p.get("user") or {}).get("login")) or "") for p in prs_for],
            "section": section,
        })
    rows.sort(key=lambda r: r["number"])
    return rows


def render(repo: str, rows: list[dict[str, Any]]) -> str:
    out = [
        "# Roadmap",
        "",
        f"<!-- {HEADER} -->",
        f"_{HEADER}_",
        "",
        f"Tasks are open issues in `{repo}` labeled `{LABEL}`. "
        "Claim one with `/deep-mode:contribute` or by commenting on the issue.",
        "",
    ]
    sections = [
        ("open", "Open to claim", "Claimed by"),
        ("claimed", "Claimed", "Claimed by"),
        ("review", "In review", "Pull request"),
    ]
    for key, title, who_header in sections:
        sec = [r for r in rows if r["section"] == key]
        out.append(f"## {title}")
        out.append("")
        if not sec:
            out.append("_None._")
            out.append("")
            continue
        out.append(f"| Issue | Title | Labels | {who_header} | Files |")
        out.append("| --- | --- | --- | --- | --- |")
        for r in sec:
            labels = ", ".join(f"`{l}`" for l in r["labels"]) or "-"
            if r["prs"]:
                who = ", ".join(f"[#{n}]({u})" + (f" by @{a}" if a else "") for n, u, a in r["prs"])
            elif r["claimants"]:
                who = ", ".join(f"@{c}" for c in r["claimants"])
            else:
                who = "-"
            files = ", ".join(f"`{f.replace('`', '').replace('|', chr(92) + '|')}`" for f in r["files"]) or "-"
            out.append(
                f"| [#{r['number']}]({r['url']}) | {cell(r['title'])} | {labels} | {who} | {files} |"
            )
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def write_atomic(path: str, text: str) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".roadmap-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sync-roadmap.py",
        description="Generate a deterministic ROADMAP.md from open GitHub issues labeled 'help wanted'.",
        epilog="Exit codes: 0 ok/unchanged, 1 would change (--check), 2 usage or gh error.",
    )
    parser.add_argument("--repo", required=True, help="owner/name of the GitHub repository")
    parser.add_argument("--out", default="ROADMAP.md", help="output file (default: ROADMAP.md)")
    parser.add_argument("--check", action="store_true", help="do not write; exit 1 if the file would change")
    parser.add_argument("--today", help=argparse.SUPPRESS)  # YYYY-MM-DD override for tests
    args = parser.parse_args(argv)

    if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
        print(f"sync-roadmap: --repo must be owner/name, got {args.repo!r}", file=sys.stderr)
        return 2
    try:
        today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(dt.timezone.utc).date()
    except ValueError:
        print("sync-roadmap: --today must be YYYY-MM-DD", file=sys.stderr)
        return 2

    try:
        rows = collect(args.repo, today)
    except FileNotFoundError:
        print("sync-roadmap: GitHub CLI `gh` not found on PATH", file=sys.stderr)
        return 2
    except (GhError, json.JSONDecodeError, KeyError) as exc:
        print(f"sync-roadmap: {exc}", file=sys.stderr)
        return 2

    text = render(args.repo, rows)
    try:
        with open(args.out, encoding="utf-8", newline="") as fh:
            current = fh.read()
    except FileNotFoundError:
        current = None

    if args.check:
        if current != text:
            print(f"sync-roadmap: {args.out} is out of date", file=sys.stderr)
            return 1
        print(f"sync-roadmap: {args.out} is up to date")
        return 0

    if current == text:
        print(f"sync-roadmap: {args.out} unchanged")
        return 0
    write_atomic(args.out, text)
    counts = {k: sum(1 for r in rows if r["section"] == k) for k in ("open", "claimed", "review")}
    print(
        f"sync-roadmap: wrote {args.out} "
        f"({counts['open']} open, {counts['claimed']} claimed, {counts['review']} in review)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
