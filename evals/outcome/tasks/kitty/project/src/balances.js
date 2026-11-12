// What each person is owed (positive) or owes (negative), sorted by name.
export function balances(ledger) {
  const totals = new Map();
  const bump = (name, value) => totals.set(name, (totals.get(name) ?? 0) + value);
  for (const expense of ledger.expenses) {
    bump(expense.paidBy, expense.amount);
    const share = expense.amount / expense.among.length;
    for (const name of expense.among) {
      bump(name, -share);
    }
  }
  return [...totals].sort(([a], [b]) => a.localeCompare(b));
}
