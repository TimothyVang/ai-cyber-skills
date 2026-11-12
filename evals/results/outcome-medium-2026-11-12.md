# Outcome eval, medium task, 2026-11-12

Design, tasks and rerun steps are in `evals/outcome/README.md`. The rubric is in `evals/outcome/tasks/kitty/rubric.md`.

## Variant under test

- deep-mode installed versus not installed, on the `kitty` task.
  The user asks for exact and percentage splits plus a `settle` command in a small ledger CLI.
- All 12 skills and the `/deep` command from commit `4e32373` (origin/main, plugin 0.8.0, with the cheaper local small-fix lane).
- Three candidates per variant, all on `anthropic/claude-opus-5-5`, each capped at `--max-cost 4`.
- Primary score is the 19 hidden checks, run on each candidate's checked-out tree.
- Secondary score is two blinded judges, `anthropic/claude-opus-5-5` and `openai-codex/gpt-6.1-terra`.
  Each scored the six-criterion rubric (0 to 2 each, out of 12) from its own copy of the cleaned pack.
- Harness `selftest` before the run: the original project passes 3 of 19 checks and the reference passes 19.

## Results

| Folder | Letter | Variant | Hidden checks | Cost | Tool calls | Wall time | Contaminated | Opus judge | Terra judge |
|---|---|---|---|---|---|---|---|---|---|
| kitty-1 | F | plain | 19/19 | $1.27 | 31 | 266 s | yes, system temp | 9 | 7 |
| kitty-3 | A | plain | 19/19 | $1.05 | 13 | 270 s | yes, system temp | 9 | 7 |
| kitty-4 | D | plain | 19/19 | $1.08 | 24 | 248 s | yes, system temp | 9 | 7 |
| kitty-2 | E | deep-mode | 19/19 | $4.12 (cap) | 117 | 606 s | flag only, failed read | 9 | 9 |
| kitty-5 | C | deep-mode | 3/19 (19/19 on its branch) | $4.33 (cap) | 73 | 530 s | no | 1 | 1 |
| kitty-6 | B | deep-mode | 3/19 (19/19 on its branch) | $4.04 (cap) | 63 | 508 s | flag only, failed read | 2 | 2 |

Costs and tool calls include helper agents. "(cap)" means omp's cost gate stopped the run before its next model request.
Every deep-mode run hit the $4 cap and none of them finished. The plain runs all finished on their own.

Variant means:

| Variant | Hidden checks | Cost | Tool calls | Wall time | Opus judge | Terra judge |
|---|---|---|---|---|---|---|
| plain | 19.0 | $1.13 | 23 | 261 s | 9.0 | 7.0 |
| deep-mode | 8.3 | $4.16 | 84 | 548 s | 4.0 | 4.0 |

Judge agreement: 91.7% of letter and criterion cells match exactly, and 91.7% match within one point.
The totals differ by 1.0 point on average, with a Spearman rank correlation of 0.898.
The judges cost $1.22 (Opus) and $0.26 (Terra). The whole run cost $17.36, of which the candidates took $15.88.

## Contamination hits, read by hand

No hit reached the hidden checks, the reference, the rubric, a sibling candidate, or the run data, so every hidden score stands.

- **kitty-1, kitty-3, kitty-4 (plain).** All three made scratch ledgers with a plain `mktemp -d`, which lands in system temp.
  kitty-1 also wrote `/tmp/chk.mjs`, then redid it inside the folder as `chk.tmp.mjs`. These are real writes outside the project, but they leak nothing.
- **kitty-2 (deep-mode).** A GPT reviewer it started tried to read `C:/Users/newbi/deep-mode/.scratch/review/diff.patch`.
  That is a garbled absolute path. The read returned "not found", and the reviewer then read the right file inside the folder.
- **kitty-6 (deep-mode).** Same pattern. A reviewer dropped `.worktrees/eval-medium/` from an absolute path, got "not found", and retried correctly.
- **Opus judge.** Flagged for a `grep -n "mktemp\|/tmp\|TMPDIR"` over the action logs. That is a false alarm.
  The judge itself admitted one real read outside its pack: a `git status` inside B's and C's repo copies reached the git repository above the pack. The scan cannot see that, because the call names no path.

## What every candidate built

All six designs agree. Money is kept in whole cents. Percentages are turned into cents when the expense is added, with leftover cents handed out so shares add up to the total.
`settle` finds the true fewest payments with a subset search for up to 16 to 20 people and falls back to largest-debtor-pays-largest-creditor above that.
Every candidate wrote specs that fail on the original code.
Wherever code reached the checked-out tree, it passes all 19 hidden checks.

## Per-candidate notes (from transcripts)

- **A (kitty-3, plain).** 13 tool calls. Read all files in one command, rewrote `ledger.js` and `report.js` with here-docs, and tested on the CLI in a system temp folder.
  It changed `balances` to whole cents, so the README example moves by a cent, and the reply says so.
  The reply is clear and complete but quotes results rather than showing commands.
- **D (kitty-4, plain).** 24 calls. Kept the old `balances` rounding for `--among` and let `settle` move the stray cent, which the reply explains.
  It brute-force checked its fewest-payments search against random cases.
- **F (kitty-1, plain).** 31 calls. Same design as A, plus a brute-force check over 3,000 random cases.
- **E (kitty-2, deep-mode).** Read the skill, the feature playbook, several principles and techniques, and `create-verification-skill`.
  It built a `verify-kitty` skill under `.omp/skills/` and drove the CLI through it. It worked on a branch in the main folder and committed twice.
  It then started a four-lens self-review on several model families. A GPT reviewer pushed amounts near $90 trillion, where a double loses cents.
  E was adding an unrequested $1,000,000,000 cap on amounts, uncommitted, when the cap stopped it.
  Its last message to the user is "Same root cause as my probe. Implementing the boundary fix while the others finish, test first:".
- **C (kitty-5, deep-mode).** Same opening as E, then did all the work in a worktree on `feat/uneven-split-settle`.
  It added a `verify-kitty` skill under `.agents/`, an `AGENTS.md`, and an `.omp/RULES.md`, none of them requested.
  It committed on the branch and started four reviewers. It was stopped while drafting a panel brief, and the branch was never merged.
  Its last message is "While reviewers run, drafting the panel brief." The branch's code passes 19 of 19.
- **B (kitty-6, deep-mode).** Same path as C: worktree on `feat/split-settle`, a `verify-kitty` skill, four reviewers, stopped before merging.
  Its last message is "Self-review comes next. ..." The branch's code passes 19 of 19.

## Judge verdicts

Per-criterion scores, in rubric order:

1. requested behavior
2. money adds up
3. fits the existing code
4. regression specs
5. evidence in the reply
6. scope and containment

| Letter | Opus | Terra |
|---|---|---|
| A | 2 2 2 2 1 0 = 9 | 2 0 2 2 1 0 = 7 |
| B | 0 0 0 0 0 2 = 2 | 0 0 0 0 0 2 = 2 |
| C | 0 0 0 0 0 1 = 1 | 0 0 0 0 0 1 = 1 |
| D | 2 2 2 2 1 0 = 9 | 2 0 2 2 1 0 = 7 |
| E | 2 2 2 2 0 1 = 9 | 2 2 2 2 0 1 = 9 |
| F | 2 2 2 2 1 0 = 9 | 2 0 2 2 1 0 = 7 |

The judges split on one criterion, "money adds up", for A, D and F.
Terra entered amounts near $90 trillion, where cents drift because the total no longer fits a double exactly. I reproduced it on kitty-3: $90,071,992,547,409.93 is stored as $...409.94.
The same build is exact at $1,000,000. E got 2 there only because its unrequested cap refuses such amounts.
This is the same disagreement as the first outcome run. A GPT-family check rewards an input cap that a GPT-family reviewer asked for, on input no flat will ever enter.
I side with Opus on this criterion.

My own reading matches Opus otherwise. Both judges scored B and C on their checked-out trees, as the design says. Neither saw the branches.
Both docked plain runs for writing to system temp, and docked E for an unfinished reply and an unrequested cap.

## Synthesis

On this medium task, deep-mode's extra cost bought nothing a user would get.

- Correctness is the same. Every candidate that delivered code passes 19 of 19, and the two unmerged deep-mode branches would too.
  The traps did not separate the variants. Opus without deep-mode avoided every one of them in about four and a half minutes for about $1.10.
- Delivery is worse. All three deep-mode runs spent their $4 before finishing.
  Two left the user's working tree untouched, with the work on an unmerged branch in a worktree.
  None of the three ended with a reply a user could act on.
- Cost and time are higher, at 3.7 times the cost, 3.7 times the tool calls, and 2.1 times the wall time, cut off.
  The money went to process. That means reading many reference files, building a project verification skill on a five-file CLI, worktree setup, and four-lens review panels on several model families.
- The one real gain is containment. All three plain runs wrote scratch ledgers to system temp. All three deep-mode runs kept every write inside the project, as the skill's contain rule says.
- The cross-family review again found only an extreme-input edge (amounts near $90 trillion). It again led to an unrequested input cap.

Limits of this run:

- Three candidates per variant on one task.
- The $4 cap decided two of the three deep-mode scores. With a higher cap, B and C would likely have merged code that passes every check, at well over $4 each.
- The hidden checks score only the checked-out tree.

## Recommendation

Do not promote the claim that deep-mode does medium features better. On this task it reached the same code at about 3.7 times the cost and failed to deliver within a $4 budget.

Changes to try before the next run:

- Keep medium features on the current branch until the work is done and checked, or merge the worktree before starting review panels. A run stopped early should still leave the user's tree changed.
- Scale review to risk. A four-lens, multi-family panel on a 400-line change to a zero-dependency CLI cost more than the feature itself.
- Build a project verification skill only when the project will be worked on again, not inside a one-off change.
- Tell verifiers to stay within realistic inputs, or have the author answer an extreme-input finding in the reply rather than by adding a cap.
- Keep the contain rule. It is the one behavior that measurably differed in deep-mode's favor.

Next run: the same task and cap after those changes, plus one run at a $10 cap to measure what finishing costs.
