# pre-commit

**Use when:** "add pre-commit hooks", "set up husky / lint-staged / lefthook / pre-commit", "format and typecheck on commit", or a retro found the repo has no guardrail: nothing runs its lint, typecheck, and tests before code leaves the machine. The hook runs the repo's own checks at commit time, so agents get the error while the change is still in their context.

1. **Read what exists.** The repo's check commands (package scripts, `Makefile`, `justfile`, `pyproject.toml`, `Cargo.toml`, task runner) and the commands any CI workflow runs.
   - Existing hook setup (`.husky/`, `.pre-commit-config.yaml`, `lefthook.yml`, `core.hooksPath` in git config): extend it, never add a second hook manager.
   - The hook runs the same commands CI runs; when they differ, fix the gap in the same change.
   - Done when you can list every check command and the hook manager already in place, or that there is none.
2. **Pick the manager by language.** Use the repo's existing formatter and linter. Add one only when there is none, and say which and why. Done when one manager is chosen and named with its reason.

   | Repo | Manager | Pre-commit runs | Install |
   |---|---|---|---|
   | JS/TS | husky + lint-staged | formatter and linter fixes on staged files; `typecheck`; tests if fast | dev-install `husky lint-staged` with the lockfile's package manager; `npx husky init` adds the `prepare` script and `.husky/pre-commit` |
   | Python | `pre-commit` framework | ruff check `--fix` and ruff format; type checker and tests as `repo: local` hooks | `pre-commit install`, then `pre-commit autoupdate` to pin current revs |
   | Go, Rust, or several languages | lefthook (`lefthook.yml`) | Go: `gofmt -l -w {staged_files}`, `go vet ./...`. Rust: `cargo fmt --all`, `cargo clippy --all-targets -- -D warnings` | the repo's usual tool install, project-local first (`npm i -D lefthook`), then `lefthook install` |

   - JS/TS lockfiles pick the package manager: `package-lock.json` npm, `pnpm-lock.yaml` pnpm, `yarn.lock` yarn, `bun.lock` or `bun.lockb` bun.
   - Python's ruff hooks come from `https://github.com/astral-sh/ruff-pre-commit`, hook ids `ruff-check` (called `ruff` in older revs) and `ruff-format`. Local hooks use `language: system` and `pass_filenames: false`.
   - `go install github.com/evilmartians/lefthook@latest` and `brew install lefthook` are global installs and need the user's yes.

   Fixers that rewrite files must re-stage what they fixed (lint-staged does this; lefthook needs `stage_fixed: true`). Commands that use a project environment run through it (`uv run`, `poetry run`, `npx`, the repo's package manager).
3. **Keep it fast.** Time the full hook. Staged-file fixers always run on commit. Typecheck and tests run on commit when the whole hook stays under about 30 seconds; otherwise move them to `pre-push`. A hook so slow that people skip it protects nothing. Done when the timed hook is under 30 seconds, or the slow parts are on `pre-push`.
4. **Prove it blocks.** On a scratch branch, stage a file with a deliberate formatting error and one with a type or lint error; the commit must fail with a message naming the problem. Fix them; the commit must pass.
   - Run the manager's all-files mode once (`npx lint-staged` on a staged set, `pre-commit run --all-files`, `lefthook run pre-commit --all-files`) and fix or record pre-existing failures. Delete the scratch branch.
   - Done when you have the blocked commit's message and the passing commit, and every all-files failure is fixed or recorded.
5. **Land it.** Commit the config through the hook itself (the first real run), document the one-line setup for new clones in the README or `CONTRIBUTING.md` (`npm install` triggers `prepare`; `pre-commit install`; `lefthook install`), and open the PR through the Opening a PR playbook (`references/playbooks/opening-a-pr.md`). Done when the PR is open with the setup line documented.

**Hard rules.** Never commit with `--no-verify` to get past a failing hook; fix the code or the hook. Never weaken a check to make the first run pass; fix the existing violations or record them as a tracked issue. One hook manager per repo.

**Output:** the manager and hooks installed, the commands each stage runs and how long the hook takes, the proof (blocked commit message, then passing commit), and the PR.
