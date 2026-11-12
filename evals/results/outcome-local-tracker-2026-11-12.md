# Outcome eval, local tracker, 2026-11-12

PR #33 (issue #29) changes how Spec, Tickets and Phased build use a local tracker: what each commit holds, which branch holds the tickets, and how a local issue number is picked.
The `billsplit` and `kitty` tasks never reach Spec, Tickets or a local tracker, so this run uses a task that does. Their standard rerun at `015cbad`, with hidden checks and both judges, is `outcome-pr33-2026-11-12.md`.
The routing eval reran too: `routing-local-tracker-2026-11-12.json`, 20/20 route and 20/20 size, $6.66. `SKILL.md` is unchanged by the PR (same SHA-256 `da4c08e7…` as `routing-light-lane-2026-11-12.json`).

## Setup

- Project: a 7-line Node notes CLI (`notes add`, `notes list`) with one `node:test` file, `git init` on `main`, no remote (rounds 1-3).
- `docs/deep-mode/tracker.md` names the local kind. `main` holds closed issue `0001`.
- Branch `spec/archive-notes`, not on `main`, holds issue `0002` and its spec file: another session's spec.
- Round 2 only: `refs/deep-mode/issues/0003` already exists (another session reserved `0003` and has not committed it), and the user has `TODO.md` staged on `main`.
- Request, through the `/deep` command body at each ref: write a spec and its tickets for `notes list --json` and `notes add --json <text>`, to be built later on one integration branch; stop once the tickets are published.
- Skills copied into `.omp/skills/` from each ref, as `run.py setup` does. One `omp -p` per candidate with `--no-rules --no-context-files --no-extensions --skills <every copied skill> --max-cost 6`, API keys removed, default model `anthropic/claude-opus-5-5`.
- Before: `97ced32` (origin/main). After: `4672da6` in round 1, `693fbb1` in round 2, `77b5f61` in round 3, `2596b54` in round 4 (this branch).
- Round 3 uses round 2's setup, except the reservation `refs/deep-mode/issues/0003` points at a blob, as `015cbad` requires. Only the after variant ran.
- Round 4 adds a shared bare remote. The candidate is a clone of it, and `tracker.md` names it as `Reservations: <url>`. After the clone, another contributor pushes `spec/archive-notes` (issue `0002`) and reserves `0003` on the remote, so neither is visible locally until a fetch. `TODO.md` is staged. Only the after variant ran, with `--model anthropic/claude-opus-5-5`.
- Scoring is the end state of each repo (`git branch`, `git log --name-status`, `git ls-tree` per branch, `git for-each-ref refs/deep-mode`) plus the final reply.

## Results

| Run | Skill | Spec issue | Ticket issues | Spec commit | Tickets commit | Default branch | Exit | Main-session cost |
|---|---|---|---|---|---|---|---|---|
| round 1 before | `97ced32` | `0002`, collides with `spec/archive-notes`; renamed to `0003` after a panel found it | `0003`-`0005`, renamed `0004`-`0006` | spec file and issue in separate commits | one commit | ran setup and merged a setup branch into `main` | 3 (cost cap, in a third panel round) | $3.88 |
| round 1 after | `4672da6` | `0003` | `0004`, `0005` | spec file and issue in one commit | one commit on `spec/json-output` | untouched | 0 | $1.57 |
| round 2 before | `97ced32` | `0002`, collides with `spec/archive-notes` | `0003`, collides with the reservation; `0004` | spec file alone; issue went in with the tickets | one commit with the spec issue | untouched; `TODO.md` still staged | 0 | $1.70 |
| round 2 after | `693fbb1` | `0004`, skipping `0002` on the other branch and the reserved `0003` | `0005`, `0006` | spec file and issue in one commit | one commit holding only the two tickets, on `spec/json-output` | untouched; `TODO.md` still staged | 0 | $1.09 |
| round 3 after | `77b5f61` | `0004`, skipping `0002` and the reserved `0003` | `0005`, `0006` | spec file and issue in one commit | one commit holding only the two tickets, on `spec/json-output` | untouched; `TODO.md` still staged | 0 | $1.65 |
| round 4 after | `2596b54` | `0004`, skipping `0002` and `0003`, both seen only after fetching the shared remote | `0005`, `0006` | spec file and issue in one commit | one commit holding only the two tickets, on `spec/json-output`, pushed | untouched; `TODO.md` still staged | 0 | $1.30 |

Round 2 after reserved `refs/deep-mode/issues/0004` to `0006` before writing each file, so the numbers it took are visible to every worktree.
No run touched `spec/archive-notes`. Neither round 2 run put `TODO.md` in a commit: both worked in a worktree of the spec branch, so the staged file never sat in their index.
Round 3 worked in the main checkout itself, switched to `spec/json-output` with `TODO.md` staged, and both commits still held only their named paths. `TODO.md` stayed staged and uncommitted.
Round 4 fetched the reservation refs and `spec/archive-notes` from the remote named by `Reservations:`, then reserved `0004` to `0006` there: the shared remote holds all four `refs/deep-mode/issues/*` refs, each pointing at a blob.
Its first attempt, without `--model`, went to omp's current default (`openrouter/openai/gpt-6.1-sol`) and stopped after 17 s on a 402 credit error. That attempt changed nothing in the repo, and the run above repeated it on Opus.
A scratch-repo check covers the commit form the playbooks now name: with `other.txt` staged, `git commit -m spec -- docs/specs/a.md issue.md` committed exactly those two paths and left `other.txt` staged.

## Recommendation

Ship. The after runs give every new issue a number no other branch or session holds, commit the spec issue with its spec file, and commit the tickets alone on the integration branch, at a lower cost than the before runs.
Unproven here: two sessions racing for one number at the same moment. Checked by hand in scratch repos instead: a second `git update-ref <ref> <object> ''` from another worktree fails with "reference already exists", and a second clone's `git push --force-with-lease=<ref>: origin <ref>` is rejected as "stale info".
Round 2 reserved with a ref pointing at `HEAD`. Two clones at one commit then both "won", because the second push reported "Everything up-to-date", so `015cbad` points the ref at a per-session blob and confirms it with `git ls-remote`. In scratch repos with that form, the second clone lost the number and no local-only commit reached the remote.
