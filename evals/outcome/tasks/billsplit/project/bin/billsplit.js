#!/usr/bin/env node
import { parseArgs } from 'node:util';
import { formatAmount, parseAmount } from '../src/money.js';
import { splitEvenly, withTip } from '../src/split.js';

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    people: { type: 'string', short: 'p', default: '2' },
    tip: { type: 'string', short: 't', default: '0' },
  },
});

if (positionals.length !== 1) {
  console.error('usage: billsplit <amount> [--people N] [--tip PERCENT]');
  process.exit(2);
}

try {
  const total = withTip(parseAmount(positionals[0]), Number(values.tip));
  const shares = splitEvenly(total, Number(values.people));
  console.log(`Total:    ${formatAmount(total)}`);
  shares.forEach((share, i) => console.log(`Person ${i + 1}: ${formatAmount(share)}`));
} catch (err) {
  console.error(`billsplit: ${err.message}`);
  process.exit(1);
}
