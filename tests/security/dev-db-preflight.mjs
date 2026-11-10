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
  '20261023191246_p1_onboarding_approval.sql',
  '20261024113000_p1_poster_drafts.sql',
  '20261024150000_p1_poster_jobs.sql',
  '20261024160000_p1_notification_outbox.sql',
  '20261024170000_p1_poster_banner_selection.sql',
  '20261024180000_p1_poster_dispatch_schema_usage.sql',
  '20261024190000_p1_platform_operations.sql',
  '20261026152000_feature2_trends_drafts.sql',
  // CLI-generated, 2026-10-26T15:21:02Z, reviewed P0 #249 Reel RPC source.
  '20261026152102_p0_249_reel_render_intent.sql',
  '20261026194000_feature2_ai_cost_ledger.sql',
  // Hosted history already includes Feature2; Feature3 is the last pending migration.
  '20261028092346_feature3_model_catalog_drafts.sql',
  '20261028101328_feature3_gpu_budget_jobs.sql',
  // Feature #1 retailer inbox is additive, SOURCE-ONLY and not a hosted release authorization.
  '20261028173000_feature1_retailer_inbox.sql',
  // Feature3 human review is SOURCE ONLY, not a hosted rollout authorization.
  '20261028190000_feature3_model_review_audit.sql',
  // Feature3 immutable verifier RPC is SOURCE ONLY; never execute on hosted DEV automatically.
  '20261028210000_feature3_private_evidence_commit.sql',
  // Feature3 pending import is SOURCE ONLY, not a hosted migration authorization.
  '20261028223000_feature3_pending_model_import.sql',
  // Retailer-registered original model PNG, source-only / explicitly not hosted approved.
  '20261028230000_feature3_gpu_private_output_cas.sql',
  '20261028231000_feature3_gpu_outbox_recovery.sql',
  '20261028232000_feature3_model_original_registration.sql',
]);

const CAPABILITIES = {
  '20261028231000': [
    /alter table retail_private[.]feature3_gpu_outbox/i,
    /create table retail_private[.]feature3_gpu_recovery_events/i,
    /enable row level security/i,
    /revoke all on retail_private[.]feature3_gpu_recovery_events/i,
    /create function public[.]feature3_claim_gpu_dispatch/i,
    /create function public[.]feature3_confirm_gpu_dispatch/i,
    /create function public[.]feature3_audit_gpu_recovery/i,
    /for update of o skip locked/i,
    /MANUAL_FINANCIAL_RECONCILIATION/i,
    /grant execute on function public[.]feature3_audit_gpu_recovery/i,
    /to service_role/i,
  ],
  '20261028230000': [
    /create table retail_private[.]feature3_gpu_output_evidence/i,
    /create function public[.]feature3_commit_gpu_private_output/i,
    /security definer set search_path=''/i,
    /on storage[.]objects as restrictive/i,
    /for update/i,
    /insert into public[.]media_assets/i,
    /p_image_sha256/i,
    /create trigger feature3_output_settlement_guard/i,
    /retail_private[.]feature3_output_settlement_fence/i,
    /grant execute on function public[.]feature3_commit_gpu_private_output/i,
    /to service_role/i,
  ],
  '20261028232000': [
    /drop policy retailgrowth_media_insert on storage[.]objects/i,
    /create policy retailgrowth_media_insert on storage[.]objects/i,
    /model-library/i,
    /owner_id=[(]select auth[.]uid[(][)][)]::text/i,
    /create function public[.]feature3_register_model_original/i,
    /security definer set search_path=''/i,
    /public[.]shop_memberships/i,
    /storage[.]objects/i,
    /owner_id=actor::text/i,
    /insert into public[.]media_assets/i,
    /SOURCE_REGISTERED_PENDING_EVIDENCE/i,
    /byte_sha_verified/i,
    /license_verified/i,
    /grant execute on function public[.]feature3_register_model_original/i,
    /to authenticated/i,
  ],
  '20261028223000': [
    /create function public[.]feature3_import_pending_model/i,
    /security definer set search_path=''/i,
    /public[.]shop_memberships/i,
    /public[.]media_assets/i,
    /scope,status,source_kind/i,
    /'PENDING_REVIEW'/i,
    /rights_verified/i,
    /for share/i,
    /for update/i,
    /on conflict[(]model_id[)] do nothing/i,
    /revoke all on function public[.]feature3_import_pending_model/i,
    /grant execute on function public[.]feature3_import_pending_model/i,
    /to authenticated/i,
  ],
  '20261028210000': [
    /create function public[.]feature3_commit_verified_evidence/i,
    /security definer set search_path=''/i,
    /retail_private[.]feature3_model_evidence/i,
    /from public[.]feature3_models/i,
    /for update/i,
    /public[.]shop_memberships/i,
    /p_expected_image_sha256/i,
    /grant execute on function public[.]feature3_commit_verified_evidence/i,
    /to service_role/i,
  ],
  '20261028190000': [
    /create table retail_private[.]feature3_model_evidence/i,
    /create table retail_private[.]feature3_model_review_events/i,
    /enable row level security/i,
    /revoke all on retail_private[.]feature3_model_evidence from public,anon,authenticated/i,
    /revoke all on retail_private[.]feature3_model_review_events from public,anon,authenticated/i,
    /create function public[.]feature3_review_model/i,
    /create function public[.]feature3_revoke_model/i,
    /create trigger feature3_model_rights_guard/i,
    /feature3_can_review/i,
    /for update/i,
    /grant execute on function public[.]feature3_review_model/i,
    /grant execute on function public[.]feature3_revoke_model/i,
  ],
  '20261028173000': [
    /create table retail_private[.]retailer_inbox_events/i,
    /create table retail_private[.]retailer_inbox_reads/i,
    /alter table retail_private[.]retailer_inbox_events enable row level security/i,
    /alter table retail_private[.]retailer_inbox_reads enable row level security/i,
    /revoke all on retail_private[.]retailer_inbox_events from public,anon,authenticated/i,
    /revoke all on retail_private[.]retailer_inbox_reads from public,anon,authenticated/i,
    /retail_private[.]has_role[(]p_shop_id/i,
    /create function public[.]retail_retailer_inbox/i,
    /create function public[.]retail_retailer_set_inbox_read/i,
    /capture_retailer_job_event/i,
    /grant execute on function public[.]retail_retailer_inbox/i,
    /grant execute on function public[.]retail_retailer_set_inbox_read/i,
  ],
  '20261028101328': [
    /alter table public[.]shop_ai_budget_controls/i,
    /feature3_gpu_enabled boolean not null default false/i,
    /create table public[.]feature3_gpu_jobs/i,
    /create table retail_private[.]feature3_gpu_outbox/i,
    /enable row level security/i,
    /revoke all on public[.]feature3_gpu_jobs/i,
    /feature3_reserve_gpu_job/i,
    /feature3_claim_gpu_job/i,
    /feature3_finish_gpu_job/i,
    /grant execute on function public[.]feature3_reserve_gpu_job/i,
    /grant execute on function public[.]feature3_finish_gpu_job/i,
  ],
  '20261026194000': [
    /create table public[.]shop_ai_budget_controls/i,
    /create table public[.]shop_ai_spend_reservations/i,
    /enable row level security/i,
    /ai_unique_request_per_shop unique[(]shop_id,request_id[)]/i,
    /pg_catalog[.]ceil[(]p_upper_cost_usd/i,
    /AI_REQUEST_ALREADY_RESERVED/i,
    /security definer set search_path = ''/i,
    /grant execute on function public[.]feature2_reserve_ai_budget[(]uuid,uuid,text,numeric,uuid[)]/i,
  ],
  '20261028092346': [
    /create table public[.]feature3_models/i,
    /create table public[.]feature3_poster_designs/i,
    /enable row level security/i,
    /revoke all on table public[.]feature3_models from public,anon,authenticated/i,
    /revoke all on table public[.]feature3_poster_designs from public,anon,authenticated/i,
    /feature3_valid_design/i,
    /create function public[.]save_feature3_poster_design/i,
    /security definer set search_path=''/i,
    /retail_private[.]has_role/i,
    /for update/i,
    /check[(]status in [(]'DRAFT','APPROVED','REJECTED'[)]/i,
    /grant execute on function public[.]save_feature3_poster_design/i,
  ],
  '20261026152102': [
    /create function retail_private[.]python_json_v1/i,
    /create function retail_private[.]request_reel_render_job_internal/i,
    /security definer set search_path = ''/i,
    /create function public[.]request_reel_render_job/i,
    /security invoker set search_path = ''/i,
    /if music = any[(]ids[)] then return null/i,
    /revoke all on function public[.]request_reel_render_job/i,
    /grant execute on function public[.]request_reel_render_job/i,
    /insert into public[.]render_jobs/i,
    /idempotency_key/i,
  ],
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
  '20261023191246': [
    /create table retail_private\.onboarding_requests/i,
    /retail_private\.onboarding_gate/i,
    /create trigger retail_queue_on_auth_signup/i,
    /retail_platform_onboarding_requests/i,
    /retail_platform_review_onboarding/i,
    /shop_onboarding_allowed/i,
    /revoke all on retail_private\.onboarding_requests/i,
  ],
  '20261024113000': [
    /create table public\.poster_drafts/i,
    /enable row level security/i,
    /revoke all on table public\.poster_drafts from public, anon, authenticated/i,
    /create policy poster_drafts_member_read/i,
    /create function public\.create_poster_draft/i,
    /security definer set search_path = ''/i,
    /retail_private\.has_role/i,
    /pg_catalog\.sha256/i,
    /for update/i,
  ],
  '20261024150000': [/create table public\.poster_jobs/i, /create table retail_private\.poster_outbox/i, /request_poster_job/i, /claim_poster_job/i, /complete_poster_job/i, /reconcile_poster_jobs/i, /revoke all on public\.poster_jobs/i],
  '20261024160000': [/create table retail_private\.notification_outbox/i, /capture_onboarding_notification/i, /claim_notifications/i, /confirm_notification/i, /notification_recipients/i, /revoke all on retail_private\.notification_outbox/i],
  '20261024170000': [/select_poster_banner/i, /security definer set search_path = ''/i, /retail_private\.has_role/i, /output_asset_id/i, /p_expected_instagram/i, /revoke all on function public\.select_poster_banner/i],
  '20261024180000': [/grant usage on schema retail_private to service_role/i, /begin;/i, /commit;/i],
  '20261024190000': [
    /create table retail_private[.]platform_notifications/i,
    /create table retail_private[.]platform_notification_reads/i,
    /enable row level security/i,
    /retail_platform_notifications/i,
    /retail_platform_set_notification_read/i,
    /retail_platform_subscription_watch/i,
    /refresh_platform_signals/i,
    /assert_platform_admin/i,
    /revoke all on retail_private[.]platform_notifications from public,anon,authenticated/i,
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
