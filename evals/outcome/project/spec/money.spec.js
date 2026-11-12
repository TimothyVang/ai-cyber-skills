import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { formatAmount, parseAmount } from '../src/money.js';

describe('parseAmount', () => {
  it('reads plain numbers', () => {
    assert.equal(parseAmount('12'), 12);
    assert.equal(parseAmount('12.5'), 12.5);
  });

  it('strips a dollar sign and thousands separators', () => {
    assert.equal(parseAmount('$1,234.50'), 1234.5);
  });

  it('rejects text that is not an amount', () => {
    assert.throws(() => parseAmount('abc'));
    assert.throws(() => parseAmount('1.234'));
  });
});

describe('formatAmount', () => {
  it('always shows two decimals', () => {
    assert.equal(formatAmount(3.5), '$3.50');
  });
});
