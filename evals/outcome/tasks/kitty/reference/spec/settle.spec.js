import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { settle } from '../src/settle.js';

describe('settle', () => {
  it('has each debtor pay the creditor', () => {
    assert.deepEqual(settle([['ana', 6000], ['ben', -3000], ['cy', -3000]]), [
      { from: 'ben', to: 'ana', cents: 3000 },
      { from: 'cy', to: 'ana', cents: 3000 },
    ]);
  });

  it('needs no payments when everyone is square', () => {
    assert.deepEqual(settle([['ana', 0], ['ben', 0]]), []);
  });

  it('squares everyone in at most n - 1 payments', () => {
    const rows = [['ana', 4500], ['ben', -1250], ['cy', -2001], ['dee', 751], ['eve', -2000]];
    const payments = settle(rows);
    assert.ok(payments.length <= rows.length - 1);
    const left = new Map(rows);
    for (const { from, to, cents } of payments) {
      assert.ok(cents > 0);
      left.set(from, left.get(from) + cents);
      left.set(to, left.get(to) - cents);
    }
    assert.deepEqual([...left.values()], [0, 0, 0, 0, 0]);
  });
});
