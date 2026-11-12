export function parseAmount(input) {
  const cleaned = String(input).trim().replace(/^\$/, '').replaceAll(',', '');
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) {
    throw new Error(`not an amount: ${input}`);
  }
  return Number(cleaned);
}

export function formatAmount(dollars) {
  return `$${Math.abs(dollars).toFixed(2)}`;
}

// "+" means the tab owes you money, "-" means you owe the tab.
export function formatBalance(dollars) {
  const sign = dollars > 0 ? '+' : dollars < 0 ? '-' : '';
  return `${sign}${formatAmount(dollars)}`;
}
