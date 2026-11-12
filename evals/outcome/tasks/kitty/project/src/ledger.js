import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

export function ledgerPath(file) {
  return resolve(file ?? process.env.KITTY_FILE ?? 'kitty.json');
}

export function loadLedger(path) {
  if (!existsSync(path)) {
    return { expenses: [] };
  }
  return JSON.parse(readFileSync(path, 'utf8'));
}

export function saveLedger(path, ledger) {
  writeFileSync(path, `${JSON.stringify(ledger, null, 2)}\n`);
}

// Names are case-insensitive: "Ana" and "ana" are the same person.
export function normalizeName(name) {
  const clean = String(name).trim().toLowerCase();
  if (!/^[a-z][a-z0-9_-]*$/.test(clean)) {
    throw new Error(`not a name: ${name}`);
  }
  return clean;
}

export function people(ledger) {
  const names = new Set();
  for (const expense of ledger.expenses) {
    names.add(expense.paidBy);
    for (const name of expense.among) {
      names.add(name);
    }
  }
  return [...names].sort();
}

export function addExpense(ledger, { amount, description, paidBy, among }) {
  const payer = normalizeName(paidBy);
  const group = among && among.length > 0 ? among.map(normalizeName) : [...people(ledger), payer];
  const expense = {
    id: ledger.expenses.reduce((max, e) => Math.max(max, e.id), 0) + 1,
    description,
    amount,
    paidBy: payer,
    among: [...new Set(group)],
  };
  ledger.expenses.push(expense);
  return expense;
}

export function removeLast(ledger) {
  if (ledger.expenses.length === 0) {
    throw new Error('nothing to undo');
  }
  return ledger.expenses.pop();
}
