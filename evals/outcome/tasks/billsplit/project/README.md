# billsplit

Split a restaurant bill between friends, tip included.

## Use

```
node bin/billsplit.js 75 --people 3 --tip 20
```

```
Total:    $90.00
Person 1: $30.00
Person 2: $30.00
Person 3: $30.00
```

`--people` defaults to 2 and `--tip` (a percentage) to 0.
The amount may carry a dollar sign and thousands separators (`$1,250.00`).

## Develop

Needs Node 20 or later and no dependencies.

```
npm test
```
