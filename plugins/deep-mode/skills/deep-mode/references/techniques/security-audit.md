# security-audit

**Use when:** every PR in a repo should get a security audit in CI ("audit every PR", "add a security gate"), or one change needs a security audit before it merges. It runs Cloudflare's security-audit skill (github.com/cloudflare/security-audit-skill, MIT) scoped to the PR's diff, and blocks the PR on a confirmed finding at or above a severity bar.

The pieces live in this skill's `assets/security-audit/`:
- `security-audit.yml`: the GitHub Actions workflow. It runs on every PR, pins the Cloudflare skill to one commit, audits the diff with Claude Code, then gates and comments.
- `prompt.md`: the audit request. Full audit mode, `quick` profile, scoped to `git diff base...head`, source-only.
- `gate.cjs`: turns `findings.json` into a pass or fail and one PR comment that it updates on each run.

## Set up the gate in a repo

1. Copy `security-audit.yml` to `.github/workflows/security-audit.yml`, and `prompt.md` and `gate.cjs` to `.github/security-audit/`. Commit and push them on a branch and open a PR. That PR's own run proves the workflow.
2. The repo needs an `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` secret. Check with `gh secret list`; adding one is a hard stop for the user (`gh secret set ANTHROPIC_API_KEY`).
3. Tune the `env:` block when the defaults don't fit: `FAIL_AT` (default `high`), `BLOCK_ON_UNVALIDATED` (default `true`), `AUDIT_MODEL`, `AUDIT_AGENTS`, `AUDIT_BUDGET_USD`.
4. Make `security-audit / audit` a required status check on the default branch. Changing branch protection is a hard stop: hand the user `gh api -X PUT repos/<owner>/<repo>/branches/<branch>/protection ...` or the settings page.

Done when a PR shows the `security-audit` check and the gate's comment.

## Reading the result

- `confirmed`: a reproduced boundary violation with a severity. At or above `FAIL_AT`, it fails the check. Treat each confirmed finding as a P0 in the **pr-review** technique: fix it in the PR.
- `needs_validation`: a source-grounded lead with an exact unresolved fact. It has no severity, and by default it blocks: CI can't run code, so a real injection usually lands here rather than as `confirmed`. Settle each one: fix it, or prove it isn't exploitable and accept it by adding `<fingerprint> # <reason and proof>` to `.github/security-audit/accepted.txt` in the same PR, where the panel and reviewers see it.
- No `findings.json`, or one that fails the skill's validator → the gate fails closed. Read the job log; fix the run, never the gate.

## Limits

- CI has no sandbox, so the audit reads source only. A finding needs a reproduced result to be `confirmed`, so most CI leads land as `needs_validation`.
- Fork PRs get no secrets, so the job skips them. Audit those locally before merging.
- The prompt and gate are read from the base branch, so a PR can't weaken them, and the agent can write only inside its output folder. A PR can still edit the workflow file itself: protect `.github/` with CODEOWNERS or required review.
- The audit agent reads the PR's text, so a hostile PR can try to talk it into writing an empty `findings.json`. For PRs from people you don't trust, the panel and a human read the diff; the gate alone is not enough.
- One run finds roughly half of what repeated runs find (Cloudflare's own measurement). The gate is a floor, not a clearance.

## Audit one change locally

When the Cloudflare skill is installed (`npx skills add https://github.com/cloudflare/security-audit-skill --skill security-audit`), give it `prompt.md` with the placeholders filled in: `{{SKILL}}` the skill folder, `{{OUT}}` an output folder outside the repo, `{{BASE}}` and `{{HEAD}}` the commits, `{{AGENTS}}` the agent budget. Then run `node gate.cjs <out> <skill> high false` and act on the result as above.
