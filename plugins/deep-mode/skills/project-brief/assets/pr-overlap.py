#!/usr/bin/env python3
"""Detect overlapping work between open pull requests and active issue claims.

Stdlib only (Python 3.10+). Talks to GitHub through the `gh` CLI, which must be
installed and authenticated (or have GH_TOKEN set).

Subcommands (all take --repo owner/name):
  check   --files a,b,dir/ [--exclude-pr N] [--exclude-issue N] [--json]
          List open PRs and active claims whose paths overlap the given files.
          Exit 0 = no overlap, 3 = overlap, 2 = usage or gh error.
  comment --pr N
          Post or update one overlap comment on PR N (marker <!-- deep-mode:overlap -->).
  claims  [--json]
          List active claims (claim comments and issue assignees).

Claims are looked for on open issues labeled "help wanted" and on open issues
with an assignee; other issues are not scanned.

Overlap rule: two path sets overlap if any path is equal, or one is a directory
prefix ("dir/") of the other. Paths are repo-relative with forward slashes.

Claim comment format (posted on an issue):
  <!-- deep-mode:claim -->
  Claimed by @<login> via /contribute
  Plan: <one line>
  Files: <comma-separated repo paths; trailing "/" = whole directory>
  Expires: <YYYY-MM-DD>
A claim is active if it is the newest claim comment on an open issue, its
Expires date is today (UTC) or later, and no newer comment from the same author
contains <!-- deep-mode:unclaim -->. An issue assignee also counts as a claim
with unknown files: it never overlaps by file, only by issue.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

CLAIM_MARKER = "<!-- deep-mode:claim -->"
UNCLAIM_MARKER = "<!-- deep-mode:unclaim -->"
OVERLAP_MARKER = "<!-- deep-mode:overlap -->"

EXIT_OK = 0
EXIT_ERROR = 2
EXIT_OVERLAP = 3

LINK_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s+(?:[\w.-]+/[\w.-]+)?#(\d+)\b", re.IGNORECASE
)
FIELD_RE = re.compile(r"^\s*(plan|files|expires)\s*:\s*(.*?)\s*$", re.IGNORECASE)
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

MAX_WORKERS = 8

OPEN_PRS_QUERY = " ".join("""
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: OPEN, first: 100, after: $cursor,
                 orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url
        author { login __typename }
        files(first: 50) { pageInfo { hasNextPage } nodes { path changeType } }
      }
    }
  }
}
""".split())


class GhError(Exception):
    """Raised when gh is missing, unauthenticated, or a call fails."""


# --------------------------------------------------------------------------- gh


def _gh_path() -> str:
    path = shutil.which("gh")
    if not path:
        raise GhError(
            "GitHub CLI `gh` not found on PATH. Install it from https://cli.github.com/ "
            "and run `gh auth login` (or set GH_TOKEN)."
        )
    return path


def run_gh(args: list[str]) -> str:
    """Run gh with an argument list (no shell). Returns stdout as text."""
    try:
        proc = subprocess.run(
            [_gh_path(), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "GH_PROMPT_DISABLED": "1", "NO_COLOR": "1"},
            check=False,
        )
    except OSError as exc:
        raise GhError(f"could not run gh: {exc}") from exc
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        low = err.lower()
        if "auth login" in low or "not logged" in low or "authentication" in low or "http 401" in low:
            raise GhError(
                "gh is not authenticated. Run `gh auth login` or set GH_TOKEN.\n" + err
            )
        raise GhError(f"gh {' '.join(args)} failed (exit {proc.returncode}):\n{err}")
    return proc.stdout


def _decode_concatenated(text: str) -> list:
    """Decode output of `gh api --paginate`, which may be several JSON documents back to back."""
    decoder = json.JSONDecoder()
    items: list = []
    idx, n = 0, len(text)
    while True:
        while idx < n and text[idx].isspace():
            idx += 1
        if idx >= n:
            break
        try:
            value, idx = decoder.raw_decode(text, idx)
        except json.JSONDecodeError as exc:
            raise GhError(f"could not parse gh output as JSON: {exc}") from exc
        if isinstance(value, list):
            items.extend(value)
        else:
            items.append(value)
    return items


def gh_api_list(path: str) -> list[dict]:
    sep = "&" if "?" in path else "?"
    return _decode_concatenated(run_gh(["api", "--paginate", f"{path}{sep}per_page=100"]))


def gh_graphql(query: str, variables: dict[str, str]) -> dict:
    """Run a GraphQL query; variables are passed as raw strings (-f), never interpolated."""
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args += ["-f", f"{key}={value}"]
    try:
        doc = json.loads(run_gh(args))
    except json.JSONDecodeError as exc:
        raise GhError(f"could not parse gh graphql output as JSON: {exc}") from exc
    if doc.get("errors"):
        msgs = "; ".join(str(e.get("message", e)) for e in doc["errors"])
        raise GhError(f"GitHub GraphQL error: {msgs}")
    return doc.get("data") or {}


def parallel_map(fn, items: list) -> list:
    """Apply fn to items concurrently (gh calls are I/O bound); preserves order."""
    if len(items) <= 1:
        return [fn(x) for x in items]
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(items))) as pool:
        return list(pool.map(fn, items))


def gh_api_write(method: str, path: str, body: str) -> dict:
    """Send {"body": body} via a temp JSON file (no untrusted text on the command line)."""
    fd, tmp = tempfile.mkstemp(prefix="pr-overlap-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"body": body}, fh)
        out = run_gh(["api", "--method", method, path, "--input", tmp])
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    return json.loads(out) if out.strip() else {}


# ------------------------------------------------------------------------ paths


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


def paths_overlap(a: str, b: str) -> bool:
    if a == b:
        return True
    if a.endswith("/") or a == "":
        if b.startswith(a) or b + "/" == a:
            return True
    if b.endswith("/") or b == "":
        if a.startswith(b) or a + "/" == b:
            return True
    return False


def overlapping(mine: list[str], theirs: list[str]) -> list[str]:
    """Return the paths from `theirs` that overlap any path in `mine`."""
    return [t for t in theirs if any(paths_overlap(m, t) for m in mine)]


# ----------------------------------------------------------------------- claims


@dataclass
class Claim:
    issue: int
    title: str
    url: str
    author: str
    kind: str  # "comment" or "assignee"
    plan: str = ""
    files: list[str] = field(default_factory=list)
    expires: str = ""


def _today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


def parse_claim_body(body: str) -> dict:
    fields: dict[str, str] = {}
    for line in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        m = FIELD_RE.match(line)
        if m and m.group(1).lower() not in fields:
            fields[m.group(1).lower()] = m.group(2)
    return fields


def _login(obj: dict | None) -> str:
    return ((obj or {}).get("login") or "").strip()


def active_claim_from_comments(comments: list[dict], today: dt.date) -> dict | None:
    """Apply the claim rule to an issue's comments. Returns the active claim comment or None."""
    ordered = sorted(comments, key=lambda c: (c.get("created_at") or "", c.get("id") or 0))
    claim_idx = None
    for i, c in enumerate(ordered):
        if CLAIM_MARKER in (c.get("body") or ""):
            claim_idx = i
    if claim_idx is None:
        return None
    claim = ordered[claim_idx]
    author = _login(claim.get("user")).lower()
    for later in ordered[claim_idx + 1 :]:
        if _login(later.get("user")).lower() == author and UNCLAIM_MARKER in (later.get("body") or ""):
            return None
    fields = parse_claim_body(claim.get("body") or "")
    expires = fields.get("expires", "").strip()
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", expires)
    if not m:
        return None
    try:
        exp_date = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None
    if exp_date < today:
        return None
    return {
        "author": _login(claim.get("user")),
        "plan": fields.get("plan", ""),
        "files": parse_paths(fields.get("files", "")),
        "expires": exp_date.isoformat(),
    }


def _open_issues(repo: str, query: str) -> list[dict]:
    return [i for i in gh_api_list(f"repos/{repo}/issues?state=open&{query}")
            if "pull_request" not in i]


def fetch_active_claims(repo: str) -> list[Claim]:
    today = _today()
    issues: dict[int, dict] = {}
    for query in ("labels=help%20wanted", "assignee=*"):
        for issue in _open_issues(repo, query):
            issues.setdefault(issue["number"], issue)
    with_comments = [n for n, i in issues.items() if i.get("comments", 0)]
    fetched = parallel_map(
        lambda n: gh_api_list(f"repos/{repo}/issues/{n}/comments"), with_comments
    )
    comments_by_issue = dict(zip(with_comments, fetched))
    claims: list[Claim] = []
    for number, issue in issues.items():
        title = issue.get("title") or ""
        url = issue.get("html_url") or ""
        found = None
        if number in comments_by_issue:
            found = active_claim_from_comments(comments_by_issue[number], today)
        if found:
            claims.append(Claim(number, title, url, found["author"], "comment",
                                found["plan"], found["files"], found["expires"]))
            continue
        assignees = [_login(a) for a in issue.get("assignees") or [] if _login(a)]
        if not assignees and _login(issue.get("assignee")):
            assignees = [_login(issue.get("assignee"))]
        if assignees:
            claims.append(Claim(number, title, url, ", ".join(assignees), "assignee"))
    claims.sort(key=lambda c: c.issue)
    return claims


# -------------------------------------------------------------------------- PRs


def pr_files(repo: str, number: int) -> list[str]:
    paths: list[str] = []
    for f in gh_api_list(f"repos/{repo}/pulls/{number}/files"):
        for key in ("filename", "previous_filename"):
            norm = normalize_path(f.get(key) or "")
            if norm and norm not in paths:
                paths.append(norm)
    return paths


def _graphql_author(author: dict | None) -> str:
    login = _login(author)
    # REST reports bot users as "name[bot]"; GraphQL drops the suffix.
    if login and (author or {}).get("__typename") == "Bot" and not login.endswith("[bot]"):
        login += "[bot]"
    return login


def open_prs(repo: str, exclude_pr: int | None = None) -> list[dict]:
    """All open PRs with their changed paths, in one GraphQL pass.

    PRs with more than 50 files, renamed files (GraphQL has no previous path),
    or no file data fall back to the REST files endpoint for that PR only.
    """
    owner, name = repo.split("/", 1)
    prs: list[dict] = []
    needs_rest: list[dict] = []
    cursor: str | None = None
    while True:
        variables = {"owner": owner, "name": name}
        if cursor:
            variables["cursor"] = cursor
        conn = (((gh_graphql(OPEN_PRS_QUERY, variables).get("repository") or {})
                 .get("pullRequests")) or {})
        for node in conn.get("nodes") or []:
            if not node or node.get("number") == exclude_pr:
                continue
            pr = {
                "number": node["number"],
                "title": node.get("title") or "",
                "author": _graphql_author(node.get("author")),
                "url": node.get("url") or "",
                "files": [],
            }
            files = node.get("files")
            file_nodes = (files or {}).get("nodes") or []
            if (files is None
                    or ((files.get("pageInfo") or {}).get("hasNextPage"))
                    or any((f or {}).get("changeType") == "RENAMED" for f in file_nodes)):
                needs_rest.append(pr)
            else:
                for f in file_nodes:
                    norm = normalize_path((f or {}).get("path") or "")
                    if norm and norm not in pr["files"]:
                        pr["files"].append(norm)
            prs.append(pr)
        page = conn.get("pageInfo") or {}
        if not page.get("hasNextPage") or not page.get("endCursor"):
            break
        cursor = page["endCursor"]
    for pr, paths in zip(needs_rest, parallel_map(lambda p: pr_files(repo, p["number"]), needs_rest)):
        pr["files"] = paths
    return prs


def linked_issues(text: str) -> set[int]:
    return {int(n) for n in LINK_RE.findall(text or "")}


def find_overlaps(
    repo: str,
    files: list[str],
    exclude_pr: int | None = None,
    exclude_issues: set[int] | None = None,
    exclude_claim_authors: set[str] | None = None,
) -> list[dict]:
    exclude_issues = exclude_issues or set()
    excl_authors = {a.lower() for a in (exclude_claim_authors or set())}
    results: list[dict] = []
    for pr in open_prs(repo, exclude_pr=exclude_pr):
        hits = overlapping(files, pr["files"])
        if hits:
            results.append({
                "kind": "pr",
                "number": pr["number"],
                "title": pr["title"],
                "author": pr["author"],
                "url": pr["url"],
                "overlapping": hits,
            })
    for c in fetch_active_claims(repo):
        if c.issue in exclude_issues or c.kind != "comment":
            continue  # assignee-only claims have unknown files: never overlap by file
        if c.author.lower() in excl_authors:
            continue
        hits = overlapping(files, c.files)
        if hits:
            results.append({
                "kind": "claim",
                "number": c.issue,
                "title": c.title,
                "author": c.author,
                "url": c.url,
                "overlapping": hits,
            })
    return results


# ----------------------------------------------------------------------- output


def _table(rows: list[list[str]], headers: list[str]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row)]
    def fmt(row: list[str]) -> str:
        return "  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip()
    lines = [fmt(headers), fmt(["-" * w for w in widths])]
    lines += [fmt(r) for r in rows]
    return "\n".join(lines)


def _clip(text: str, n: int = 50) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _md_escape(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")


def render_overlap_comment(pr_number: int, overlaps: list[dict]) -> str:
    lines = [OVERLAP_MARKER, f"### Overlap check for #{pr_number}", ""]
    if not overlaps:
        lines.append("No overlap now: no other open PR or active claim touches these files.")
    else:
        lines += [
            "This PR touches files that other open work also touches. "
            "Coordinate with the people below before going further.",
            "",
            "| Kind | # | Title | Author | Overlapping paths |",
            "| --- | --- | --- | --- | --- |",
        ]
        for o in overlaps:
            kind = "PR" if o["kind"] == "pr" else "Claim"
            paths = ", ".join(f"`{_md_escape(p.replace('`', ''))}`" for p in o["overlapping"][:20])
            if len(o["overlapping"]) > 20:
                paths += f" (+{len(o['overlapping']) - 20} more)"
            lines.append(
                f"| {kind} | [#{o['number']}]({o['url']}) | {_md_escape(o['title'])} "
                f"| @{o['author']} | {paths} |"
            )
    lines += ["", "<sub>Updated by scripts/pr-overlap.py.</sub>"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------- commands


def cmd_check(args: argparse.Namespace) -> int:
    files = parse_paths(args.files)
    if not files:
        print("error: --files is empty", file=sys.stderr)
        return EXIT_ERROR
    excl = {args.exclude_issue} if args.exclude_issue is not None else set()
    overlaps = find_overlaps(args.repo, files, exclude_pr=args.exclude_pr, exclude_issues=excl)
    if args.json:
        print(json.dumps(overlaps, indent=2, ensure_ascii=False))
    elif not overlaps:
        print("No overlap: no open PR or active claim touches " + ", ".join(files))
    else:
        rows = [
            [o["kind"], f"#{o['number']}", _clip(o["title"]), "@" + o["author"],
             ", ".join(o["overlapping"]), o["url"]]
            for o in overlaps
        ]
        print(_table(rows, ["KIND", "#", "TITLE", "AUTHOR", "OVERLAPPING", "URL"]))
    return EXIT_OVERLAP if overlaps else EXIT_OK


def cmd_comment(args: argparse.Namespace) -> int:
    repo, number = args.repo, args.pr
    pr = json.loads(run_gh(["api", f"repos/{repo}/pulls/{number}"]))
    files = pr_files(repo, number)
    author = _login(pr.get("user"))
    # The PR's own linked issues and its author's claims are the same work, not overlap.
    own_issues = linked_issues(pr.get("body") or "") | linked_issues(pr.get("title") or "")
    overlaps = find_overlaps(
        repo, files, exclude_pr=number, exclude_issues=own_issues,
        exclude_claim_authors={author} if author else set(),
    ) if files else []

    existing = None
    for c in gh_api_list(f"repos/{repo}/issues/{number}/comments"):
        if OVERLAP_MARKER in (c.get("body") or ""):
            existing = c
            break

    body = render_overlap_comment(number, overlaps)
    if existing:
        if (existing.get("body") or "").replace("\r\n", "\n") == body:
            print(f"Overlap comment on #{number} already up to date.")
        else:
            gh_api_write("PATCH", f"repos/{repo}/issues/comments/{existing['id']}", body)
            print(f"Updated overlap comment on #{number} ({len(overlaps)} overlap(s)).")
    elif overlaps:
        gh_api_write("POST", f"repos/{repo}/issues/{number}/comments", body)
        print(f"Posted overlap comment on #{number} ({len(overlaps)} overlap(s)).")
    else:
        print(f"No overlap for #{number}; nothing posted.")
    return EXIT_OK


def cmd_claims(args: argparse.Namespace) -> int:
    claims = fetch_active_claims(args.repo)
    if args.json:
        print(json.dumps([c.__dict__ for c in claims], indent=2, ensure_ascii=False))
        return EXIT_OK
    if not claims:
        print("No active claims.")
        return EXIT_OK
    rows = [
        [f"#{c.issue}", _clip(c.title, 40), "@" + c.author.replace(", ", ", @"), c.kind,
         c.expires or "-", ", ".join(c.files) or "(unknown)", _clip(c.plan, 50) or "-"]
        for c in claims
    ]
    print(_table(rows, ["ISSUE", "TITLE", "CLAIMANT", "KIND", "EXPIRES", "FILES", "PLAN"]))
    return EXIT_OK


# ------------------------------------------------------------------------- main


def _repo_arg(value: str) -> str:
    if not REPO_RE.match(value):
        raise argparse.ArgumentTypeError("expected owner/name")
    return value


def _positive_int(value: str) -> int:
    try:
        n = int(value.lstrip("#"))
    except ValueError:
        raise argparse.ArgumentTypeError("expected a number") from None
    if n <= 0:
        raise argparse.ArgumentTypeError("expected a positive number")
    return n


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pr-overlap.py",
        description="Find overlap between open PRs and active issue claims (uses the gh CLI).",
        epilog="Exit codes: 0 = no overlap, 3 = overlap (check), 2 = usage or gh error.",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="{check,comment,claims}")

    def add_repo(p: argparse.ArgumentParser) -> None:
        p.add_argument("--repo", required=True, type=_repo_arg, help="GitHub repository, owner/name")

    p = sub.add_parser("check", help="list open PRs and active claims overlapping the given files",
                       description="List open PRs and active claims whose paths overlap --files. "
                                   "Exit 0 = no overlap, 3 = overlap, 2 = error.")
    add_repo(p)
    p.add_argument("--files", required=True,
                   help='comma-separated repo paths; a trailing "/" means a whole directory')
    p.add_argument("--exclude-pr", type=_positive_int, metavar="N", help="ignore this PR")
    p.add_argument("--exclude-issue", type=_positive_int, metavar="N",
                   help="ignore the claim on this issue")
    p.add_argument("--json", action="store_true", help="print a JSON array instead of a table")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("comment", help="create or update the overlap comment on a PR",
                       description="Compute PR N's files, check overlap excluding itself, and "
                                   f"create or update one PR comment marked {OVERLAP_MARKER}.")
    add_repo(p)
    p.add_argument("--pr", required=True, type=_positive_int, metavar="N", help="pull request number")
    p.set_defaults(func=cmd_comment)

    p = sub.add_parser("claims", help="list active claims",
                       description="List active claims: claim comments and issue assignees.")
    add_repo(p)
    p.add_argument("--json", action="store_true", help="print a JSON array instead of a table")
    p.set_defaults(func=cmd_claims)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except GhError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
