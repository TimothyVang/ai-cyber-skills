import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { splitEvenly, withTip } from '../src/split.js';

describe('splitEvenly', () => {
  it('splits an even total into equal shares', () => {
    assert.deepEqual(splitEvenly(90, 3), [30, 30, 30]);
  });

  it('gives one person the whole total', () => {
    assert.deepEqual(splitEvenly(42.5, 1), [42.5]);
  });

  it('rejects zero people', () => {
    assert.throws(() => splitEvenly(10, 0), RangeError);
  });
});

describe('withTip', () => {
  it('adds the tip percentage', () => {
    assert.equal(withTip(100, 18), 118);
  });

  it('rounds to cents', () => {
    assert.equal(withTip(84.5, 18), 99.71);
  });
});
