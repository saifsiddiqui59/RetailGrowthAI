import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, rmSync, renameSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { DEV_PROJECT_REF, REQUIRED_MIGRATIONS, verifyPreflight } from './dev-db-preflight.mjs';

const sourceMigrations = resolve(import.meta.dirname ?? resolve('.'), '../../supabase/migrations');
const known = verifyPreflight();

function history(entries) {
  return { project_ref: DEV_PROJECT_REF, applied: entries };
}
function temporaryMigrationCopy(run) {
  const dir = mkdtempSync(resolve(tmpdir(), 'retailgrowthai-dev-db-'));
  try {
    cpSync(sourceMigrations, dir, { recursive: true, force: true });
    run(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}
test('all ten canonical migrations exist with ordered unique timestamps and security markers', () => {
  assert.deepEqual(known.local.slice(0, REQUIRED_MIGRATIONS.length).map(x => x.file), REQUIRED_MIGRATIONS);
  assert.equal(known.pending, null);
});
test('read-only remote DEV snapshot identifies exact prefix and pending ordered migrations', () => {
  const result = verifyPreflight({ remoteHistory: history(known.local.slice(0, 3)) });
  assert.equal(result.appliedCount, 3);
  assert.equal(result.pending.length, known.local.length - 3);
  assert.equal(result.pending[0].file, '20261022100400_p1_durable_planning.sql');
  assert.deepEqual(result.pending.slice(-13).map(x=>x.file), [
    '20261024190000_p1_platform_operations.sql',
    '20261026152000_feature2_trends_drafts.sql',
    '20261026152102_p0_249_reel_render_intent.sql',
    '20261026194000_feature2_ai_cost_ledger.sql',
    '20261028092346_feature3_model_catalog_drafts.sql',
    '20261028101328_feature3_gpu_budget_jobs.sql',
    '20261028173000_feature1_retailer_inbox.sql',
    '20261028190000_feature3_model_review_audit.sql',
    '20261028210000_feature3_private_evidence_commit.sql',
    '20261028223000_feature3_pending_model_import.sql',
    '20261028230000_feature3_gpu_private_output_cas.sql',
    '20261028231000_feature3_gpu_outbox_recovery.sql',
    '20261028232000_feature3_model_original_registration.sql',
  ]);
});
test('refuses missing snapshot, wrong project, gaps, duplicates, renamed or newer remote versions', () => {
  assert.throws(() => verifyPreflight({ requireRemoteHistory: true }), /history is required/);
  assert.throws(() => verifyPreflight({ remoteHistory: { project_ref: 'wrong-project', applied: [] } }), /dedicated/);
  const one = known.local[0], two = known.local[1], three = known.local[2];
  for (const bad of [
    [one, three],
    [one, one],
    [one, { ...two, name: 'wrong_name' }],
    [one, two, { version: '20991231235959', name: 'fake' }],
  ]) assert.throws(() => verifyPreflight({ remoteHistory: history(bad) }), /diverges|duplicate/);
});
test('rejects gaps, duplicate version files and stripped service-only migration safeguards', () => {
  temporaryMigrationCopy(dir => {
    rmSync(resolve(dir, '20261022220000_p1_durable_recovery.sql'));
    assert.throws(() => verifyPreflight({ migrationDir: dir }), /missing canonical/);
  });
  temporaryMigrationCopy(dir => {
    writeFileSync(resolve(dir, '20261022220000_collision.sql'), readFileSync(resolve(dir, '20261022220000_p1_durable_recovery.sql'), 'utf8'));
    assert.throws(() => verifyPreflight({ migrationDir: dir }), /duplicate migration version/);
  });
  temporaryMigrationCopy(dir => {
    const path = resolve(dir, '20261022220000_p1_durable_recovery.sql');
    const sql = readFileSync(path, 'utf8').replace('alter table public.job_outbox enable row level security;', '-- removed');
    writeFileSync(path, sql);
    assert.throws(() => verifyPreflight({ migrationDir: dir }), /missing required SQL capability/);
  });
  temporaryMigrationCopy(dir => {
    renameSync(resolve(dir, '20261022180000_p1_dev_media_integrity.sql'), resolve(dir, 'broken.sql'));
    assert.throws(() => verifyPreflight({ migrationDir: dir }), /invalid migration file name|missing canonical/);
  });
  temporaryMigrationCopy(dir => {
    const path = resolve(dir, '20261026152102_p0_249_reel_render_intent.sql');
    const sql = readFileSync(path, 'utf8').replace('if music = any(ids) then return null; end if;', '-- removed mixed media rights denial');
    writeFileSync(path, sql);
    assert.throws(() => verifyPreflight({ migrationDir: dir }), /missing required SQL capability/);
  });
});
