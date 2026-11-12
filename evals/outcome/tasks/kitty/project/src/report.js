import { formatAmount, formatBalance } from './money.js';

export function formatExpense(expense) {
  return `#${expense.id}  ${expense.description}  ${formatAmount(expense.amount)}  paid by ${expense.paidBy}, `
    + `split between ${expense.among.join(', ')}`;
}

export function formatHistory(ledger) {
  if (ledger.expenses.length === 0) {
    return 'No expenses yet.';
  }
  return ledger.expenses.map(formatExpense).join('\n');
}

export function formatBalances(rows) {
  if (rows.length === 0) {
    return 'No expenses yet.';
  }
  const width = Math.max(...rows.map(([name]) => name.length));
  return rows.map(([name, value]) => `${name.padEnd(width)}  ${formatBalance(value)}`).join('\n');
}
