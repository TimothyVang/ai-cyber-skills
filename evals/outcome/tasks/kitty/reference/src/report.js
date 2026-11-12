import { formatAmount, formatBalance, formatCents } from './money.js';

export function formatExpense(expense) {
  const split = expense.shares
    ? Object.entries(expense.shares).map(([name, dollars]) => `${name} ${formatAmount(dollars)}`).join(', ')
    : expense.among.join(', ');
  return `#${expense.id}  ${expense.description}  ${formatAmount(expense.amount)}  paid by ${expense.paidBy}, `
    + `split between ${split}`;
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

export function formatPayments(payments) {
  if (payments.length === 0) {
    return 'Everyone is square.';
  }
  return payments.map(({ from, to, cents }) => `${from} pays ${to} ${formatCents(cents)}`).join('\n');
}
