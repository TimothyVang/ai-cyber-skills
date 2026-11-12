// Acceptance checks for the kitty task. Candidates never see this file.
// They drive the CLI only, so a broken module fails single checks instead of hiding the whole file.
// Every check follows from the request or from behavior the project's README already documents.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const PROJECT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const CLI = join(PROJECT, 'bin', 'kitty.js');
const WORK = join(PROJECT, '.acceptance-work');
let tabs = 0;

function tab() {
  const dir = join(WORK, `tab-${++tabs}`);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  const file = join(dir, 'kitty.json');
  const run = (...args) => {
    const r = spawnSync(process.execPath, [CLI, ...args], {
      cwd: dir, env: { ...process.env, KITTY_FILE: file }, encoding: 'utf8', timeout: 15000,
    });
    return { code: r.status, out: r.stdout ?? '', err: `${r.stderr ?? ''}${r.error ? r.error.message : ''}` };
  };
  const ok = (...args) => {
    const r = run(...args);
    assert.equal(r.code, 0, `kitty ${args.join(' ')} exited ${r.code}: ${r.err}`);
    return r.out;
  };
  return { file, run, ok };
}

const cents = (text) => Math.round(Number(text.replaceAll(',', '')) * 100);
const sum = (values) => values.reduce((a, b) => a + b, 0);

// `kitty balances` as { name: cents }. Fails when one person shows up twice.
function balances(t) {
  const rows = {};
  for (const line of t.ok('balances').split(/\r?\n/)) {
    const m = /^\s*(\S+)\s+([+-]?)\$([\d,]+\.\d{2})\s*$/.exec(line);
    if (!m) continue;
    const name = m[1].toLowerCase();
    assert.ok(!(name in rows), `${name} is listed twice in balances`);
    rows[name] = (m[2] === '-' ? -1 : 1) * cents(m[3]);
  }
  return rows;
}

function payments(t) {
  return t.ok('settle').split(/\r?\n/).flatMap((line) => {
    const m = /^\s*(\S+)\s+pays\s+(\S+)\s+\$([\d,]+\.\d{2})\s*$/i.exec(line);
    return m ? [{ from: m[1].toLowerCase(), to: m[2].toLowerCase(), cents: cents(m[3]) }] : [];
  });
}

// The exact position of each person, in fractional cents, and how far a cent-rounded split may move it.
// A split that rounds and still adds up to the total moves one share by less than (people - 1) cents.
function exactTab(expenses) {
  const tabRows = {};
  const bump = (name, exact, slack) => {
    tabRows[name] ??= { exact: 0, slack: 0 };
    tabRows[name].exact += exact;
    tabRows[name].slack += slack;
  };
  for (const { by, amount, shares } of expenses) {
    const names = Object.keys(shares);
    const slack = Object.values(shares).some((s) => !Number.isInteger(s)) ? names.length - 1 : 0;
    bump(by, amount, 0);
    for (const name of names) bump(name, -shares[name], slack);
  }
  return tabRows;
}
const even = (amount, names) => Object.fromEntries(names.map((name) => [name, amount / names.length]));
const percent = (amount, split) => Object.fromEntries(Object.entries(split).map(([name, p]) => [name, (amount * p) / 100]));

function near(actual, exact, slack, label) {
  assert.ok(Math.abs(actual - exact) < Math.max(slack, 0.5),
    `${label}: ${actual} cents is too far from the exact ${exact.toFixed(2)} cents`);
}

// After the payments everyone must be even: what each person receives minus what they pay
// matches their exact position within the rounding slack, with no empty, self, or extra payments.
function assertSettles(t, expenses) {
  const model = exactTab(expenses);
  const list = payments(t);
  const moved = Object.fromEntries(Object.keys(model).map((name) => [name, 0]));
  for (const p of list) {
    assert.ok(p.cents > 0, `empty payment ${p.from} -> ${p.to}`);
    assert.notEqual(p.from, p.to, `${p.from} pays themself`);
    assert.ok(p.from in moved && p.to in moved, `payment names someone not on the tab: ${p.from} -> ${p.to}`);
    moved[p.to] += p.cents;
    moved[p.from] -= p.cents;
  }
  for (const [name, { exact, slack }] of Object.entries(model)) {
    near(moved[name], exact, slack, `${name} after settling`);
  }
  const owing = Object.values(moved).filter((v) => v !== 0).length;
  assert.ok(list.length <= Math.max(owing - 1, 0), `${list.length} payments for ${owing} people who are not even`);
  return list;
}

test('exact amounts split a cost unevenly', () => {
  const t = tab();
  t.ok('add', '90', 'Dinner', '--by', 'ana', '--split', 'ana=40,ben=30,cy=20');
  assert.deepEqual(balances(t), { ana: 5000, ben: -3000, cy: -2000 });
});

test('the payer can be left out of an exact split', () => {
  const t = tab();
  t.ok('add', '60', 'Tickets', '--by', 'ana', '--split', 'ben=35,cy=25');
  assert.deepEqual(balances(t), { ana: 6000, ben: -3500, cy: -2500 });
});

test('exact amounts that add up are accepted even where floating point sums drift', () => {
  const t = tab();
  t.ok('add', '19.99', 'Lunch', '--by', 'ana', '--split', 'ana=9.99,ben=10.00');
  t.ok('add', '0.30', 'Gum', '--by', 'ben', '--split', 'ana=0.10,ben=0.20');
  assert.deepEqual(balances(t), { ana: 990, ben: -990 });
});

test('exact amounts that do not add up are refused and nothing is saved', () => {
  const t = tab();
  t.ok('add', '30', 'Pizza', '--by', 'ana', '--among', 'ana,ben');
  const before = readFileSync(t.file, 'utf8');
  const r = t.run('add', '90', 'Dinner', '--by', 'ana', '--split', 'ana=40,ben=30,cy=10');
  assert.notEqual(r.code, 0, 'a split adding up to $80 of $90 was accepted');
  assert.equal(readFileSync(t.file, 'utf8'), before);
});

test('percentages split a cost', () => {
  const t = tab();
  t.ok('add', '1450', 'Rent', '--by', 'ana', '--split', 'ana=37.5%,ben=37.5%,cy=25%');
  assert.deepEqual(balances(t), { ana: 90625, ben: -54375, cy: -36250 });
});

test('percentage shares are rounded so they add up to the total', () => {
  const t = tab();
  t.ok('add', '20', 'Pizza', '--by', 'dee', '--split', 'ana=33.33%,ben=33.33%,cy=33.34%');
  const rows = balances(t);
  assert.equal(rows.dee, 2000);
  assert.equal(sum(Object.values(rows)), 0, `the shares add up to ${2000 + sum(Object.values(rows))} cents, not 2000`);
  near(-rows.ana, 666.6, 2, 'ana');
  near(-rows.ben, 666.6, 2, 'ben');
  near(-rows.cy, 666.8, 2, 'cy');
});

test('percentages that add up to 100 are accepted even where floating point sums drift', () => {
  const t = tab();
  t.ok('add', '300', 'Rent', '--by', 'ana', '--split', 'ana=28.6%,ben=35.7%,cy=35.7%');
  assert.deepEqual(balances(t), { ana: 21420, ben: -10710, cy: -10710 });
});

test('percentages that do not add up to 100 are refused and nothing is saved', () => {
  const t = tab();
  t.ok('add', '30', 'Pizza', '--by', 'ana', '--among', 'ana,ben');
  const before = readFileSync(t.file, 'utf8');
  const r = t.run('add', '90', 'Dinner', '--by', 'ana', '--split', 'ana=50%,ben=30%,cy=10%');
  assert.notEqual(r.code, 0, 'percentages adding up to 90 were accepted');
  assert.equal(readFileSync(t.file, 'utf8'), before);
});

test('names in a split are case-insensitive like everywhere else', () => {
  const t = tab();
  t.ok('add', '90', 'Dinner', '--by', 'Ana', '--split', 'ana=40,BEN=30,Cy=20');
  assert.deepEqual(balances(t), { ana: 5000, ben: -3000, cy: -2000 });
});

test('people first named in a split join the tab', () => {
  const t = tab();
  t.ok('add', '30', 'Snacks', '--by', 'ana', '--split', 'ben=10,dee=20');
  t.ok('add', '60', 'Taxi', '--by', 'ana');
  assert.deepEqual(balances(t), { ana: 7000, ben: -3000, dee: -4000 });
});

test('list still works with split expenses on the tab', () => {
  const t = tab();
  t.ok('add', '90', 'Dinner', '--by', 'ana', '--among', 'ana,ben');
  t.ok('add', '1450', 'Rent', '--by', 'ben', '--split', 'ana=60%,ben=40%');
  const out = t.ok('list');
  assert.match(out, /Dinner/);
  assert.match(out, /Rent/);
});

test('--among still splits evenly', () => {
  const t = tab();
  t.ok('add', '90', 'Dinner', '--by', 'ana', '--among', 'ana,ben,cy');
  t.ok('add', '30', 'Taxi', '--by', 'ben', '--among', 'ana,ben');
  assert.deepEqual(balances(t), { ana: 4500, ben: -1500, cy: -3000 });
});

test('a ledger saved by the current version still works', () => {
  const t = tab();
  writeFileSync(t.file, `${JSON.stringify({
    expenses: [
      { id: 1, description: 'Groceries', amount: 54.2, paidBy: 'ana', among: ['ana', 'ben', 'cy'] },
      { id: 2, description: 'Dinner', amount: 90, paidBy: 'ben', among: ['ana', 'ben', 'cy'] },
    ],
  }, null, 2)}\n`);
  const expenses = [
    { by: 'ana', amount: 5420, shares: even(5420, ['ana', 'ben', 'cy']) },
    { by: 'ben', amount: 9000, shares: even(9000, ['ana', 'ben', 'cy']) },
  ];
  const rows = balances(t);
  for (const [name, { exact, slack }] of Object.entries(exactTab(expenses))) {
    near(rows[name], exact, slack, name);
  }
  assertSettles(t, expenses);
  t.ok('add', '12', 'Wine', '--by', 'cy', '--split', 'ana=6,cy=6');
  assert.match(t.ok('list'), /Groceries[\s\S]*Dinner[\s\S]*Wine/);
});

test('settle says who pays whom and changes nothing', () => {
  const t = tab();
  t.ok('add', '90', 'Dinner', '--by', 'ana', '--among', 'ana,ben,cy');
  const before = readFileSync(t.file, 'utf8');
  const list = payments(t).map((p) => `${p.from} pays ${p.to} ${p.cents}`).sort();
  assert.deepEqual(list, ['ben pays ana 3000', 'cy pays ana 3000']);
  assert.equal(readFileSync(t.file, 'utf8'), before);
});

test('settle evens out a total that does not divide evenly', () => {
  const t = tab();
  t.ok('add', '100', 'Dinner', '--by', 'ana', '--among', 'ana,ben,cy');
  const list = assertSettles(t, [{ by: 'ana', amount: 10000, shares: even(10000, ['ana', 'ben', 'cy']) }]);
  assert.equal(list.length, 2);
});

test('settle evens out a rounded percentage split', () => {
  const t = tab();
  t.ok('add', '20', 'Pizza', '--by', 'dee', '--split', 'ana=33.33%,ben=33.33%,cy=33.34%');
  assertSettles(t, [{ by: 'dee', amount: 2000, shares: percent(2000, { ana: 33.33, ben: 33.33, cy: 33.34 }) }]);
});

test('settle evens out a busy tab in few payments', () => {
  const t = tab();
  const everyone = ['ana', 'ben', 'cy', 'dee', 'eve'];
  t.ok('add', '54.20', 'Groceries', '--by', 'ana', '--among', everyone.join(','));
  t.ok('add', '1450', 'Rent', '--by', 'ben', '--split', 'ana=12.5%,ben=27.5%,cy=20%,dee=20%,eve=20%');
  t.ok('add', '19.99', 'Wine', '--by', 'cy', '--split', 'dee=9.99,eve=10.00');
  t.ok('add', '100', 'Taxi', '--by', 'dee', '--among', 'ana,ben,cy');
  t.ok('add', '33.33', 'Snacks', '--by', 'eve');
  assertSettles(t, [
    { by: 'ana', amount: 5420, shares: even(5420, everyone) },
    { by: 'ben', amount: 145000, shares: percent(145000, { ana: 12.5, ben: 27.5, cy: 20, dee: 20, eve: 20 }) },
    { by: 'cy', amount: 1999, shares: { dee: 999, eve: 1000 } },
    { by: 'dee', amount: 10000, shares: even(10000, ['ana', 'ben', 'cy']) },
    { by: 'eve', amount: 3333, shares: even(3333, everyone) },
  ]);
});

test('settle on a tab that is already even prints no payments', () => {
  const t = tab();
  for (const payer of ['ana', 'ben', 'cy']) {
    t.ok('add', '0.30', 'Coffee', '--by', payer, '--among', 'ana,ben,cy');
  }
  assert.deepEqual(payments(t), []);
});

test('after everyone pays what settle says, nothing is left to settle', () => {
  const t = tab();
  t.ok('add', '100', 'Dinner', '--by', 'ana', '--among', 'ana,ben,cy');
  t.ok('add', '54.20', 'Groceries', '--by', 'ben', '--among', 'ana,ben,cy,dee');
  t.ok('add', '20', 'Pizza', '--by', 'dee', '--split', 'ana=33.33%,ben=33.33%,cy=33.34%');
  const list = payments(t);
  assert.ok(list.length > 0, 'settle printed no payments for an uneven tab');
  // The way a user records paying someone back: an expense the payer covers for the one they owe.
  for (const p of list) {
    t.ok('add', (p.cents / 100).toFixed(2), 'Payback', '--by', p.from, '--among', p.to);
  }
  assert.deepEqual(payments(t), []);
});
