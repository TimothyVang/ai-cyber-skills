export function withTip(subtotal, tipPercent = 0) {
  return Math.round(subtotal * (100 + tipPercent)) / 100;
}

export function splitEvenly(total, people) {
  if (!Number.isInteger(people) || people < 1) {
    throw new RangeError('people must be a whole number of at least 1');
  }
  const share = Math.round((total / people) * 100) / 100;
  return Array(people).fill(share);
}
