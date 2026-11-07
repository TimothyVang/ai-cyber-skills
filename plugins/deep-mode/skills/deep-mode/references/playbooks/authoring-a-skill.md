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
4. Validate: frontmatter has `name` and `description`; every referenced file exists; every cross-skill link resolves.
5. Structural skill (routing, gates, scripts) → write test cases; subjective skill → skip.
6. Repeatedly-hit workflow not captured anywhere → propose a new skill.
7. Run **Opening a PR** (`references/playbooks/opening-a-pr.md`) only if the user asked for git writes.

## Gates

- Validation (step 4) must pass before reporting done.
- A rule that a lint, type, or test could enforce goes there instead of prose.
- No git writes unless the user asked.

## Evidence

- Summary of the skill.
- Key design decisions.
- Validation notes: frontmatter check, referenced files, link resolution, test cases run or why skipped.
