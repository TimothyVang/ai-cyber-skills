import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { balances } from '../src/balances.js';
import { parseSplit, splitEvenly } from '../src/split.js';

describe('splitEvenly', () => {
  it('hands leftover cents to the first people so shares add up', () => {
    assert.deepEqual(splitEvenly(10000, ['ana', 'ben', 'cy']), { ana: 3334, ben: 3333, cy: 3333 });
  });
});

describe('parseSplit', () => {
  it('reads exact amounts', () => {
    assert.deepEqual(parseSplit('ana=40,Ben=30,cy=20', 9000), { ana: 4000, ben: 3000, cy: 2000 });
  });

  it('accepts amounts that add up even when floats would not', () => {
    assert.deepEqual(parseSplit('ana=9.99,ben=10.00', 1999), { ana: 999, ben: 1000 });
  });

  it('refuses amounts that do not add up', () => {
    assert.throws(() => parseSplit('ana=40,ben=30,cy=10', 9000), /adds up to \$80\.00/);
  });

  it('reads percentages, including decimals', () => {
    assert.deepEqual(parseSplit('ana=37.5%,ben=37.5%,cy=25%', 145000), { ana: 54375, ben: 54375, cy: 36250 });
    assert.deepEqual(parseSplit('ana=28.6%,ben=35.7%,cy=35.7%', 30000), { ana: 8580, ben: 10710, cy: 10710 });
  });

  it('rounds percentage shares so they still add up to the total', () => {
    const shares = parseSplit('ana=33.33%,ben=33.33%,cy=33.34%', 2000);
    assert.equal(Object.values(shares).reduce((a, b) => a + b, 0), 2000);
    assert.deepEqual(shares, { ana: 667, ben: 666, cy: 667 });
  });

  it('refuses percentages that do not add up to 100', () => {
    assert.throws(() => parseSplit('ana=50%,ben=30%,cy=10%', 9000), /90%/);
  });

  it('refuses a mix of amounts and percentages, and a name given twice', () => {
    assert.throws(() => parseSplit('ana=50%,ben=45', 9000), /not both/);
    assert.throws(() => parseSplit('ana=45,Ana=45', 9000), /twice/);
  });
});

describe('balances with uneven splits', () => {
  it('add up to zero for a total that does not divide evenly', () => {
    const ledger = { expenses: [{ id: 1, description: 'Dinner', amount: 100, paidBy: 'ana', among: ['ana', 'ben', 'cy'] }] };
    const rows = balances(ledger);
    assert.deepEqual(rows, [['ana', 66.66], ['ben', -33.33], ['cy', -33.33]]);
  });

  it('use stored shares', () => {
    const ledger = {
      expenses: [{ id: 1, description: 'Dinner', amount: 90, paidBy: 'ana', among: ['ana', 'ben'], shares: { ana: 60, ben: 30 } }],
    };
    assert.deepEqual(balances(ledger), [['ana', 30], ['ben', -30]]);
  });
});
