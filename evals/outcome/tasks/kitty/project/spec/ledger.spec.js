import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { addExpense, normalizeName, people, removeLast } from '../src/ledger.js';

describe('normalizeName', () => {
  it('ignores case and spaces', () => {
    assert.equal(normalizeName(' Ana '), 'ana');
  });

  it('rejects empty names', () => {
    assert.throws(() => normalizeName(''));
  });
});

describe('addExpense', () => {
  it('records who paid and who shares it', () => {
    const ledger = { expenses: [] };
    const expense = addExpense(ledger, { amount: 30, description: 'Pizza', paidBy: 'Ana', among: ['ana', 'Ben'] });
    assert.deepEqual(expense, { id: 1, description: 'Pizza', amount: 30, paidBy: 'ana', among: ['ana', 'ben'] });
  });

  it('splits between everyone on the tab when --among is left out', () => {
    const ledger = { expenses: [] };
    addExpense(ledger, { amount: 30, description: 'Pizza', paidBy: 'ana', among: ['ana', 'ben'] });
    const expense = addExpense(ledger, { amount: 12, description: 'Wine', paidBy: 'cy' });
    assert.deepEqual(expense.among, ['ana', 'ben', 'cy']);
    assert.deepEqual(people(ledger), ['ana', 'ben', 'cy']);
  });

  it('numbers expenses after the highest id', () => {
    const ledger = { expenses: [] };
    addExpense(ledger, { amount: 1, description: 'a', paidBy: 'ana' });
    addExpense(ledger, { amount: 2, description: 'b', paidBy: 'ana' });
    removeLast(ledger);
    assert.equal(addExpense(ledger, { amount: 3, description: 'c', paidBy: 'ana' }).id, 2);
  });
});

describe('removeLast', () => {
  it('refuses an empty ledger', () => {
    assert.throws(() => removeLast({ expenses: [] }), /nothing to undo/);
  });
});
