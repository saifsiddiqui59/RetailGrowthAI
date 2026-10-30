// Read-only, fail-closed, seven-version Feature3 hosted DEV release rehearsal.
// A migration plan is NEVER permission to execute SQL or a signed-user acceptance result.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DEV_PROJECT_REF, verifyPreflight } from './dev-db-preflight.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
export const FEATURE3_HOSTED_BASELINE = 24;
export const FEATURE3_PENDING_SQL = Object.freeze([
  '20261028173000_feature1_retailer_inbox.sql',
  '20261028190000_feature3_model_review_audit.sql',
  '20261028210000_feature3_private_evidence_commit.sql',
  '20261028223000_feature3_pending_model_import.sql',
  '20261028230000_feature3_gpu_private_output_cas.sql',
  '20261028231000_feature3_gpu_outbox_recovery.sql',
  '20261028232000_feature3_model_original_registration.sql',
]);
export const FEATURE3_DEPENDENCIES = Object.freeze([
  'Feature1 inbox after existing campaign/render/poster jobs',
  'Model-review evidence and immutable audit after Feature3 model catalog',
  'Service-only evidence commit after human-review tables',
  'Signed pending model import after Feature3 model catalog',
  'Private generated-output CAS after Feature3 GPU jobs',
  'GPU dispatch/recovery after generated-output/outbox tables',
  'Signed private model-original registration after pending import',
]);

function fail(message) { throw new Error('Feature3 DEV migration gate: ' + message); }

export function planFeature3DevMigrations({
  remoteHistory,
  migrationDir = resolve(root, 'supabase/migrations'),
  now = new Date(),
} = {}) {
  if (!remoteHistory || typeof remoteHistory !== 'object') fail('read-only remote history required');
  const currentMs = new Date(now).getTime();
  const capturedMs = Date.parse(remoteHistory.captured_at);
  if (!Number.isFinite(currentMs) || !Number.isFinite(capturedMs) ||
      capturedMs > currentMs + 120_000 || currentMs - capturedMs > 1_800_000) {
    fail('read-only snapshot must be fresh (30 minutes maximum)');
  }
  // Verifies ALL preceding schema capability markers, local naming and exact remote
  // chronological prefix. A newer release or divergent version requires re-review.
  const result = verifyPreflight({ migrationDir, remoteHistory, requireRemoteHistory: true });
  const local = result.local;
  if (local.length !== FEATURE3_HOSTED_BASELINE + FEATURE3_PENDING_SQL.length ||
      local.slice(FEATURE3_HOSTED_BASELINE).map(x => x.file).join('|') !== FEATURE3_PENDING_SQL.join('|')) {
    fail('canonical migration inventory changed; stop for coordinator re-review');
  }
  if (result.appliedCount !== FEATURE3_HOSTED_BASELINE && result.appliedCount !== local.length) {
    fail('partial or unexpected hosted migration history; stop for recovery review');
  }
  const steps = FEATURE3_PENDING_SQL.map((file, index) => {
    const sql = readFileSync(resolve(migrationDir, file), 'utf8');
    const body = sql.replace(/^(?:\s*--[^\n]*\n)*/, '').trimStart();
    if (!/^begin\s*;/i.test(body) || !/\bcommit\s*;\s*$/i.test(sql)) {
      fail('transaction BEGIN/COMMIT required in ' + file);
    }
    if (/^\s*\\(?:i|ir|connect|!|copy)\b/im.test(sql) ||
        /\b(?:drop\s+(?:database|schema|table)\b|truncate\s+table\b|alter\s+system\b)/i.test(sql)) {
      fail('dangerous DDL or psql meta-command in ' + file);
    }
    return {
      order: index + 1,
      file,
      version: local[FEATURE3_HOSTED_BASELINE + index].version,
      bytes: Buffer.byteLength(sql),
      sha256: createHash('sha256').update(sql).digest('hex'),
      dependency: FEATURE3_DEPENDENCIES[index],
      transactional: true,
      // SQL contains CREATEs without IF NOT EXISTS. Duplicate application is
      // NOT idempotent; Supabase version ledger must guarantee exactly-once.
      replay_is_safe: false,
    };
  });
  const alreadyApplied = result.appliedCount === local.length;
  return {
    project_ref: DEV_PROJECT_REF,
    captured_at: remoteHistory.captured_at,
    observed_applied_count: result.appliedCount,
    stage: alreadyApplied ? 'SCHEMA_PRESENT_AUTHENTICATED_E2E_UNVERIFIED' : 'SEVEN_MIGRATIONS_PENDING',
    pending: alreadyApplied ? [] : steps,
    reviewed_source: steps,
    prerequisites: ['separately recorded operator approval', 'verified DEV backup and restore rehearsal',
      'offline disposable SQL negative/RLS test PASS', 'protected ordered release with version-preserving history'],
    rollback: 'Do not replay/down-migrate with DROP CASCADE. Halt on any error and use verified DEV restore/roll-forward procedure.',
    authorized_to_apply: false,
    hosted_sql_applied_by_this_tool: false,
    hosted_signed_auth_verified: false,
    provider_vton_inference_verified: false,
  };
}

function main(argv) {
  if (argv.length !== 2 || argv[0] !== '--remote-history') {
    fail('usage: node tests/security/feature3-migration-release-gate.mjs --remote-history <uncommitted-readonly-dev-history.json>');
  }
  const remoteHistory = JSON.parse(readFileSync(resolve(process.cwd(), argv[1]), 'utf8'));
  process.stdout.write(JSON.stringify(planFeature3DevMigrations({ remoteHistory }), null, 2) + '\n');
  process.stdout.write('READ ONLY: no hosted DDL, no test-user provisioning, no paid inference.\n');
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { main(process.argv.slice(2)); } catch (e) { console.error(e.message); process.exitCode = 1; }
}
