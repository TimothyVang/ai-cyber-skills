# security-audit

**Use when:** a PR needs a security audit before it merges ("audit this PR", "audit every PR", "add a security gate"), the repo opted into the gate (it has `.deep-mode/security-audit-accepted.txt`), or the change touches auth, permissions, input parsing, secrets, or anything an untrusted user can reach. It runs Cloudflare's security-audit skill (github.com/cloudflare/security-audit-skill, MIT) on the PR's diff and blocks the merge on a confirmed finding at or above a severity bar. Your own agent runs it; there is no CI job and no SaaS reviewer.

The pieces live in this skill's `assets/security-audit/`:
- `audit-pr.sh`: the runner. It checks the PR head out in a temporary worktree, pins the Cloudflare skill to one commit, computes the diff itself, runs the audit with the `claude` CLI under a locked-down profile, gates the result, and posts or updates one PR comment.
- `prompt.md`: the audit request. Full audit mode, `quick` profile, scoped to the precomputed diff, source-only.
- `gate.cjs`: turns `findings.json` into a pass or fail and the comment text.

## Run it

1. From a checkout of the target repo (bash with `git`, `gh`, `node`, and the `claude` CLI logged in): `bash <this skill>/assets/security-audit/audit-pr.sh <PR number>`. A local branch without a PR: `audit-pr.sh --range <base> <head>` prints the verdict and posts nothing. Add `--dry-run` to check the setup without a model call. It runs on Linux, macOS, and WSL. Native Windows (Git for Windows bash) can't run it: the pinned skill's validators need POSIX file flags Windows lacks, so the script stops before any model call.
   Done when the script has exited and you have its exit code.
2. Tune with environment variables when the defaults don't fit: `FAIL_AT` (default `high`), `BLOCK_ON_UNVALIDATED` (default `true`), `AUDIT_MODEL` (default `sonnet`), `AUDIT_AGENTS` (default `12`), `AUDIT_BUDGET_USD` (default `8`).
3. Exit code `0` passes; `1` blocks; `2` means the audit could not run here (native Windows, or no `claude` CLI). A block is a P0 finding in the **pr-review** technique and blocks the **panel** like any failed check. The comment carries the marker `<!-- deep-mode-security-audit -->`; each run updates the same comment.
4. Exit `2`, or a harness with no `claude` CLI → the gate has not run. Say so in the report, never count it as a pass, and brief one **panel** verifier to read the diff for the security boundary (auth, permissions, input parsing, secrets) instead.
   Done when the report says the gate did not run and the verifier's result is in.

Done when the PR has the audit comment for its current head and the gate passed, or every blocking finding is fixed or accepted.

## Reading the result

- `confirmed`: a reproduced boundary violation with a severity. At or above `FAIL_AT`, it fails the gate. Fix it in the PR.
- `needs_validation`: a source-grounded lead with an exact unresolved fact. It has no severity, and by default it blocks: the audit reads source and doesn't run code, so a real injection usually lands here rather than as `confirmed`. Settle each one: fix it, or prove it isn't exploitable and accept it with a separate PR that adds `<fingerprint> # <reason and proof>` to `.deep-mode/security-audit-accepted.txt`. The runner reads acceptances from the base branch only, so a PR can't accept its own findings; the acceptance PR passes its own panel first.
- No `findings.json`, or one that fails the skill's validator → the gate fails closed. Read the run output; fix the run, never the gate.

## Limits

- The audit reads source only. A finding needs a reproduced result to be `confirmed`, so most leads land as `needs_validation`.
- `prompt.md` and `gate.cjs` come from your installed skill, and acceptances from the base branch, so a PR can't weaken them. The agent runs from an empty folder with the PR's `.claude/` settings, hooks, `.mcp.json`, and `CLAUDE.md` ignored, has no shell beyond the two validators, reads only its temp folder, and writes only its output folder. The pinned skill is reset before gating.
- The audit agent reads the PR's text, so a hostile PR can try to talk it into writing an empty `findings.json`. For PRs from people you don't trust, the panel and a human read the diff; the gate alone is not enough.
- One run finds roughly half of what repeated runs find (Cloudflare's own measurement). The gate is a floor, not a clearance.
- Each run spends model budget (`AUDIT_BUDGET_USD`, default $8). Run it once per head that will merge, not on every push.
