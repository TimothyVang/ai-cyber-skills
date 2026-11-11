# pr-agent

**Use when:** after opening a PR and after each later push to it, or when the user asks for PR-Agent ("run pr-agent", "/describe", "/review", "/improve"). It runs PR-Agent (github.com/The-PR-Agent/pr-agent, MIT) from your machine, powered by the subscription omp is logged into (Claude or Codex). There is no GitHub Action and no API key.

`assets/pr-agent/pr_agent_local.py` in this skill does the wiring. It serves an OpenAI-compatible endpoint on `127.0.0.1` that answers each PR-Agent call with `omp -p` on omp's current model, with no tools, MCP servers, plugins, skills or context files (a `--config` overlay turns off every discovery source, since `--no-tools` alone leaves MCP tools mounted) and API-key variables removed, so the subscription's usage pays. `@` mentions in the PR text are defanged, because omp would otherwise attach the named local file to the prompt. It passes `gh auth token` to PR-Agent and runs the pinned `pr-agent` through `uvx`.

1. **Check the tools:** `omp` logged in to a subscription, `gh` logged in, `uvx` on PATH. A missing login is a hard stop for the user (`omp` → `/login`, `gh auth login`).
2. **Run the three commands** on the PR, in order, from any directory:
   ```bash
   python <deep-mode skill dir>/assets/pr-agent/pr_agent_local.py <pr-url> describe
   python <deep-mode skill dir>/assets/pr-agent/pr_agent_local.py <pr-url> review
   python <deep-mode skill dir>/assets/pr-agent/pr_agent_local.py <pr-url> improve
   ```
   Each posts to the PR as the user, which needs no ask on the user's own PRs. On someone else's PR, add `--dry-run` to read the output without posting; posting there is a hard stop. `--model` picks the model (default: omp's current one). `ask "<question>"` asks about the PR.
3. **Triage what it says.** Each review finding and code suggestion is a review comment: fix, dismiss with proof, or escalate, per Babysit's review-comment triage (`references/playbooks/babysit.md`). Its "security concerns" line goes through the **security-audit** technique (`references/techniques/security-audit.md`) when it names a real data flow.
4. **Feed the panel.** Give the review text to the panel's verifiers (`references/techniques/panel.md`) as one more input. PR-Agent never votes, and its approval is not a verdict.

**Done when** describe, review, and improve have run on the PR's current head and every finding has a triage outcome.

## Limits

- Each command is one or a few model calls (about 30 to 120 seconds each) and counts against the subscription's usage limits.
- PR-Agent sees the diff and some surrounding lines, not the whole repo; large PRs are compressed. It complements the panel and pr-review; it never replaces running the change.
