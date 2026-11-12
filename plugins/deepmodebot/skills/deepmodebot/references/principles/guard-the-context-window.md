# guard-the-context-window

Group: delegation. When: context is filling — large outputs, long files, repeated reads, fan-out planning.
- **Rule.** Route bulk to subagents (`task`, `scout` for read-only); keep summaries in the main thread, not raw payloads. Overflow degrades reasoning, creates compression artifacts, halts progress.
- **Check.** Size phases and cap scope: limit files per phase, set turn budgets, account for mechanism costs.
