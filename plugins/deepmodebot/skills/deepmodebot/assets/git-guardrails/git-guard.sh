#!/usr/bin/env bash
# Git guard for Claude Code: a PreToolUse hook on the Bash tool.
# Reads the hook JSON on stdin; exit 2 blocks the call and sends stderr back to the agent.
# Test a command without the harness: git-guard.sh --check 'git reset --hard' (branch rules use the current directory).
# Patterns live in git-guard-patterns.txt beside this script.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
patterns="$here/git-guard-patterns.txt"

work_dir="$PWD"
if [[ "${1:-}" == --check ]]; then
  command_text="${2:-}"
else
  input="$(cat)"
  if command -v jq >/dev/null 2>&1; then
    command_text="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)" || command_text="$input"
    hook_cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)" || hook_cwd=""
  else
    # No jq: pull the strings out with sed and undo JSON escapes; fall back to the raw JSON.
    command_text="$(printf '%s' "$input" | sed -nE 's/.*"command"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p' | sed 's/\\"/"/g')"
    command_text="$(printf '%b' "${command_text:-$input}")"
    hook_cwd="$(printf '%s' "$input" | sed -nE 's/.*"cwd"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p' | sed 's/\\\\/\\/g')"
  fi
  work_dir="${hook_cwd:-$PWD}"
fi

if [[ ! -r "$patterns" ]]; then
  echo "git guard: pattern file missing at $patterns; blocking until it is restored." >&2
  exit 2
fi
[[ -n "$command_text" ]] || exit 0
command_text="${command_text//$'\\\n'/ }"  # a backslash-newline continues the command on the next line

block() {
  {
    echo "Blocked by the git guard: \"$1\" can destroy work or rewrite shared history."
    echo "Use a safe form instead (git stash, a new branch, git push --force-with-lease to your own feature branch, a PR for the default branch),"
    echo "or ask the user to run it themselves."
  } >&2
  exit 2
}

active="$(grep -vE '^[[:space:]]*(#|@|$)' "$patterns")"
if [[ -n "$active" ]]; then
  hit="$(printf '%s\n' "$command_text" | grep -Eo -f <(printf '%s\n' "$active") | head -n 1)"
  [[ -z "$hit" ]] || block "$hit"
fi

branch_rules="$(grep -E '^@branch ' "$patterns")"
if [[ -n "$branch_rules" ]]; then
  branch="$(git -C "$work_dir" symbolic-ref --short -q HEAD 2>/dev/null)"
  if [[ -n "$branch" ]]; then
    while read -r _ branch_regex command_regex; do
      [[ "$branch" =~ ^($branch_regex)$ ]] || continue
      hit="$(printf '%s\n' "$command_text" | grep -Eo -e "$command_regex" | head -n 1)"
      [[ -z "$hit" ]] || block "$hit (on $branch)"
    done <<< "$branch_rules"
  fi
fi
exit 0
