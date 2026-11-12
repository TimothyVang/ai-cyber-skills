# Evals

Two evals check whether the deep-mode skill does what it claims.
They live at the repo root, not in the plugin, so installs never ship them.
Every run writes its results to `evals/results/`, and those files are committed.
A later change to the skill reruns the same eval, and the new file sits next to the old one for comparison.

## Routing

Measures whether a model that reads `SKILL.md` picks the right route and size for a request.
The cases are in `routing/cases.json`.
Each one has a realistic request, the expected route, and the expected size.
A route is a playbook file name (`bug-fix`), a technique (`pr-review`), or a sibling skill (`contribute`).
A size is `S`, `M`, `L`, or `none` for read-only work.
A case may set its own `context` line in place of the default one at the top of the file.

`scripts/eval_routing.py` runs one headless `omp -p` per case from an empty folder under `.scratch/routing-runs/`.
Tools, skills, rules, context files and extensions are off, so the answer comes from the skill text alone.
It strips `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` and `CODEX_API_KEY` from the child, so the run stays on the subscription.
It runs 4 cases at a time and scores an exact route match and an exact size match.

```bash
python scripts/eval_routing.py --dry-run            # print every prompt, no model calls
python scripts/eval_routing.py --only typo-fix      # one case; results go to .scratch/routing-runs/
python scripts/eval_routing.py                      # all cases; writes evals/results/routing-<date>.json
python scripts/eval_routing.py path/to/SKILL.md --model <id> --max-cost 0.5
```

The results file holds every case, the raw answer, both scores, the model, the cost, and the SHA-256 of the skill file.
A case costs about $0.15 on the default model.
A miss is a finding about the skill or about the case.
Read the case's `note` before changing either.

## Outcome

Measures whether installing deep-mode changes how well an agent fixes a real bug.
It follows the Eval playbook (`plugins/deep-mode/skills/deep-mode/references/playbooks/eval.md`) and its blinding gates.
Design, rubric, and how to rerun are in `outcome/README.md`.
Each run writes `results/outcome-<date>.md` with notes per candidate, the judge's verdict, and a recommendation.
