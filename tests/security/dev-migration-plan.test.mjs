import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildMigrationExecutionPlan, GATE_STATUS, MAX_HISTORY_AGE_MS } from './dev-migration-plan.mjs';
import { DEV_PROJECT_REF, REQUIRED_MIGRATIONS, verifyPreflight } from './dev-db-preflight.mjs';

const source = resolve(dirname(fileURLToPath(import.meta.url)), '../../supabase/migrations');
const sqlFile = resolve(dirname(fileURLToPath(import.meta.url)), '../../supabase/DEV_MIGRATION_READONLY.sql');
const now = new Date('2026-10-22T14:00:00.000Z');
const baseline = verifyPreflight().local.slice(0, 3);

function history(applied = baseline, captured_at = '2026-10-22T13:45:00.000Z', project_ref = DEV_PROJECT_REF) {
  return { project_ref, applied, captured_at };
}
function plan(h = history(), opts = {}) {
  return buildMigrationExecutionPlan({ remoteHistory: h, now, ...opts });
}
function copied(fn) {
  const tmp = mkdtempSync(resolve(tmpdir(), 'retailgrowthai-p-'));
  try { cpSync(source, tmp, { recursive: true }); fn(tmp); }
  finally { rmSync(tmp, { recursive: true, force: true }); }
}

test('fresh exact DEV baseline creates seven fingerprinted and explicitly unapproved ordered steps', () => {
  const result = plan();
  assert.equal(result.project_ref, DEV_PROJECT_REF);
  assert.equal(result.authorized_to_apply, false);
  assert.equal(result.gate, GATE_STATUS);
  assert.equal(result.pending.length, 7);
  assert.deepEqual(result.pending.map(item => item.file), REQUIRED_MIGRATIONS.slice(3));
  for (const [index, item] of result.pending.entries()) {
    assert.equal(item.step, index + 1);
    assert.match(item.sha256, /^[0-9a-f]{64}$/);
    assert.ok(item.bytes > 100);
  }
});
test('rejects old/future/missing capture, wrong project, remote drift or a partial rollout', () => {
  const cases = [
    history(baseline, new Date(now.getTime() - MAX_HISTORY_AGE_MS - 1).toISOString()),
    history(baseline, new Date(now.getTime() + 2 * 60 * 1000 + 1).toISOString()),
    history(baseline, null),
    history(baseline, 'not-a-date'),
    history(baseline, undefined, 'other-project'),
    history([...baseline.slice(0, 2), {version:'20261022100400', name:'p1_durable_planning'}]),
    history(verifyPreflight().local.slice(0, 4)),
  ];
  for (const bad of cases) assert.throws(() => plan(bad), /history|project|diverges|baseline|captured_at/);
});
test('refuses unreviewed extra migration and missing transaction boundary', () => {
  copied(dir => {
    writeFileSync(resolve(dir, '20261022230000_unreviewed.sql'), 'begin; select 1; commit;');
    assert.throws(() => plan(history(), { migrationDir: dir }), /unreviewed migration/);
  });
  copied(dir => {
    const path = resolve(dir, REQUIRED_MIGRATIONS[3]);
    writeFileSync(path, readFileSync(path, 'utf8').replace(/commit;\s*$/i, ''));
    assert.throws(() => plan(history(), { migrationDir: dir }), /BEGIN\/COMMIT/);
  });
});
test('manifest sha256 changes if reviewed SQL changes; no auto execution flag exists', () => {
  const original = plan();
  copied(dir => {
    const path = resolve(dir, REQUIRED_MIGRATIONS[3]);
    writeFileSync(path, readFileSync(path, 'utf8').replace('begin;', 'begin;\n-- reviewer-visible change'));
    const changed = plan(history(), { migrationDir: dir });
    assert.notEqual(changed.pending[0].sha256, original.pending[0].sha256);
    assert.equal(changed.authorized_to_apply, false);
  });
});
test('operator snapshot SQL is SELECT-only (no DDL/DML, psql commands or secret extraction)', () => {
  const sql = readFileSync(sqlFile, 'utf8').replace(/^\s*--[^\n]*$/gm, '').trim();
  const statements = sql.split(';').map(s => s.trim()).filter(Boolean);
  assert.ok(statements.length >= 4);
  for (const statement of statements) assert.match(statement, /^select\s/i);
  assert.doesNotMatch(sql, /\b(?:insert|update|delete|truncate|alter|drop|create|grant|revoke|copy|pg_read_file|dblink)\b/i);
});
