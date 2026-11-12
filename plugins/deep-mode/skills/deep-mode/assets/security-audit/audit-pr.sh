#!/usr/bin/env bash
# deep-mode security gate, run by your own agent: Cloudflare's security-audit skill scoped to one
# PR's diff, then gate.cjs turns the findings into pass/fail and one PR comment.
#
# Usage (from a checkout of the target repo, with gh, node, git, and the claude CLI logged in):
#   audit-pr.sh <pr-number>            audit the PR, post or update its comment, exit 1 to block
#   audit-pr.sh --range <base> <head>  audit a local range, print the verdict, post nothing
#   add --dry-run to stop after preparing the diff and prompt (no model call)
# Exit 2: the audit cannot run on this machine (native Windows, or no claude CLI). That is not a pass.
#
# Trust: prompt.md and gate.cjs come from this skill install, never from the PR. Accepted
# findings come from the base branch's .deep-mode/security-audit-accepted.txt, so a PR can't
# accept its own findings. The PR head is checked out in a temporary worktree.
set -euo pipefail

SKILL_REPO="${SKILL_REPO:-https://github.com/cloudflare/security-audit-skill}"
SKILL_SHA="${SKILL_SHA:-c1c8a8c1471069fb0e188eeaff69b8e8db6564a8}"
AUDIT_MODEL="${AUDIT_MODEL:-sonnet}"
AUDIT_AGENTS="${AUDIT_AGENTS:-12}"
AUDIT_BUDGET_USD="${AUDIT_BUDGET_USD:-8}"
FAIL_AT="${FAIL_AT:-high}"
BLOCK_ON_UNVALIDATED="${BLOCK_ON_UNVALIDATED:-true}"
ACCEPTED_PATH=".deep-mode/security-audit-accepted.txt"
MARKER="<!-- deep-mode-security-audit -->"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=false
PR=""
if [ "${1:-}" = "--range" ]; then
  BASE_REF="$2"; HEAD_REF="$3"; shift 3
else
  PR="${1:?usage: audit-pr.sh <pr-number> | --range <base> <head> [--dry-run]}"; shift
fi
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true

# The pinned skill's validators open their input with O_NOFOLLOW and O_NONBLOCK, which Windows doesn't have, so
# on Git for Windows the gate could only fail closed after the model budget was spent. Stop first.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    echo "audit-pr.sh can't run on native Windows: the pinned security-audit validators need POSIX file flags." >&2
    echo "Run it from WSL, Linux, or macOS. This is not a pass." >&2
    exit 2 ;;
esac
if ! $DRY_RUN && ! command -v claude >/dev/null 2>&1; then
  echo "audit-pr.sh needs the claude CLI for its locked-down audit run, and it isn't on PATH. This is not a pass." >&2
  exit 2
fi

T="$(mktemp -d)"
cleanup() { git worktree remove --force "$T/target" >/dev/null 2>&1 || true; rm -rf "$T"; }
trap cleanup EXIT

if [ -n "$PR" ]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
  read -r BASE_NAME HEAD_SHA < <(gh pr view "$PR" --json baseRefName,headRefOid -q '.baseRefName + " " + .headRefOid')
  git fetch --quiet origin "$BASE_NAME" "pull/$PR/head"
  BASE_REF="origin/$BASE_NAME"
  HEAD_REF="$HEAD_SHA"
fi
BASE_SHA="$(git rev-parse "$BASE_REF")"
HEAD_SHA="$(git rev-parse "$HEAD_REF")"

git worktree add --quiet --detach "$T/target" "$HEAD_SHA"
git clone --quiet --filter=blob:none "$SKILL_REPO" "$T/skill"
git -C "$T/skill" checkout --quiet "$SKILL_SHA"
SKILL="$T/skill/skills/security-audit"
OUT="$T/audit"
mkdir -p "$OUT" "$T/agent-cwd"

# The diff is computed here, not by the agent. --text and --no-textconv stop the PR's
# .gitattributes from hiding changed lines as "binary".
git diff --no-ext-diff --no-textconv --text "$BASE_SHA...$HEAD_SHA" > "$T/pr.diff"
git diff --name-only "$BASE_SHA...$HEAD_SHA" > "$T/pr.files"
sed -e "s|{{SKILL}}|$SKILL|g" -e "s|{{OUT}}|$OUT|g" -e "s|{{BASE}}|$BASE_SHA|g" \
  -e "s|{{HEAD}}|$HEAD_SHA|g" -e "s|{{AGENTS}}|$AUDIT_AGENTS|g" -e "s|{{TARGET}}|$T/target|g" \
  -e "s|{{DIFF}}|$T/pr.diff|g" -e "s|{{FILES}}|$T/pr.files|g" "$HERE/prompt.md" > "$T/prompt.md"
echo "audit: base ${BASE_SHA:0:7} head ${HEAD_SHA:0:7}, $(wc -l < "$T/pr.files") files changed" >&2

if $DRY_RUN; then
  echo "dry run: prepared $T/prompt.md and $T/pr.diff; stopping before the model call" >&2
  exit 0
fi

# Run from an empty folder with user settings only, no hooks, and no MCP servers, so the PR's
# .claude/ settings, hooks, .mcp.json, and CLAUDE.md never load. Reads stay in the temp folder.
READS="Read(/$T/**),Grep(/$T/**),Glob(/$T/**)"
( cd "$T/agent-cwd" && claude -p --model "$AUDIT_MODEL" --output-format json --permission-mode dontAsk \
    --setting-sources user --settings '{"disableAllHooks": true}' --strict-mcp-config \
    --allowedTools "$READS,Write(/$OUT/**),Edit(/$OUT/**),Task,TodoWrite,Bash(node $SKILL/validate-findings.cjs:*),Bash(node $SKILL/validate-coverage-ledger.cjs:*)" \
    --disallowedTools "WebFetch,WebSearch" \
    --add-dir "$T" --max-budget-usd "$AUDIT_BUDGET_USD" \
    < "$T/prompt.md" > "$T/claude.json" ) \
  || echo "warning: the audit agent exited non-zero; the gate decides from its output" >&2

# The agent could write inside $T, so restore the pinned skill before gating.
git -C "$T/skill" reset --quiet --hard "$SKILL_SHA"
git -C "$T/skill" clean -fdxq
git show "$BASE_SHA:$ACCEPTED_PATH" > "$T/accepted.txt" 2>/dev/null || : > "$T/accepted.txt"
set +e
node "$HERE/gate.cjs" "$OUT" "$SKILL" "$FAIL_AT" "$BLOCK_ON_UNVALIDATED" "$T/accepted.txt" > "$T/comment.md"
code=$?
set -e
cat "$T/comment.md"

if [ -n "$PR" ]; then
  id=$(gh api "repos/$REPO/issues/$PR/comments" --paginate \
    --jq ".[] | select(.body | contains(\"$MARKER\")) | .id" | tail -n 1)
  if [ -n "$id" ]; then
    gh api -X PATCH "repos/$REPO/issues/comments/$id" -F body=@"$T/comment.md" > /dev/null
  else
    gh api "repos/$REPO/issues/$PR/comments" -F body=@"$T/comment.md" > /dev/null
  fi
fi
exit $code
