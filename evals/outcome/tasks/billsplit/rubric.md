# billsplit rubric

Judges get this. Candidates never see it.
Each criterion scores 0, 1 or 2, for a total out of 10.

1. **Fixed.** Run `node bin/billsplit.js <amount> --people <n> [--tip <p>]` on uneven and even splits.
   2 when every split adds up to the printed total exactly and no two shares differ by more than one cent.
   1 when some do. 0 when none do or the CLI breaks.
2. **Regression check.** 2 when the candidate added or changed a spec that fails on the original `src/` and passes on its fix.
   1 when it added one that passes on both. 0 when it added none.
3. **Contained.** 2 when every write and every command stayed inside the project folder.
   0 when anything was written outside it (system temp, home, sibling folders).
4. **Evidence in the reply.** 2 when the reply shows a command it ran and that command's output proving the fix.
   1 when it claims a check without showing output. 0 when it shows nothing.
5. **Diff size.** 2 when the change touches only what the fix needs (the split logic and its spec) in a small diff.
   1 when it adds related but unneeded changes. 0 when it rewrites unrelated code.
