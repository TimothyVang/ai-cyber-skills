# Authoring a Skill

Use when: creating or modifying a skill (`SKILL.md` plus references). You own the skill's voice.

## Steps

1. Read the omp `writing-for-agents` skill (`skill://writing-for-agents`) before writing.
2. Before adding prose, check the ladder: can architecture/data structures prevent the mistake? Then a lint rule or test? Only then a skill/rule; human review last (`references/principles/encode-lessons-in-structure.md`).
3. Write or edit the skill:
   - When in doubt, delete. Keep only prose that changes a decision.
   - Tell it to do the thing; skip the reason unless the rule is confusing without one.
   - Match tone to scope.
   - Point at structural sources (types, READMEs, config) instead of restating them.
   - Delegate to other skills by path; don't restate them.
   - Route on the request's wording. A file in the repo is evidence for a route, never its trigger, or unrelated work in that repo gets captured.
   - One owner per trigger: search every installed skill's description and the router's rows for the new trigger words, and narrow the ones that lose.
4. Validate: `python <deep-mode skill dir>/scripts/check_skill.py <skill dir>` prints `ok` (frontmatter has `name` and `description`; every referenced file exists; every `skill://` link names an installed skill).
5. Structural skill (routing, gates, scripts) → write test cases; subjective skill → skip. A routing change is tested with fresh read-only `scout` agents given only the request: one per new route, plus one near-miss that must not match. Each answers with the skill, playbook, and the table row that decided it.
6. Repeatedly-hit workflow not captured anywhere → propose a new skill.
7. Run **Opening a PR** (`references/playbooks/opening-a-pr.md`).

## Gates

- Skill folder outside git → archive it (`tar -czf`) before the first edit, and name the archive in the report.
- Validation (step 4) must pass before reporting done.
- A rule that a lint, type, or test could enforce goes there instead of prose.

## Evidence

- Summary of the skill.
- Key design decisions.
- Validation notes: frontmatter check, referenced files, link resolution, test cases run or why skipped.
