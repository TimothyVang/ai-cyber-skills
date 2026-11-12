export function parseAmount(input) {
  const cleaned = String(input).trim().replace(/^\$/, '').replaceAll(',', '');
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) {
    throw new Error(`not an amount: ${input}`);
  }
  return Number(cleaned);
}

// Money math happens in whole cents, so shares always add up to the total.
export function toCents(dollars) {
  return Math.round(dollars * 100);
}

export function formatAmount(dollars) {
  return `$${Math.abs(dollars).toFixed(2)}`;
}

export function formatCents(cents) {
  return formatAmount(cents / 100);
}

// "+" means the tab owes you money, "-" means you owe the tab.
export function formatBalance(dollars) {
  const sign = dollars > 0 ? '+' : dollars < 0 ? '-' : '';
  return `${sign}${formatAmount(dollars)}`;
}
