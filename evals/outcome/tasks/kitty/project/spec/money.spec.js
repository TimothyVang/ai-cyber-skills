import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { formatAmount, formatBalance, parseAmount } from '../src/money.js';

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
    assert.throws(() => parseAmount('-5'));
  });
});

describe('formatBalance', () => {
  it('marks money owed to you with a plus', () => {
    assert.equal(formatBalance(12.5), '+$12.50');
  });

  it('marks money you owe with a minus', () => {
    assert.equal(formatBalance(-3), '-$3.00');
  });

  it('shows zero without a sign', () => {
    assert.equal(formatBalance(0), '$0.00');
  });

  it('formats plain amounts with two decimals', () => {
    assert.equal(formatAmount(7), '$7.00');
  });
});
