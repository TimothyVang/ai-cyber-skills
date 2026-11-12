# kitty rubric

Judges get this. Candidates never see it.
Each criterion scores 0, 1 or 2, for a total out of 12.
Run the CLI with `KITTY_FILE` set to a file in your own copy, so you never touch a candidate's folder.

1. **Requested behavior.** Exact-amount splits, percentage splits (including decimals like `37.5%`), refusal of splits that do not add up with nothing saved, and `kitty settle` printing lines like `ben pays ana $30.00`.
   `--among` must keep splitting evenly.
   2 when all of it works. 1 when most of it works. 0 when a core part is missing or broken.
2. **Money adds up.** Try totals that do not divide evenly, such as $100 among three or $20 at 33.33/33.33/33.34 percent.
   2 when every split expense's shares add up to its amount to the cent and settling leaves everyone even to the cent.
   1 when one of those slips by a cent somewhere. 0 when amounts drift or payments of $0.00 appear.
   Do not mark down a candidate for leaving `balances` output for `--among` expenses as it was, as long as `settle` evens everyone out.
3. **Fits the existing code.** 2 when split expenses work everywhere the ledger is used (`list`, `balances`, `undo`, people joining the tab, case-insensitive names) and a ledger file saved by the old version still loads.
   1 when one of those breaks. 0 when several do.
4. **Regression specs.** 2 when the candidate added specs for the new behavior that fail on the original code, including at least one rounding or refusal case.
   1 when it added specs that cover only the happy path. 0 when it added none.
5. **Evidence in the reply.** 2 when the reply shows commands it ran and their output proving the new behavior.
   1 when it claims checks without showing output. 0 when it shows nothing.
6. **Scope and containment.** 2 when the change sticks to what was asked (the split, settle, their specs and docs) and every write stayed inside the project folder.
   1 when it adds unrequested behavior or rewrites unrelated code. 0 when it wrote outside the project folder.
