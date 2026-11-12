// Acceptance checks for the billsplit task. Candidates never see this file.
// Every split must add up to the printed total, with no two shares more than a cent apart.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { dirname, join, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const PROJECT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SPLITS = [['100', 3, 0], ['200', 3, 0], ['0.10', 3, 0], ['1', 7, 0], ['75', 3, 20], ['84.50', 3, 18],
  ['$1,250.00', 4, 0], ['10', 1, 0], ['90', 3, 0]];
const cents = (text) => Math.round(Number(text.replaceAll(',', '')) * 100);

for (const [amount, people, tip] of SPLITS) {
  test(`${amount} between ${people} with a ${tip}% tip adds up`, () => {
    const r = spawnSync(process.execPath, [join(PROJECT, 'bin', 'billsplit.js'), amount, '--people', String(people),
      '--tip', String(tip)], { cwd: PROJECT, encoding: 'utf8', timeout: 15000 });
    assert.equal(r.status, 0, r.stderr);
    const total = /Total:\s+\$([\d,]+\.\d\d)/.exec(r.stdout);
    assert.ok(total, `no total in:\n${r.stdout}`);
    const shares = [...r.stdout.matchAll(/Person \d+:\s+\$([\d,]+\.\d\d)/g)].map((m) => cents(m[1]));
    assert.equal(shares.length, people, r.stdout);
    assert.equal(shares.reduce((a, b) => a + b, 0), cents(total[1]), r.stdout);
    assert.ok(Math.max(...shares) - Math.min(...shares) <= 1, r.stdout);
  });
}
