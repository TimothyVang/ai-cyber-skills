# Setup

Use when: a repo is about to use the planning flows (Spec, Tickets, Implement spec, Triage) for the first time, or the user asks to set deep-mode up in a repo ("set up deep-mode here", "configure the tracker", "add a glossary and ADRs", "switch this repo to a local tracker"). Runs once per repo; a re-run updates what is there and never overwrites the user's edits.

Every file this playbook writes is optional for the other flows. Each flow works without it by detecting what it needs; setup makes the choices stick and visible.

Files it may write:
- `docs/deep-mode/tracker.md`: tracker kind, repo, label strings, whether external PRs are triaged.
- `GLOSSARY.md` at the repo root, and `docs/adr/` (per the **domain-model** technique, `references/techniques/domain-model.md`).
- `CODING_STANDARDS.md` at the repo root: rules reviewers check that no tool enforces.
- A short `## deep-mode` section in `AGENTS.md` or `CLAUDE.md` that points to the files above.

## Steps

1. **Look** (read-only). `git remote -v`; `gh repo view --json nameWithOwner,hasIssuesEnabled,viewerPermission`; `gh label list --json name --limit 200`. Check for `docs/deep-mode/tracker.md`, `AGENTS.md`, `CLAUDE.md`, `GLOSSARY.md`, `docs/adr/`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, lint and format configs, and monorepo signals (workspace files, several packages with their own `src/`).
2. **Pick the tracker kind** (decide; don't ask, per SKILL.md Autonomy):
   - GitHub remote, issues enabled, and write permission → `github`.
   - No forge remote, or the user said local → `local` (`docs/deep-mode/issues/`).
   - Another forge or a tracker the user names (GitLab, Jira, Linear) → `other`: write each operation from the **tracker** technique (`references/techniques/tracker.md`) as one line of prose with the exact command or steps for that system.
3. **Map the labels.** For each role in the tracker technique's Label roles table, use an existing repo label with the same meaning when there is one (a repo `wontfix` serves `triage:wontfix`), else the role name. On `github`, create each missing label with `gh label create <name> --description "<meaning>"`. Never pass `--force`: it rewrites labels the user already styled.
4. **Write `docs/deep-mode/tracker.md`**:

   ```markdown
   # Tracker

   Kind: github | local | other
   Repo: <owner/name, or none>
   Triage external PRs: no

   ## Labels

   | Role | Label |
   |---|---|
   | bug | <label> |
   | ... | ... |

   ## Operations (kind other only)

   - Create: <how>
   - ...
   ```

   `Triage external PRs` defaults to `no`. The user turns it on by editing the file.
5. **Seed the domain docs.** No `GLOSSARY.md` → write the domain-model header (project name and one sentence on what it does) and an empty `## Terms`. Monorepo signals → one glossary per package that owns its own concepts, listed from the root file. No `docs/adr/` → create it with `0001-record-decisions-as-adrs.md`, an ADR in the domain-model format that records this setup choice.
6. **Seed `CODING_STANDARDS.md`** when absent. Fill it only with rules you can point to: each rule one line, with a `file:line` that follows it. Sources, in order: `CONTRIBUTING.md`, `AGENTS.md` or `CLAUDE.md`, then patterns the code already follows consistently. Leave out anything a linter, formatter, or type checker already enforces; the **pr-review** technique reads this file as its standards source.
7. **Point to it.** Edit `AGENTS.md` when it exists, else `CLAUDE.md` when it exists, else create `AGENTS.md`. Add or update one `## deep-mode` section: one line each for the tracker file, the glossary, the ADR folder, and the standards file. Update the section in place on a re-run; never duplicate it or touch the rest of the file.
8. **Optional guardrails.** When the user asks for commit-time checks or protection against destructive git commands, run the **pre-commit** technique (`references/techniques/pre-commit.md`) or the **git-guardrails** technique (`references/techniques/git-guardrails.md`).
9. **Ship it** as one `chore(deep-mode): set up tracker and project docs` change through Opening a PR (`references/playbooks/opening-a-pr.md`).
10. **Resume the request.** When setup ran because the user asked for Spec, Tickets, Implement spec, or Triage, run that playbook now, in the same session. Don't wait for the setup PR to merge: each flow detects the tracker on its own, and Setup has already created the labels.

## Gates

- Never overwrite an existing glossary, ADR, standards file, or user section. Merge into them.
- Labels are created, never renamed or deleted.
- A tracker of kind `github` must answer `gh issue list -R <repo> --limit 1` before the file says so. If it can't, use `local` and say why.

## Evidence

- The tracker kind and why; the label table with which labels were created and which were mapped to existing ones.
- Each file written or updated, with its path.
- The pointer section's location.
- Done when `docs/deep-mode/tracker.md` exists, every mapped label exists on the tracker, the setup PR is open, and any flow that routed here (step 10) has run to its own Evidence.
