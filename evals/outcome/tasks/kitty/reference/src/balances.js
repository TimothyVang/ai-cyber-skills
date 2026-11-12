import { toCents } from './money.js';
import { splitEvenly } from './split.js';

// Each person's share of one expense, in cents.
export function sharesInCents(expense) {
  if (expense.shares) {
    return Object.fromEntries(Object.entries(expense.shares).map(([name, dollars]) => [name, toCents(dollars)]));
  }
  return splitEvenly(toCents(expense.amount), expense.among);
}

// What each person is owed (positive) or owes (negative) in cents, sorted by name. The values add up to zero.
export function balancesInCents(ledger) {
  const totals = new Map();
  const bump = (name, cents) => totals.set(name, (totals.get(name) ?? 0) + cents);
  for (const expense of ledger.expenses) {
    bump(expense.paidBy, toCents(expense.amount));
    for (const [name, cents] of Object.entries(sharesInCents(expense))) {
      bump(name, -cents);
    }
  }
  return [...totals].sort(([a], [b]) => a.localeCompare(b));
}

// The same balances in dollars.
export function balances(ledger) {
  return balancesInCents(ledger).map(([name, cents]) => [name, cents / 100]);
}
