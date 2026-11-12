#!/usr/bin/env node
import { parseArgs } from 'node:util';
import { balances } from '../src/balances.js';
import { addExpense, ledgerPath, loadLedger, removeLast, saveLedger } from '../src/ledger.js';
import { parseAmount } from '../src/money.js';
import { formatBalances, formatExpense, formatHistory } from '../src/report.js';

const USAGE = `usage:
  kitty add <amount> <description> --by <name> [--among <name,name,...>]
  kitty list
  kitty balances
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
      const expense = addExpense(ledger, {
        amount: parseAmount(rest[0]),
        description: rest.slice(1).join(' '),
        paidBy: values.by,
        among: values.among?.split(','),
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
