# Contributing

Anyone can improve these skills, starting with the Ai Cyber community. Changes land through pull requests.

## Flow

1. Branch from `main`.
2. Edit. Each plugin lives in `plugins/<name>/`; skills in `plugins/<name>/skills/<skill>/SKILL.md`.
3. Run `python scripts/check.py`. It must print `OK`. There is no CI; this local run is the gate.
4. Open a PR. Say what agent behavior you saw, what you changed, and how you tested it, including the check output.
5. A maintainer reviews and merges.

## What the check enforces

- Every `SKILL.md` has `name` and `description` frontmatter, and `name` matches its folder.
- Every `references/...md` link resolves to a real file. No `#anchor` links (omp can't read them).
- No line longer than 760 bytes (omp's `read` cuts long lines).
- Marketplace and plugin manifests, and `plugins/*/hooks/hooks.json`, are valid JSON and point at real folders.

## Testing a behavior change

A wording change can change what agents do. Before a PR that changes a playbook or technique, run the change on a throwaway repo with a small planted bug:

```bash
omp -p "/deep <task that exercises your change>"
claude -p "/deep-mode:deep <task>" --plugin-dir plugins/deep-mode
codex exec "\$deep-mode:deep-mode <task>"   # after `codex plugin marketplace add <this checkout>`
```

Report what the agent did before and after in the PR. For bigger changes, follow the Eval playbook (`plugins/deep-mode/skills/deep-mode/references/playbooks/eval.md`).

## Style for skill text

- Short declarative sentences. One rule per line.
- Prefer a lint, test, or script over more prose (see the `encode-lessons-in-structure` principle).
- Git and forge actions follow the Autonomy section of `plugins/deep-mode/skills/deep-mode/SKILL.md`: agents commit, push, open PRs, and merge on a panel pass, and stop only at its hard stops. A skill that needs a new hard stop adds it there, not in its own text.
