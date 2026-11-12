import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { balances } from '../src/balances.js';

describe('balances', () => {
  it('credits the payer and charges everyone their share', () => {
    const ledger = { expenses: [{ id: 1, description: 'Dinner', amount: 90, paidBy: 'ana', among: ['ana', 'ben', 'cy'] }] };
    assert.deepEqual(balances(ledger), [['ana', 60], ['ben', -30], ['cy', -30]]);
  });

  it('nets out several expenses', () => {
    const ledger = {
      expenses: [
        { id: 1, description: 'Dinner', amount: 90, paidBy: 'ana', among: ['ana', 'ben', 'cy'] },
        { id: 2, description: 'Taxi', amount: 30, paidBy: 'ben', among: ['ana', 'ben', 'cy'] },
      ],
    };
    assert.deepEqual(balances(ledger), [['ana', 50], ['ben', -10], ['cy', -40]]);
  });

  it('lets someone pay for others without a share', () => {
    const ledger = { expenses: [{ id: 1, description: 'Tickets', amount: 50, paidBy: 'cy', among: ['ana', 'ben'] }] };
    assert.deepEqual(balances(ledger), [['ana', -25], ['ben', -25], ['cy', 50]]);
  });
});
