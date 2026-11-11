#!/usr/bin/env bash
# Git guard for Claude Code: a PreToolUse hook on the Bash tool.
# Reads the hook JSON on stdin; exit 2 blocks the call and sends stderr back to the agent.
# Test a command without the harness: git-guard.sh --check 'git reset --hard'
# Patterns live in git-guard-patterns.txt beside this script.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
patterns="$here/git-guard-patterns.txt"

if [[ "${1:-}" == --check ]]; then
  command_text="${2:-}"
else
  input="$(cat)"
  if command -v jq >/dev/null 2>&1; then
    command_text="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)" || command_text="$input"
  else
    # No jq: pull the command string out with sed and undo JSON escapes; fall back to the raw JSON.
    command_text="$(printf '%s' "$input" | sed -nE 's/.*"command"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p' | sed 's/\\"/"/g')"
    command_text="$(printf '%b' "${command_text:-$input}")"
  fi
fi

if [[ ! -r "$patterns" ]]; then
  echo "git guard: pattern file missing at $patterns; blocking until it is restored." >&2
  exit 2
fi

active="$(grep -vE '^[[:space:]]*(#|$)' "$patterns")"
[[ -n "$command_text" && -n "$active" ]] || exit 0

hit="$(printf '%s\n' "$command_text" | grep -Eo -f <(printf '%s\n' "$active") | head -n 1)"
if [[ -n "$hit" ]]; then
  {
    echo "Blocked by the git guard: \"$hit\" can destroy work or rewrite shared history."
    echo "Use a safe form instead (git stash, a new branch, git push --force-with-lease to your own feature branch, a PR for the default branch),"
    echo "or ask the user to run it themselves."
  } >&2
  exit 2
fi
exit 0
