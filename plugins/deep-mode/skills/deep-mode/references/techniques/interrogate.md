# interrogate

**Use when:** "adversarial review", "challenge/stress-test this", "find blind spots". Demoted by the author: use only for a contested design or change you can't otherwise settle; prefer empirical and formal verification. Report findings; apply no fixes.

1. **Frame.** Scope = what the user names, else the branch diff from merge base through the working tree. State intent via **in-your-own-words** from the message, commits, PR body; `ask` if unclear.
2. **Fan out** adversaries per arena steps 2–4 (own worktree each, uncommitted changes copied in; mixed model families when available). Brief verbatim in spirit: *Break this change. Prove each finding with a run against the real code — failing test, repro script, or command output showing wrong behavior. For a design, run a prototype or probe the current tree. Keep repros in your worktree. Report title, exact command, printed output, output the intent requires. Omit anything not run: style, naming, structure, risks needing a future change. No findings is valid.*
3. **Verify** each by rerunning its command. Keep it only if the output shows the failure and the failure breaks the intent. Merge shared root causes. Skip arena's judge/pick/graft: keep every verified finding.

**Output:** **Intent** · **Findings** (command, output, how it breaks intent, which adversaries found it; or "no verified findings") · **Dropped** (per adversary: count and why).
