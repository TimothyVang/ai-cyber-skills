# Outcome eval

Does installing deep-mode make an agent fix a real bug better?
This eval follows the Eval playbook (`plugins/deep-mode/skills/deep-mode/references/playbooks/eval.md`) step by step.

## Design

- **Variant under test.** deep-mode installed versus not installed.
- **With deep-mode.** The skill from a chosen commit is copied into the candidate's `.omp/skills/deep-mode/`.
  The prompt starts with what `/deep` expands to (`plugins/deep-mode/commands/deep.md` at that commit), with the bug report as its request.
- **Without.** The same project and the same bug report, nothing else.
- **Task.** `project/` is `billsplit`, a small Node CLI that splits a restaurant bill.
  `splitEvenly` rounds each share on its own, so `$100` three ways prints `$33.33` three times and loses a cent.
  `$200` three ways gains a cent.
  The suite in `spec/` passes and never splits an uneven amount.
- **Prompt.** `prompt.txt`, a bug report in a user's words. It never names tests, skills, or the experiment.
- **Candidates.** Two per variant, four in all, assigned to folders `.scratch/billsplit-1` to `-4` in a seeded random order.
  Each folder is its own `git init` repo with one commit.
  `.omp/` sits in `.git/info/exclude` in every folder, so `git status` looks the same in both variants.
- **Isolation.** Each candidate is one `omp -p --max-cost 3` process with its folder as the working directory.
  Both variants run with `--no-rules --no-context-files --no-extensions`, so the user's global `AGENTS.md`, rules, and contain hook stay out.
  The deep-mode candidates run with `--skills deep-mode`, which loads the project copy.
  The others run with `--no-skills`, because deep-mode is also installed globally on the machine that ran this.
  The API keys are removed from the child's environment.
- **Judge.** One blinded `task` subagent on a different model family from the candidates scores all four in one pass.
  It sees each candidate by a shuffled letter, never by folder, variant, or model.

## Rubric

The judge gets this. Candidates never see it.
Each criterion scores 0, 1 or 2, for a total out of 10.

1. **Fixed.** Run `node bin/billsplit.js <amount> --people <n> [--tip <p>]` on uneven and even splits.
   2 when every split adds up to the printed total exactly and no two shares differ by more than one cent.
   1 when some do. 0 when none do or the CLI breaks.
2. **Regression check.** 2 when the candidate added or changed a spec that fails on the original `src/` and passes on its fix.
   1 when it added one that passes on both. 0 when it added none.
3. **Contained.** 2 when every write and every command stayed inside the project folder.
   0 when anything was written outside it (system temp, home, sibling folders).
4. **Evidence in the reply.** 2 when the reply shows a command it ran and that command's output proving the fix.
   1 when it claims a check without showing output. 0 when it shows nothing.
5. **Diff size.** 2 when the change touches only what the fix needs (the split logic and its spec) in a small diff.
   1 when it adds related but unneeded changes. 0 when it rewrites unrelated code.

## Gates

The Eval playbook's blinding gates hold here.

- Candidate folders are named like a user's project (`billsplit-1`).
  No folder, file name, or prompt a candidate sees holds a gate word.
  The project's suite lives in `spec/*.spec.js` for that reason.
- Run data (prompts, event logs, sessions, the variant key) sits in `.scratch/billsplit-runs/`, outside every candidate folder.
- Candidates are never told about each other.
- The judge pack leaves `.git/`, `.omp/`, `.scratch/` and `.worktrees/` out of each copy and replaces folder paths with `<project>`.
  It drops every action line that reads a skill file and removes the phrase "light panel", which names deep-mode's verifier.
- Helper agents a candidate starts write their own session files. `collect` reads those too, for cost, actions, and the outside-path scan.
- One residual risk remains.
  Candidate folders sit inside this repo's `.scratch/`, so a candidate that lists its parent folder can see its siblings and this repo.
  `run.py collect` flags every absolute path outside the candidate's folder found in its tool calls, so a run can confirm none did.

## Rerun

```bash
rm -rf .scratch/billsplit-*                      # only from a previous run
python evals/outcome/run.py setup --ref HEAD     # four folders plus the variant key
python evals/outcome/run.py run                  # four omp processes at once, each capped at $3
python evals/outcome/run.py collect              # measurements plus the judge pack
```

`collect` prints one line per candidate and writes `.scratch/billsplit-runs/measurements.json`.
It holds cost, files changed, diff lines, each CLI split, the suite on the fix and on the original source, files read, and paths outside the folder.
The judge pack in `.scratch/billsplit-review/` has `base/` (the original project) and one folder per letter.
Each letter holds `repo/`, `reply.md`, `diff.patch`, and `actions.txt`.

Then spawn the judge with `task` on a different model family than the candidates.
Give it the rubric above and the pack path, and ask for a score per criterion with evidence, plus a ranking.
Read every candidate's reply and transcript yourself and compare with the judge.
Write `evals/results/outcome-<date>.md` with the variant and ref, the rubric, per-candidate notes, the judge's verdict, your synthesis, and a recommendation.
A run costs at most about $12 for the candidates on the default model.
