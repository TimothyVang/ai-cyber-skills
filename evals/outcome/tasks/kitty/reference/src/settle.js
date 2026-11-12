// Payments that square everyone up: the biggest debtor pays the biggest creditor until nobody is owed anything.
// Every payment clears at least one person, so n people need at most n - 1 payments.
export function settle(rowsInCents) {
  const byOwed = (a, b) => b.cents - a.cents || a.name.localeCompare(b.name);
  const creditors = rowsInCents.filter(([, cents]) => cents > 0).map(([name, cents]) => ({ name, cents }));
  const debtors = rowsInCents.filter(([, cents]) => cents < 0).map(([name, cents]) => ({ name, cents: -cents }));
  const payments = [];
  while (creditors.length > 0 && debtors.length > 0) {
    creditors.sort(byOwed);
    debtors.sort(byOwed);
    const [to] = creditors;
    const [from] = debtors;
    const cents = Math.min(to.cents, from.cents);
    payments.push({ from: from.name, to: to.name, cents });
    to.cents -= cents;
    from.cents -= cents;
    if (to.cents === 0) creditors.shift();
    if (from.cents === 0) debtors.shift();
  }
  return payments;
}
