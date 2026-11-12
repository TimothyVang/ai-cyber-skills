#!/usr/bin/env python3
"""Claude Code hook: deny Write, Edit and NotebookEdit outside the project root (deepmodebot "Contain the work").

Hooks start it through claude-guard.sh, which picks a Python 3.8+ and denies the write when there is none.
Modes (first argument):
  (none)               PreToolUse: always enforce. Used by the deepmodebot skill's frontmatter hook.
  if-active <data-dir> PreToolUse: enforce only in sessions marked active. Used by the plugin's hooks.json.
  activate <data-dir>  UserPromptSubmit: mark the session active when the prompt runs a /deepmodebot: command.
                       The mark outlives the process, so a resumed session (same session id) stays guarded;
                       marks older than 30 days are pruned here.

The allowed roots are the worktree holding the session's cwd and its main checkout (they differ in a linked
worktree, e.g. one under <root>/.worktrees/ or an Orca workspace), or the cwd itself outside git. Also allowed:
Claude Code's own plan and project-memory dirs, and any `extraWriteRoots` listed in a root's .deepmodebot.json
(only paths the user named).
Bash, MCP tools and hook programs are not covered here.
"""
import json
import os
import re
import subprocess
import sys
import time

MARK_MAX_AGE_SECONDS = 30 * 24 * 3600


def real(path):
    return os.path.normcase(os.path.realpath(os.path.expanduser(path)))


def inside(path, root):
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # different drives on Windows
        return False


def project_roots(cwd):
    """The worktree holding cwd, then the main checkout (they differ in a linked worktree); cwd outside git."""
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--path-format=absolute", "--show-toplevel", "--git-common-dir"],
            capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return [cwd]
    lines = out.stdout.splitlines()
    if out.returncode or len(lines) < 2:
        return [cwd]
    toplevel, common = lines[0], lines[1].rstrip("/\\")
    return [toplevel, os.path.dirname(common)] if os.path.basename(common) == ".git" else [toplevel]


def allowed_roots(roots):
    claude_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join("~", ".claude")
    allowed = [*roots, os.path.join(claude_dir, "plans"), os.path.join(claude_dir, "projects")]
    for root in roots:
        try:
            with open(os.path.join(root, ".deepmodebot.json"), encoding="utf-8") as handle:
                extra = json.load(handle).get("extraWriteRoots") or []
            allowed += [p if os.path.isabs(os.path.expanduser(p)) else os.path.join(root, p) for p in extra if isinstance(p, str)]
        except (OSError, ValueError, AttributeError):
            pass
    return [real(r) for r in allowed]


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))


def session_mark(data_dir, event):
    session = re.sub(r"[^A-Za-z0-9_-]", "", str(event.get("session_id") or ""))
    return os.path.join(data_dir, "active-sessions", session) if data_dir and session else None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "enforce"
    try:
        event = json.load(sys.stdin)
    except ValueError:
        print("deepmodebot contain guard: unreadable hook input; not blocking", file=sys.stderr)
        return 0
    mark = session_mark(sys.argv[2] if len(sys.argv) > 2 else "", event)
    if mode == "activate":
        if mark and re.match(r"\s*/deepmodebot:", str(event.get("prompt") or "")):
            folder = os.path.dirname(mark)
            os.makedirs(folder, exist_ok=True)
            for name in os.listdir(folder):
                stale = os.path.join(folder, name)
                if time.time() - os.path.getmtime(stale) > MARK_MAX_AGE_SECONDS:
                    os.remove(stale)
            open(mark, "w").close()
        return 0
    if mode == "if-active" and not (mark and os.path.exists(mark)):
        return 0
    if event.get("tool_name") not in ("Write", "Edit", "NotebookEdit"):
        return 0
    tool_input = event.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(target, str) or not target:
        return 0
    cwd = event.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    path = real(target if os.path.isabs(os.path.expanduser(target)) else os.path.join(cwd, target))
    roots = project_roots(cwd)
    root = os.path.normpath(roots[0])
    if any(inside(path, r) for r in allowed_roots(roots)):
        return 0
    deny(f"deepmodebot keeps all writes inside the project root {root}. {target} is outside it. "
         f"Put scratch and temp files in {os.path.join(root, '.scratch')} and worktrees in "
         f"{os.path.join(root, '.worktrees')}. If the user explicitly named this path, add it to "
         f"extraWriteRoots in {os.path.join(root, '.deepmodebot.json')}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
