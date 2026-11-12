#!/usr/bin/env node
import { parseArgs } from 'node:util';
import { balances, balancesInCents } from '../src/balances.js';
import { addExpense, ledgerPath, loadLedger, removeLast, saveLedger } from '../src/ledger.js';
import { parseAmount, toCents } from '../src/money.js';
import { formatBalances, formatExpense, formatHistory, formatPayments } from '../src/report.js';
import { settle } from '../src/settle.js';
import { parseSplit } from '../src/split.js';

const USAGE = `usage:
  kitty add <amount> <description> --by <name> [--among <name,name,...>]
  kitty add <amount> <description> --by <name> --split <name=amount,...|name=percent%,...>
  kitty list
  kitty balances
  kitty settle
  kitty undo
options:
  --file <path>   the ledger file (default: $KITTY_FILE, then ./kitty.json)`;

function main(argv) {
  const { values, positionals } = parseArgs({
    args: argv,
    allowPositionals: true,
    options: {
      by: { type: 'string', short: 'b' },
      among: { type: 'string', short: 'a' },
      split: { type: 'string', short: 's' },
      file: { type: 'string', short: 'f' },
      help: { type: 'boolean', short: 'h' },
    },
  });
  const [command, ...rest] = positionals;
  if (values.help || !command) {
    console.log(USAGE);
    return 0;
  }
  const path = ledgerPath(values.file);
  const ledger = loadLedger(path);

  switch (command) {
    case 'add': {
      if (rest.length < 2 || !values.by) {
        throw new Error('add needs an amount, a description and --by');
      }
      if (values.split !== undefined && values.among !== undefined) {
        throw new Error('use --among or --split, not both');
      }
      const amount = parseAmount(rest[0]);
      const expense = addExpense(ledger, {
        amount,
        description: rest.slice(1).join(' '),
        paidBy: values.by,
        among: values.among?.split(','),
        sharesInCents: values.split === undefined ? undefined : parseSplit(values.split, toCents(amount)),
      });
      saveLedger(path, ledger);
      console.log(`Added ${formatExpense(expense)}`);
      return 0;
    }
    case 'list':
      console.log(formatHistory(ledger));
      return 0;
    case 'balances':
      console.log(formatBalances(balances(ledger)));
      return 0;
    case 'settle':
      console.log(formatPayments(settle(balancesInCents(ledger))));
      return 0;
    case 'undo': {
      const expense = removeLast(ledger);
      saveLedger(path, ledger);
      console.log(`Removed ${formatExpense(expense)}`);
      return 0;
    }
    default:
      throw new Error(`unknown command: ${command}\n${USAGE}`);
  }
}

try {
  process.exitCode = main(process.argv.slice(2));
} catch (err) {
  console.error(`kitty: ${err.message}`);
  process.exitCode = 1;
}
