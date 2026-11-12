# Outcome eval

Does installing deep-mode make an agent do a real coding task better?
This eval follows the Eval playbook (`plugins/deep-mode/skills/deep-mode/references/playbooks/eval.md`) step by step.

## Design

- **Variants under test.** A chosen deep-mode revision versus plain. `setup --compare-ref <commit>` adds a previous revision as a third arm under the same task, model and runtime settings.
- **With deep-mode.** Every skill under `plugins/deep-mode/skills/` at a chosen commit is copied into the candidate's `.omp/skills/`.
  `SKILL.md` and `/deep` point at the sibling skills (`create-verification-skill`, `software-architecture` and others), so all of them ship.
  The prompt starts with what `/deep` expands to (`plugins/deep-mode/commands/deep.md` at that commit), with the task's request as its argument.
- **Without.** The same project and the same request, nothing else.
- **Tasks.** Each task is a folder under `tasks/`. See Tasks below.
- **Candidates.** `--per-variant` per variant, assigned in seeded random order. A unique `--run-id` gives every run its own project directories, raw logs, key and judge pack. Existing candidate outputs are never overwritten by `run`.
  Each folder is its own `git init` repo with one commit, named from the project's `package.json` name and version.
  `.omp/` sits in `.git/info/exclude` in every folder, so `git status` looks the same in both variants.
- **Isolation.** Each candidate is one `omp -p --max-cost <cap>` process with its folder as the working directory.
- Both variants run with `--no-rules --no-context-files --no-extensions`, so the user's global context and containment hooks stay out.
- The deep-mode variants load the complete skills snapshot at their recorded commits; plain uses `--no-skills`.
- The model is explicit. The runner checks subscription OAuth metadata, scrubs credential-shaped environment variables and disables provider fallback and automatic model switching. Common helper roles use the same model; actual model IDs are retained in results.
- Each process gets its own contained temporary directory. This is process/config isolation, not an OS sandbox. Review the contamination report.
- The reported dollar-valued usage is a harness accounting estimate, not an API invoice. omp checks its cap between turns, so one turn can overshoot it.
- **Primary score.** The task's hidden checks, run at collect time against a copy of each candidate's final tree.
  Candidates never see them. The score is the number that pass.
- **Secondary score.** Two explicitly selected blinded judges score the rubric. Use a different family when authorized and available; disclose when both are the same family.
  Each runs as its own `omp -p` process in its own copy of the judge pack under `.scratch/`.
  So one judge's trial runs never reach the other, and no run data sits beside a judge's folder.
  `judge` reports both judges separately and how far they agree.
  It always writes each raw reply and `judges.json`, with a `parse_error` for a reply it could not read.
  `judge --reparse` reads the saved replies again without calling a model, for example after fixing a malformed one by hand.

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
  Balances are floats, so `$100` among three shows balances that add up to a cent over zero, and settling them leaves a cent behind.
  Summing split amounts or percentages as floats rejects valid input (`9.99 + 10.00` is not `19.99` in floating point).
  Percentage shares rounded one by one miss the total by a cent.
  A new expense shape must still work in `list`, in case-insensitive names, in who joins the tab, and with ledger files the old version saved.
  Its 19 hidden checks cover each of those, and each follows from the request or from what the project's README documents.
  `settle` is judged on whether everyone ends up even, not on what `balances` prints, so leaving `--among` as it was costs nothing.
  A rounded share counts as right when the shares add up to the total and each is less than `people - 1` cents from exact.
  The original passes 3. Those are the two refusals, because it rejects `--split` outright, and plain `--among`.
  Probes tried while building the task score as follows.
  The reference, a variant that keeps `balances` for `--among` exactly as before but settles in cents, and a variant that gives the leftover percentage cents to the last person all pass 19.
  A float-based quick patch passes 15.

## Gates

The Eval playbook's blinding gates hold here.

- Candidate folders are named like a user's project (`kitty-1`).
  No file name or prompt a candidate sees holds a gate word.
  The projects' suites live in `spec/*.spec.js` for that reason. The `npm test` script and the `node:test` import are standard Node and stay.
  Folder paths are another matter. On the machine that ran this, every candidate's absolute path runs through `deep-mode/.worktrees/eval-medium/`.
  Both variants share that path, so it tells a candidate nothing about which variant it is.
- Run data (prompts, event logs, sessions, the variant key, hidden check results) sits in `.scratch/<task>-runs/`, outside every candidate folder.
- Candidates are never told about each other.
- The judge pack omits `.git/`, `.scratch/`, `.worktrees/` and the supplied skill snapshot. Candidate-authored verification helpers remain under `.omp/skills/` so dependent tests still run. Folder paths become `<project>`.
  It drops every action line that reads a skill file.
  In replies and actions it removes "light panel", which names deep-mode's verifier, and replaces "deep-mode" and "playbook" with neutral words.
- Judges never see the hidden checks or their results.
- Helper agents a candidate starts write their own session files. `collect` reads those too, for cost, actions, and the outside-path scan.
- Candidates and judges can still read outside their folders.
  Candidate folders sit inside this repo's `.scratch/`, so `../../evals/outcome/tasks/` (hidden checks, reference, rubric), sibling candidates and `<task>-runs/` are a few `..` away.
  `collect` and `judge` resolve every path in each tool call against that call's working folder.
  That covers path arguments of file tools, edit targets, and every word of shell commands and code, following `cd` inside a command.
  A `cd` target is judged from where the `cd` starts, so `cd spec && ... && cd ..` stays clean.
  Inside a quoted string that holds code, such as `node -e "import('../src/a.js')"`, only absolute, home and temp paths count.
  So a quoted script that reads `../` is missed. A quoted path given on its own, as in `cat "../x"`, still counts.
  A `mktemp` without an explicit destination is flagged conservatively; check the recorded process environment, because this runner points `TMPDIR` into that candidate's own `.scratch/tmp`.
  A path that lands outside the process's own folder, by an absolute path, a home or temp variable, or `..` that climbs out, is listed.
  Any hit marks the run `contaminated` in `measurements.json` or `judges.json` and in the printed table.
  Read the hits. A regex that looks like a path can be a false alarm. `evals/outcome/test_run.py` holds the cases the scan must get right.
- Adjudicate flagged paths against the raw call. A path inside text being written, or a search pattern such as `/tmp`, is not itself a filesystem read. Keep the raw flag and record the reason separately instead of silently clearing it.
- The other residual risk is behavior. A deep-mode candidate's actions still show its worktree and verifier steps, which a judge may recognize.

## Rerun

```bash
python evals/outcome/run.py selftest --task kitty
python evals/outcome/run.py setup --task kitty --run-id delivery --ref HEAD --compare-ref <previous-commit> --per-variant 5
python evals/outcome/run.py run --task kitty --run-id delivery --max-cost 4 --model openai-codex/gpt-6-astra
python evals/outcome/run.py collect --task kitty --run-id delivery
python evals/outcome/run.py judge --task kitty --run-id delivery --judge-model openai-codex/gpt-6.1-terra:high --judge-model openai-codex/gpt-6-luna:high
```

`--task` defaults to `billsplit`. Model selection is now explicit; older commands need `--model` or `--judge-model` arguments.

Choose a fresh project-shaped `--run-id` for each repetition; omit `--compare-ref` for a two-arm run. Replace the model IDs with subscription models you are authorized to use, identically across candidate arms. `process_finished` records successful process exit with a reply, not feature correctness. Claim completed delivery only after the checked-out files pass the hidden behavior checks and the reply/transcript confirms the task finished.
Parallel runs share host and provider load. Report concurrency and failures, and do not promote timing differences as a speedup without an alternating, repeated measurement. These small fixtures are development evaluations, not a production review-quality or competitor benchmark.
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
