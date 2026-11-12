# kitty

Keep track of shared costs for a flat or a trip, and what everyone is owed.

## Use

```
node bin/kitty.js add 54.20 Groceries --by ana --among ana,ben,cy
node bin/kitty.js add 90 Dinner --by ben
node bin/kitty.js balances
node bin/kitty.js settle
```

```
ana  +$6.13
ben  +$41.93
cy   -$48.06
```

```
cy pays ben $41.93
cy pays ana $6.13
```

- `add <amount> <description> --by <name>` records a cost that one person paid.
  `--among` lists who shares it, split evenly. Leftover cents go to the first people listed.
  Without `--among` or `--split`, it is split between everyone already on the tab, plus the payer.
- `--split` splits a cost unevenly, by exact amounts (`--split ana=40,ben=30,cy=20`) or by percentages (`--split ana=37.5%,ben=37.5%,cy=25%`).
  The amounts must add up to the total and the percentages to 100, or nothing is saved.
  Percentage shares are rounded to cents so they still add up to the total.
- `list` prints every expense.
- `balances` prints what each person is owed (`+`) or owes (`-`). Someone who is square shows `$0.00`.
- `settle` prints who pays whom so everyone ends up square, one payment per line. It changes nothing.
- `undo` removes the last expense.

Names are case-insensitive, so `Ana` and `ana` are the same person.
The amount may carry a dollar sign and thousands separators (`$1,250.00`).

The ledger is a JSON file.
It is `./kitty.json` unless `--file` or the `KITTY_FILE` environment variable names another.

## Develop

Needs Node 20 or later and no dependencies.

```
npm test
```
