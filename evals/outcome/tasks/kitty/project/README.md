# kitty

Keep track of shared costs for a flat or a trip, and what everyone is owed.

## Use

```
node bin/kitty.js add 54.20 Groceries --by ana --among ana,ben,cy
node bin/kitty.js add 90 Dinner --by ben
node bin/kitty.js balances
```

```
ana  +$6.13
ben  +$41.93
cy   -$48.07
```

- `add <amount> <description> --by <name>` records a cost that one person paid.
  `--among` lists who shares it, split evenly.
  Without `--among`, it is split between everyone already on the tab, plus the payer.
- `list` prints every expense.
- `balances` prints what each person is owed (`+`) or owes (`-`). Someone who is square shows `$0.00`.
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
