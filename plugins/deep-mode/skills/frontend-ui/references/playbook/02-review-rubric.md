## 2. Review rubric
Weighted design-first, because craft and functionality already come out fine by default. [anthropic harness]

| Criterion | Weight | Fails when |
| --- | --- | --- |
| Design quality | High | Parts don't add up to one mood or identity |
| Originality | High | Template layouts, unmodified library defaults, AI tells (§3) |
| Craft | Normal | Broken type hierarchy, inconsistent spacing, contrast below WCAG AA |
| Functionality | Normal | The primary action isn't obvious; the task needs guessing |
| Delegation (agent surfaces) | High | The user can't leave and come back, see each task's status, intervene, or take over [youtube/RGiXcVxSD3s] |

Originality check: if someone would believe AI made the change, it fails. [youtube/v42opQpCy60]

Report findings by severity. Lead with the problem and its user impact, then give the location, how it was verified, and the rule; the smallest fix is optional. [vercel; youtube/xOO8Wt_i72s]

| Level | Meaning |
| --- | --- |
| P0 | Blocks the task or causes severe accessibility failure |
| P1 | Likely task failure or missing state |
| P2 | Friction |
| P3 | Polish |
