export function parseAmount(input) {
  const cleaned = String(input).trim().replace(/^\$/, '').replaceAll(',', '');
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) {
    throw new Error(`not an amount: ${input}`);
  }
  return Number(cleaned);
}

export function formatAmount(dollars) {
  return `$${dollars.toFixed(2)}`;
}
