// Workstream P: local, read-only inspection only. NEVER applies hosted SQL.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DEV_PROJECT_REF, REQUIRED_MIGRATIONS, verifyPreflight } from './dev-db-preflight.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
export const MAX_HISTORY_AGE_MS = 30 * 60 * 1000;
const BASELINE_APPLIED_COUNT = 3;
export const GATE_STATUS = 'BLOCKED_UNTIL_EXPLICIT_GATE_1_APPROVAL';

function fail(message) { throw new Error('DEV migration execution plan: ' + message); }

export function buildMigrationExecutionPlan({
  remoteHistory,
  migrationDir = resolve(root, 'supabase/migrations'),
  now = new Date(),
} = {}) {
  if (!remoteHistory || typeof remoteHistory !== 'object') fail('fresh read-only history required');
  const current = new Date(now).getTime();
  const captured = Date.parse(remoteHistory.captured_at);
  if (!Number.isFinite(current) || !Number.isFinite(captured) ||
      captured > current + 2 * 60 * 1000 ||
      current - captured > MAX_HISTORY_AGE_MS) {
    fail('history captured_at must be a recent ISO-8601 timestamp (within 30 minutes)');
  }
  // Workstream L checks the pinned project and every version/name in the ordered prefix.
  const preflight = verifyPreflight({ migrationDir, remoteHistory, requireRemoteHistory: true });
  // The review is for exactly these 10 files and the currently observed 3-applied baseline.
  // Unexpected new files or partial rollout require re-review, not automatic continuation.
  if (preflight.local.length !== REQUIRED_MIGRATIONS.length) fail('unreviewed migration added');
  if (preflight.appliedCount !== BASELINE_APPLIED_COUNT) {
    fail('baseline changed or partial rollout detected; stop for coordinator review');
  }
  const pending = preflight.pending.map((item, index) => {
    const sql = readFileSync(resolve(migrationDir, item.file), 'utf8');
    const withoutLeadingComments = sql.replace(/^(?:\s*--[^\n]*(?:\n|$))*/, '').trimStart();
    if (!/^begin\s*;/i.test(withoutLeadingComments) || !/\bcommit\s*;\s*$/i.test(sql)) {
      fail('expected explicit BEGIN/COMMIT transaction wrapper: ' + item.file);
    }
    if (/^\s*\\(?:i|ir|connect|!|copy)\b/im.test(sql) ||
        /\b(?:drop\s+(?:database|schema|table)\b|truncate\s+table\b)/i.test(sql)) {
      fail('unexpected high-risk or psql meta command in ' + item.file);
    }
    return {
      step: index + 1,
      file: item.file,
      version: item.version,
      name: item.name,
      bytes: Buffer.byteLength(sql),
      sha256: createHash('sha256').update(sql).digest('hex'),
    };
  });
  return {
    project_ref: DEV_PROJECT_REF,
    history_captured_at: remoteHistory.captured_at,
    applied_versions: preflight.local.slice(0, preflight.appliedCount).map(x => x.version),
    pending,
    gate: GATE_STATUS,
    authorized_to_apply: false,
  };
}

function main(args) {
  if (args.length !== 2 || args[0] !== '--remote-history') {
    fail('usage: node tests/security/dev-migration-plan.mjs --remote-history <uncommitted-live-dev-history.json>');
  }
  const history = JSON.parse(readFileSync(resolve(process.cwd(), args[1]), 'utf8'));
  const plan = buildMigrationExecutionPlan({ remoteHistory: history });
  process.stdout.write(JSON.stringify(plan, null, 2) + '\n');
  process.stdout.write('NO SQL EXECUTED. Gate 1, verified backup AND reviewed dry-run are required.\n');
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { main(process.argv.slice(2)); } catch (err) { console.error(err.message); process.exitCode = 1; }
}
