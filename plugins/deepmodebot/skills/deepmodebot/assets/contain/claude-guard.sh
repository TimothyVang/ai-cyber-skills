#!/usr/bin/env bash
# Claude Code hook entry for deepmodebot's write guard. Runs claude_guard.py with a working Python 3.8+.
# With none on PATH the guard cannot check where a write goes, so it fails closed: in a session where deepmodebot
# is active, every Write, Edit and NotebookEdit is denied until Python is installed.
#
# Usage (hook JSON on stdin):
#   claude-guard.sh enforce               PreToolUse, always on (the deepmodebot skill's frontmatter hook)
#   claude-guard.sh if-active <data-dir>  PreToolUse, only in sessions marked active (the plugin's hooks.json)
#   claude-guard.sh activate <data-dir>   UserPromptSubmit: mark the session when the prompt runs /deepmodebot:
# DEEPMODEBOT_GUARD_PYTHONS names the interpreters to try (default "python3 python"); the tests use it.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode="${1:-enforce}"
data="${2:-}"

for py in ${DEEPMODEBOT_GUARD_PYTHONS:-python3 python}; do
  if "$py" -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
    if [ "$mode" = enforce ]; then exec "$py" "$here/claude_guard.py"; fi
    exec "$py" "$here/claude_guard.py" "$mode" "$data"
  fi
done

# No Python. Keep the session mark working in plain shell, so the plugin hook still knows when to deny.
input="$(cat)"
session="$(printf '%s' "$input" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | tr -cd 'A-Za-z0-9_-')"
mark="$data/active-sessions/$session"
case "$mode" in
  activate)
    if [ -n "$data" ] && [ -n "$session" ] &&
        printf '%s' "$input" | grep -Eq '"prompt"[[:space:]]*:[[:space:]]*"([[:space:]]|\\[nrt])*/deepmodebot:'; then
      mkdir -p "$data/active-sessions" && : > "$mark"
    fi
    exit 0 ;;
  if-active)
    if [ -z "$data" ] || [ -z "$session" ] || [ ! -f "$mark" ]; then exit 0; fi ;;
esac
echo "deepmodebot write guard: no Python 3.8+ on PATH, so it cannot check where this write goes. The write is blocked. Install Python 3.8 or newer, then retry." >&2
exit 2
