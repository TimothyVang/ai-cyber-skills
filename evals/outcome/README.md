# Outcome eval

Does installing deep-mode make an agent do a real coding task better?
This eval follows the Eval playbook (`plugins/deep-mode/skills/deep-mode/references/playbooks/eval.md`) step by step.

## Design

- **Variant under test.** deep-mode installed versus not installed.
- **With deep-mode.** The skill from a chosen commit is copied into the candidate's `.omp/skills/deep-mode/`.
  The prompt starts with what `/deep` expands to (`plugins/deep-mode/commands/deep.md` at that commit), with the task's request as its argument.
- **Without.** The same project and the same request, nothing else.
- **Tasks.** Each task is a folder under `tasks/`. See Tasks below.
- **Candidates.** `--per-variant` per variant, assigned to folders `.scratch/<task>-1` and up in a seeded random order.
  Each folder is its own `git init` repo with one commit, named from the project's `package.json` name and version.
  `.omp/` sits in `.git/info/exclude` in every folder, so `git status` looks the same in both variants.
- **Isolation.** Each candidate is one `omp -p --max-cost <cap>` process with its folder as the working directory.
  Both variants run with `--no-rules --no-context-files --no-extensions`, so the user's global `AGENTS.md`, rules, and contain hook stay out.
  The deep-mode candidates run with `--skills deep-mode`, which loads the project copy.
  The others run with `--no-skills`, because deep-mode is also installed globally on the machine that ran this.
  The API keys are removed from the child's environment, so every run bills the subscription.
  omp checks the cost cap between turns, so one turn can overshoot it.
- **Primary score.** The task's hidden checks, run at collect time against a copy of each candidate's final tree.
  Candidates never see them. The score is the number that pass.
- **Secondary score.** Two blinded judges, `anthropic/claude-opus-5-5` and `openai-codex/gpt-6.1-terra`, score the task's rubric.
  Each runs as its own `omp -p` process in its own copy of the judge pack, so one judge's trial runs never reach the other.
  `judge` reports both judges separately and how far they agree.

## Tasks

A task folder holds five things.

- `project/` is what each candidate gets. It is a Node project with no dependencies.
- `prompt.txt` is the request in a user's words. It never names checks, skills, or the experiment.
- `rubric.md` is for the judges only. Each criterion is a numbered bold line scored 0, 1 or 2.
- `hidden/` holds `node:test` files. They drive the project's CLI only, so a broken module fails single checks instead of the whole file.
- `reference/` holds files that solve the task. `selftest` lays them over a copy of `project/` and expects every hidden check to pass.

Two tasks exist.

- **billsplit** is a size S bug fix and the task of the first run (`results/outcome-2026-11-12.md`).
  `billsplit` is a small CLI that splits a restaurant bill.
  `splitEvenly` rounds each share on its own, so `$100` three ways prints `$33.33` three times and loses a cent.
  The suite in `spec/` passes and never splits an uneven amount.
  Its 9 hidden checks are the CLI splits the first run measured. The original passes 4.
- **kitty** is a medium feature across several files.
  `kitty` is a CLI ledger of shared costs for a flat. The request asks for exact and percentage splits and a `settle` command.
  The traps are the parts a quick patch misses.
  Balances are floats, so `$100` among three already shows balances that add up to a cent over zero.
  Settling those balances leaves a cent behind or prints a `$0.00` payment.
  Summing split amounts or percentages as floats rejects valid input (`9.99 + 10.00` is not `19.99` in floating point).
  Percentage shares rounded one by one miss the total by a cent.
  A new expense shape must still work in `list`, in case-insensitive names, in who joins the tab, and with ledger files the old version saved.
  Its 18 hidden checks cover each of those. The original passes 3.
  Those are the two refusals, because it rejects `--split` outright, and plain `--among`.
  A float-based quick patch, tried while building the task, passes 10.

## Gates

The Eval playbook's blinding gates hold here.

- Candidate folders are named like a user's project (`kitty-1`).
  No folder, file name, or prompt a candidate sees holds a gate word.
  The projects' suites live in `spec/*.spec.js` for that reason. The `npm test` script and the `node:test` import are standard Node and stay.
- Run data (prompts, event logs, sessions, the variant key, hidden check results) sits in `.scratch/<task>-runs/`, outside every candidate folder.
- Candidates are never told about each other.
- The judge pack leaves `.git/`, `.omp/`, `.scratch/` and `.worktrees/` out of each copy and replaces folder paths with `<project>`.
  It drops every action line that reads a skill file.
  In replies and actions it removes "light panel", which names deep-mode's verifier, and replaces "deep-mode" and "playbook" with neutral words.
- Judges never see the hidden checks or their results.
- Helper agents a candidate starts write their own session files. `collect` reads those too, for cost, actions, and the outside-path scan.
- Two residual risks remain.
  Candidate and judge folders sit inside this repo's `.scratch/`, so a process that lists its parent folder can see its siblings and this repo, hidden checks included.
  `collect` and `judge` flag every absolute path outside the process's folder found in its tool calls, so a run can confirm none did.
  The second is behavior. A deep-mode candidate's actions still show its worktree and verifier steps, which a judge may recognize.

## Rerun

```bash
python evals/outcome/run.py selftest --task kitty                      # hidden checks fail on project/, pass on reference/
rm -rf .scratch/kitty-*                                                # only from a previous run
python evals/outcome/run.py setup --task kitty --ref HEAD --per-variant 3
python evals/outcome/run.py run --task kitty --max-cost 4 --model anthropic/claude-opus-5-5
python evals/outcome/run.py collect --task kitty                       # hidden checks, measurements, judge pack
python evals/outcome/run.py judge --task kitty                         # both judges, then the combined table
```

`--task` defaults to `billsplit`, so the first run's commands still work unchanged.
`judge --dry-run` writes the judge prompt to `.scratch/<task>-runs/judge-prompt.txt` without calling a model.

`collect` prints one line per candidate and writes `.scratch/<task>-runs/measurements.json`.
It holds cost, tool calls, wall time, files changed, diff lines, and the hidden checks passed with the names of those that failed.
It also holds the candidate's own suite on its tree and on the original source, and files read and paths outside the folder.
Its `git` entry lists unmerged branches, extra worktrees, and uncommitted changes. Only the checked-out tree is scored.
The judge pack in `.scratch/<task>-review/` has `base/` (the original project) and one folder per letter.
Each letter holds `repo/`, `reply.md`, `diff.patch`, and `actions.txt`.

`judge` writes `.scratch/<task>-runs/judges.json` with each judge's scores, notes, and cost.
Agreement has four numbers.
They are the share of letter and criterion cells where the judges match exactly, the share within one point, the mean gap between their totals, and the Spearman rank correlation of their totals.
Read every candidate's reply and transcript yourself and compare with both judges.
Write the results file with the variant and ref, a table per candidate, both judges' verdicts, your synthesis, and a recommendation.
The first billsplit run is `evals/results/outcome-2026-11-12.md`. The kitty run writes `evals/results/outcome-medium-<date>.md`.
