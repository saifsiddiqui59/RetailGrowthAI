import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, rmSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { DEV_PROJECT_REF, verifyPreflight } from './dev-db-preflight.mjs';
import { FEATURE3_HOSTED_BASELINE, FEATURE3_PENDING_SQL, planFeature3DevMigrations }
  from './feature3-migration-release-gate.mjs';

const sourceMigrations = resolve(import.meta.dirname, '../../supabase/migrations');
const local = verifyPreflight().local;
function snapshot(count = FEATURE3_HOSTED_BASELINE) {
  return {
    project_ref: DEV_PROJECT_REF,
    captured_at: new Date().toISOString(),
    applied: local.slice(0, count).map(({ version, name }) => ({ version, name })),
  };
}
function tempMigrations(run) {
  const directory = mkdtempSync(resolve(tmpdir(), 'rgai-feature3-plan-'));
  try {
    cpSync(sourceMigrations, directory, { recursive: true });
    run(directory);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}
test('fresh exact 24-version hosted baseline creates seven ordered SHA256-bound pending steps, never authorization', () => {
  const plan = planFeature3DevMigrations({ remoteHistory: snapshot() });
  assert.equal(plan.project_ref, DEV_PROJECT_REF);
  assert.equal(plan.observed_applied_count, 24);
  assert.equal(plan.stage, 'SEVEN_MIGRATIONS_PENDING');
  assert.deepEqual(plan.pending.map(x => x.file), FEATURE3_PENDING_SQL);
  assert.equal(plan.pending.length, 7);
  assert.equal(plan.authorized_to_apply, false);
  assert.equal(plan.hosted_sql_applied_by_this_tool, false);
  assert.equal(plan.hosted_signed_auth_verified, false);
  assert.equal(plan.provider_vton_inference_verified, false);
  for (const step of plan.pending) {
    assert.match(step.sha256, /^[a-f0-9]{64}$/);
    assert.equal(step.transactional, true);
    assert.equal(step.replay_is_safe, false);
    assert.ok(step.bytes > 0);
    assert.ok(step.dependency);
  }
});
test('post-release canonical 31 history is informational, not authenticated hosted acceptance', () => {
  const plan = planFeature3DevMigrations({ remoteHistory: snapshot(local.length) });
  assert.equal(plan.pending.length, 0);
  assert.equal(plan.reviewed_source.length, 7);
  assert.equal(plan.stage, 'SCHEMA_PRESENT_AUTHENTICATED_E2E_UNVERIFIED');
  assert.equal(plan.authorized_to_apply, false);
  assert.equal(plan.hosted_signed_auth_verified, false);
});
test('partial applied history and missing/stale/foreign/future snapshots always refuse', () => {
  for (let count = 0; count <= local.length; count++) {
    if (count === 24 || count === local.length) continue;
    assert.throws(() => planFeature3DevMigrations({ remoteHistory: snapshot(count) }), /partial or unexpected/);
  }
  assert.throws(() => planFeature3DevMigrations(), /read-only remote history required/);
  assert.throws(() => planFeature3DevMigrations({
    remoteHistory: { ...snapshot(), project_ref: 'WineShopPOS' },
  }), /dedicated/);
  assert.throws(() => planFeature3DevMigrations({
    remoteHistory: { ...snapshot(), captured_at: '2026-01-01T00:00:00Z' },
  }), /fresh/);
  assert.throws(() => planFeature3DevMigrations({
    remoteHistory: { ...snapshot(), captured_at: new Date(Date.now() + 3 * 60_000).toISOString() },
  }), /fresh/);
  const historyWithGap = snapshot();
  historyWithGap.applied.splice(3, 1);
  assert.throws(() => planFeature3DevMigrations({ remoteHistory: historyWithGap }), /diverges/);
});
test('SQL tampering strips atomicity or introduces destructive DDL -> block before release', () => {
  tempMigrations(dir => {
    const path = resolve(dir, FEATURE3_PENDING_SQL[0]);
    const sql = readFileSync(path, 'utf8');
    writeFileSync(path, sql.replace(/commit;\s*$/i, '-- removed'));
    assert.throws(() => planFeature3DevMigrations({ remoteHistory: snapshot(), migrationDir: dir }), /BEGIN\/COMMIT required/);
  });
  tempMigrations(dir => {
    const path = resolve(dir, FEATURE3_PENDING_SQL[1]);
    const sql = readFileSync(path, 'utf8');
    writeFileSync(path, sql.replace('commit;', 'drop table public.shops;\ncommit;'));
    assert.throws(() => planFeature3DevMigrations({ remoteHistory: snapshot(), migrationDir: dir }), /dangerous DDL/);
  });
});
test('migration files have exactly 24 reviewed predecessors and 7 ordered canonical follow-ons', () => {
  assert.equal(local.length, 31, 'new migrations require manual re-review before DEV operations');
  assert.deepEqual(local.slice(24).map(x => x.file), FEATURE3_PENDING_SQL);
});
