// Read-only release preflight. No Supabase credentials, remote calls or mutation.
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
export const DEV_PROJECT_REF = 'jeearzffnjbvghwjjjrf';
export const REQUIRED_MIGRATIONS = Object.freeze([
  '20261022085124_p1_foundation.sql',
  '20261022085132_p1_private_media.sql',
  '20261022085503_p1_security_hardening.sql',
  '20261022100400_p1_durable_planning.sql',
  '20261022101800_p1_render_claim.sql',
  '20261022162000_p1_draft_save.sql',
  '20261022173000_p1_private_upload_registration.sql',
  '20261022180000_p1_dev_media_integrity.sql',
  '20261022205000_p1_worker_execution_budget.sql',
  '20261022220000_p1_durable_recovery.sql',
]);
export const FOLLOW_ON_MIGRATIONS = Object.freeze([
  '20261023134701_p1_subscription_quota.sql',
  '20261023165300_p1_platform_admin.sql',
  '20261023210000_p1_onboarding_approval.sql',
]);

const CAPABILITIES = {
  '20261022085124': [/enable row level security/i, /create table public\.shops/i, /create table public\.shop_memberships/i],
  '20261022085132': [/storage\.buckets/i, /retailgrowth-media/i],
  '20261022100400': [/claim_campaign_job/i],
  '20261022101800': [/claim_render_job/i],
  '20261022162000': [/save_campaign_day/i],
  '20261022173000': [/register_uploaded_image/i],
  '20261022180000': [/storage\.objects/i, /uploads\//i],
  '20261022205000': [/25 minutes/i],
  '20261023134701': [
    /create table public\.shop_subscriptions/i,
    /create table public\.shop_usage_reservations/i,
    /enable row level security/i,
    /for update/i,
    /reserve_subscription_unit/i,
    /subscription_reserve_campaign/i,
    /subscription_reserve_render/i,
    /errcode='RG001'/i,
    /errcode='RG002'/i,
  ],
  '20261023165300': [
    /create table retail_private\.platform_admins/i,
    /create table retail_private\.platform_admin_audit/i,
    /security definer set search_path = ''/i,
    /retail_platform_me/i,
    /retail_platform_summary/i,
    /retail_platform_shops/i,
    /retail_platform_set_subscription/i,
    /assert_platform_admin/i,
    /revoke all on retail_private\.platform_admins/i,
  ],
  '20261023210000': [
    /create table retail_private\.onboarding_requests/i,
    /retail_private\.onboarding_gate/i,
    /create trigger retail_queue_on_auth_signup/i,
    /retail_platform_onboarding_requests/i,
    /retail_platform_review_onboarding/i,
    /shop_onboarding_allowed/i,
    /revoke all on retail_private\.onboarding_requests/i,
  ],
  '20261022220000': [
    /create table public\.job_outbox/i, /create table public\.job_poison_events/i,
    /alter table public\.job_outbox enable row level security/i,
    /alter table public\.job_poison_events enable row level security/i,
    /revoke all on public\.job_outbox from public, anon, authenticated/i,
    /revoke all on public\.job_poison_events from public, anon, authenticated/i,
    /planning_claim_token/i, /render_claim_token/i,
    /claim_outbox_events/i, /confirm_outbox_event/i,
    /complete_campaign_claim/i, /fail_campaign_claim/i,
    /complete_render_claim/i, /fail_render_claim/i,
    /record_poison_event/i, /reconcile_stale_jobs/i,
    /grant execute on function public\./i,
  ],
};

function fail(message) { throw new Error('DEV migration preflight: ' + message); }

export function verifyPreflight({ migrationDir = resolve(root, 'supabase/migrations'), remoteHistory = null, requireRemoteHistory = false } = {}) {
  const names = readdirSync(migrationDir).filter(name => name.endsWith('.sql')).sort();
  if (!names.length) fail('no migration SQL found');
  const versions = new Set();
  const items = names.map(name => {
    const match = /^(\d{14})_([a-z][a-z0-9_]*)\.sql$/.exec(name);
    if (!match) fail('invalid migration file name ' + name);
    if (versions.has(match[1])) fail('duplicate migration version ' + match[1]);
    versions.add(match[1]);
    const sql = readFileSync(resolve(migrationDir, name), 'utf8');
    if (!sql.trim()) fail('empty migration ' + name);
    for (const pattern of CAPABILITIES[match[1]] || []) {
      if (!pattern.test(sql)) fail('missing required SQL capability ' + pattern + ' in ' + name);
    }
    return { version: match[1], name: match[2], file: name };
  });
  for (const file of [...REQUIRED_MIGRATIONS, ...FOLLOW_ON_MIGRATIONS]) {
    if (!names.includes(file)) fail('missing canonical migration ' + file);
  }
  for (let i = 1; i < items.length; i++) {
    if (items[i].version <= items[i - 1].version) fail('migration history is not strictly increasing');
  }
  if (requireRemoteHistory && remoteHistory === null) fail('fresh read-only DEV history is required');
  let appliedCount = 0;
  if (remoteHistory !== null) {
    if (!remoteHistory || remoteHistory.project_ref !== DEV_PROJECT_REF || !Array.isArray(remoteHistory.applied)) {
      fail('remote history must identify ONLY the dedicated RetailGrowthAI DEV project and an applied array');
    }
    const seen = new Set();
    for (const [index, entry] of remoteHistory.applied.entries()) {
      if (!entry || !/^\d{14}$/.test(String(entry.version))) fail('invalid remote version at position ' + index);
      if (seen.has(String(entry.version))) fail('duplicate remote version ' + entry.version);
      seen.add(String(entry.version));
      const expected = items[index];
      if (!expected || String(entry.version) !== expected.version || entry.name !== expected.name) {
        fail('remote migration diverges from local ordered prefix at position ' + index);
      }
    }
    appliedCount = remoteHistory.applied.length;
  }
  return { local: items, appliedCount, pending: remoteHistory === null ? null : items.slice(appliedCount) };
}

function main() {
  const args = process.argv.slice(2);
  if (args.length !== 2 || args[0] !== '--remote-history') {
    fail('usage: node tests/security/dev-db-preflight.mjs --remote-history <fresh-readonly-DEV-history.json>');
  }
  const history = JSON.parse(readFileSync(resolve(process.cwd(), args[1]), 'utf8'));
  const result = verifyPreflight({ remoteHistory: history, requireRemoteHistory: true });
  console.log('PASS: local migration versions/order and required SQL capability markers');
  console.log('DEV migration history prefix: ' + result.appliedCount + ' applied; ' + result.pending.length + ' pending');
  for (const migration of result.pending) console.log('PENDING: ' + migration.file);
  console.log('READ-ONLY preflight only. Stop for explicit approval, verified backups and hosted security checks.');
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { main(); } catch (error) { console.error(error.message); process.exitCode = 1; }
}
