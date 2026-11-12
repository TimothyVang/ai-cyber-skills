# Outcome eval, light lane, 2026-11-12

The `billsplit` outcome eval (`evals/outcome/README.md`) found that deep-mode's size S lane cost 5 to 12 times a plain run on a one-file fix.
This run measures where that cost goes, trims the S lane, and measures again.

## Setup

- Same task, prompt, project, and `run.py` as `outcome-2026-11-12.md`. Only the with-deep-mode variant ran.
- `run.py setup --ref <commit> --per-variant 2` built four folders. The two plain candidates were deleted from `key.json` and from disk before `run.py run`, so only the two deep-mode candidates ran.
- Before: skill and `/deep` command at `8fc7436` (origin/main, 0.7.0).
- After: skill and `/deep` command at `44eb824` (this branch, the trim below).
- Every candidate ran on omp's default model `anthropic/claude-opus-5-5`, capped at `--max-cost 3`. The before runs' verifiers ran on `openai-codex/gpt-6.1-terra`.
- Scoring is `run.py collect`'s objective checks plus my reading of each diff, reply, and event log. No judge ran, since both rounds are one variant.
- Cost is omp's reported cost for the candidate plus its helper agents. Tool calls include the helpers' calls. Wall time is first to last session timestamp.

## Before and after

| Run | Skill | Cost | Tool calls | Wall time | Fix correct (9 CLI splits) | Spec fails on old code | Diff lines | Unrequested changes |
|---|---|---|---|---|---|---|---|---|
| before-2 | `8fc7436` | $1.36 | 63 (34 main, 29 verifier) | 4.8 min | 9/9 | yes, 3 tests | 28 | Rejects totals over 2^51 cents (about $22.5 trillion). Committed and fast-forwarded local `main`. |
| before-3 | `8fc7436` | $1.91 | 72 (40 main, 32 verifier) | 9.0 min | 9/9 | yes, 2 tests | 20 | Rejects totals of 2^46 dollars (about $70 trillion) or more. Committed and fast-forwarded local `main`. |
| after-2 | `44eb824` | $0.60 | 11 | 0.7 min | 9/9 | yes, 1 test | 15 | None. Left uncommitted. |
| after-3 | `44eb824` | $0.61 | 11 | 0.7 min | 9/9 | yes, 2 tests | 22 | None. Left uncommitted. |

Medians: cost $1.64 before and $0.61 after, 63% less.
Tool calls 67.5 before and 11 after, 84% less.
Wall time 6.9 minutes before and 0.7 minutes after.
Both rounds wrote the same core fix: split in whole cents and give the leftover cents to the first people.
No tool call in any run touched a path outside its folder (`collect`'s scan, 0 hits in all four).
The four runs cost $4.48 in all.

## Where the before runs spent it

From the event logs, scored by `.scratch/breakdown.py` (not committed).
Each assistant turn's cost is split evenly over the tool calls it issued.

| Phase | before-2 | before-3 |
|---|---|---|
| Up to the verifier spawn (read skill, look around, reproduce, worktree, fix, test, commit) | 16 calls, $0.74 | 14 calls, $0.74 |
| Panel loop in the main session (spawn, wait, answer findings, re-test, amend, merge) | 18 calls, $0.53 | 26 calls, $1.04 |
| Verifier helpers | 29 calls, $0.09 | 32 calls, $0.13 |

Inside those phases:

- **Panel loop.** With its verifiers it made 46% and 61% of the cost. before-2 ran one verifier for two rounds. before-3 spawned three verifiers in a row.
  Every failing round failed only on totals in the tens of trillions. Each answer was a size guard, a re-test, and an amended commit.
  The main session's `wait` calls alone were 8 calls and $0.16 in before-2, and 12 calls and $0.26 in before-3.
  The verifiers' own cost is low because omp reports little cost for the `openai-codex` subscription model. Their findings drove the main session's turns.
- **Reference reads.** Each run read `SKILL.md`, then `opening-a-pr.md`, `panel.md` twice, and `pr-review.md`. That is 5 to 6 calls.
  Their turns are cheap, but every later turn re-reads the files from the context cache.
- **Worktree and scratch setup.** 2 and 4 calls to create `.scratch/`, `.worktrees/`, a branch, and to clean probe scripts.
- **Git bookkeeping.** Commit, amend after each finding, and a fast-forward of local `main`.
- **Not seen.** Neither run kept a decision log, created a verify skill, or opened a todo list.

## Where the after runs spend it

| Part | after-2 | after-3 |
|---|---|---|
| Read `SKILL.md` and two look-around turns (cold cache, system prompt and skill) | 3 calls, $0.43 | 3 calls, $0.43 |
| Reproduce, failing test, fix, test, prove on the CLI | 8 calls, $0.14 | 8 calls, $0.15 |
| Reply | $0.03 | $0.03 |

Each after run also lost one or two edits to a stale-tag retry from the edit tool, which is the harness, not the skill.

## What the after runs gave up

The before runs' verifiers found that a total in the tens of trillions of dollars can split a cent short, since a double no longer holds every cent.
The after fixes, like the plain runs in `outcome-2026-11-12.md`, still have that edge.
They leave the change uncommitted for the user, so nothing lands without a person looking at it.
Neither round restated the goal as its first visible message. The trim did not change that.

## What changed in the skill

- `SKILL.md`, Route step 3, the S row now reads:
  "Restate in one line, fix, add a test that fails without the fix, prove it once on the real artifact. A **local S fix** (no remote, or the user reviews it first) stops there, uncommitted, reading no reference file. To push or merge, take the S lane (`references/playbooks/opening-a-pr.md`) and its light panel. No other subagents, architect, or decision log."
- `SKILL.md`, Non-negotiables, the S line now reads:
  "For size **S**, only the one-line restate, the Scope ledger, proving it on the real artifact (no new verify skill), and, if it ships, the S lane apply."
- `SKILL.md`, Prove it on the real artifact, `create-verification-skill` now runs only when "an M or L task changes user-visible behavior".
- `SKILL.md`, Autonomy, the light panel bullet adds "A local S fix needs none."
  Nothing lands on a default or shared branch without a panel pass, so the rule itself is unchanged.
- `SKILL.md`, Any PR, the bullet "Size S takes the S lane instead" is removed. The S row and the Non-negotiables S line already say it, and the bytes keep the rules above `## Routes` at 19,987, under 20,000.
- `opening-a-pr.md`, Size S lane, defines the local S fix and its done-when. An S change that is pushed or merged takes the S lane and the light panel as before.
- `panel.md` names the local S fix as needing no panel. The light panel's verifier now keeps its break attempt within inputs the code plausibly sees. A failure only past that is a follow-up, not NOT DONE. This part did not run in this eval.
- `commands/deep.md` adds: "A small fix with no remote to push to, or one I said I'd review, stays an uncommitted local change: fix, a test that fails without the fix, one real run, then report. It needs no panel."

## Limits

- Two runs per round on one task. The drop is large and the same in both runs, but the sample is small.
- The task's repo has no remote, so this eval exercises only the local S fix. The pushed S lane and the light panel's realistic-input brief are unmeasured.
- The deep-mode bot's own light panel brief lives in `bot.py`, which this change does not touch.
