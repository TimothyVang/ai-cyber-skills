Closes #

## What

<!-- What this PR changes, in two or three sentences. -->

## Why

<!-- The problem it solves for users or maintainers. -->

## Evidence

<!-- Prove it works on the real app, not just in tests. Paste the exact commands and their output, or screenshots. If a deep-mode agent did the work, paste its final report below. -->

```text
$ <command>
<output>
```

## Overlap check

<!-- Output of: python scripts/pr-overlap.py check --repo OWNER/REPO --files <your changed paths> --exclude-issue <issue N> --exclude-pr <this PR number> -->

```text
<output>
```

## Checklist

- [ ] One issue, one branch, one PR; `Closes #N` above.
- [ ] I claimed the issue, and this PR only changes the files the claim lists (or I updated the claim).
- [ ] Overlap check is clean, or I coordinated with the overlapping PR or claim (link it).
- [ ] Tests and checks from `CONTRIBUTING.md` pass locally.
- [ ] Evidence above shows the change on the real app.
- [ ] Followed the constraints in `docs/PROJECT_BRIEF.md`; no secrets or real user data in code, tests, or fixtures.
