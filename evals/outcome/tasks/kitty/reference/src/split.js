import { normalizeName } from './ledger.js';
import { formatCents, parseAmount, toCents } from './money.js';

// An even split in cents. The first people in the list take the leftover cents.
export function splitEvenly(totalCents, names) {
  const base = Math.floor(totalCents / names.length);
  const extra = totalCents - base * names.length;
  return Object.fromEntries(names.map((name, i) => [name, base + (i < extra ? 1 : 0)]));
}

// "ana=40,ben=30" (amounts) or "ana=50%,ben=50%" (percentages) to { name: cents } adding up to totalCents.
export function parseSplit(text, totalCents) {
  const parts = String(text).split(',').map((part) => part.trim()).filter(Boolean);
  if (parts.length === 0) {
    throw new Error('--split needs name=amount or name=percent% pairs');
  }
  const entries = parts.map((part) => {
    const match = /^([^=]+)=(.+)$/.exec(part);
    if (!match) {
      throw new Error(`not a split entry: ${part}`);
    }
    const value = match[2].trim();
    return value.endsWith('%')
      ? { name: normalizeName(match[1]), basisPoints: parsePercent(value.slice(0, -1)) }
      : { name: normalizeName(match[1]), cents: toCents(parseAmount(value)) };
  });
  const names = entries.map((entry) => entry.name);
  const twice = names.find((name, i) => names.indexOf(name) !== i);
  if (twice) {
    throw new Error(`${twice} is in the split twice`);
  }
  const percents = entries.filter((entry) => 'basisPoints' in entry).length;
  if (percents > 0 && percents < entries.length) {
    throw new Error('use all amounts or all percentages in --split, not both');
  }
  return percents > 0 ? byPercent(entries, totalCents) : byAmount(entries, totalCents);
}

// Percentages are held in hundredths of a percent, so 37.5% is 3750 and the total must be exactly 10000.
function parsePercent(value) {
  if (!/^\d+(\.\d{1,2})?$/.test(value)) {
    throw new Error(`not a percentage: ${value}%`);
  }
  return Math.round(Number(value) * 100);
}

function byAmount(entries, totalCents) {
  const sum = entries.reduce((total, entry) => total + entry.cents, 0);
  if (sum !== totalCents) {
    throw new Error(`the split adds up to ${formatCents(sum)}, not ${formatCents(totalCents)}`);
  }
  return Object.fromEntries(entries.map((entry) => [entry.name, entry.cents]));
}

// Each person gets the floor of their exact share; the leftover cents go to the largest remainders.
function byPercent(entries, totalCents) {
  const sum = entries.reduce((total, entry) => total + entry.basisPoints, 0);
  if (sum !== 10000) {
    throw new Error(`the percentages add up to ${sum / 100}%, not 100%`);
  }
  const shares = entries.map((entry, order) => ({
    name: entry.name,
    order,
    cents: Math.floor((totalCents * entry.basisPoints) / 10000),
    remainder: (totalCents * entry.basisPoints) % 10000,
  }));
  const left = totalCents - shares.reduce((total, share) => total + share.cents, 0);
  [...shares].sort((a, b) => b.remainder - a.remainder || a.order - b.order)
    .slice(0, left)
    .forEach((share) => { share.cents += 1; });
  return Object.fromEntries(shares.map((share) => [share.name, share.cents]));
}
