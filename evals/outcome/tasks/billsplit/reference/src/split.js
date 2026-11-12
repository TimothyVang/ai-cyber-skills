export function withTip(subtotal, tipPercent = 0) {
  return Math.round(subtotal * (100 + tipPercent)) / 100;
}

// Work in whole cents: everyone gets the floor share and the first people take the leftover cents.
export function splitEvenly(total, people) {
  if (!Number.isInteger(people) || people < 1) {
    throw new RangeError('people must be a whole number of at least 1');
  }
  const cents = Math.round(total * 100);
  const base = Math.floor(cents / people);
  const extra = cents - base * people;
  return Array.from({ length: people }, (_, i) => (base + (i < extra ? 1 : 0)) / 100);
}
