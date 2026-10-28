// Feature2: exact 21-version hosted DEV preflight; DOES NOT mutate Supabase.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DEV_PROJECT_REF, verifyPreflight } from './dev-db-preflight.mjs';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)), '../..');
export const FEATURE2_FILE='20261026194000_feature2_ai_cost_ledger.sql';
export const OTHER_FEATURE_FILE='20261028092346_feature3_model_catalog_drafts.sql';
export const HOSTED_APPLIED_COUNT=21;

export function scopedFeature2Plan(snapshot, options={}) {
  if (!snapshot || snapshot.project_ref!==DEV_PROJECT_REF)
    throw new Error('Only exact RetailGrowthAI DEV is permitted');
  if (!snapshot.captured_at || !Number.isFinite(Date.parse(snapshot.captured_at)))
    throw new Error('Fresh read-only snapshot timestamp required');
  const now=options.now===undefined?Date.now():Date.parse(options.now);
  const then=Date.parse(snapshot.captured_at);
  if (!Number.isFinite(now) || then>now+120000 || now-then>30*60000)
    throw new Error('Remote migration history must be fresh within 30 minutes');
  const migrationDir=options.migrationDir||resolve(ROOT,'supabase/migrations');
  const view=verifyPreflight({
    migrationDir,
    remoteHistory:snapshot,
    requireRemoteHistory:true
  });
  if (view.appliedCount!==HOSTED_APPLIED_COUNT)
    throw new Error('Expected exactly 21 applied canonical migrations');
  const pending=view.pending.map(x=>x.file);
  // Preserve historical exact-prefix gate while explicitly recognizing the
  // source-only Feature #1 migration. No additional version is authorized for execution.
  if (pending.length!==10 || pending[0]!==FEATURE2_FILE || pending[1]!==OTHER_FEATURE_FILE ||
      pending[2]!=='20261028101328_feature3_gpu_budget_jobs.sql' ||
      pending[3]!=='20261028173000_feature1_retailer_inbox.sql' ||
      pending[4]!=='20261028190000_feature3_model_review_audit.sql' ||
      pending[5]!=='20261028210000_feature3_private_evidence_commit.sql' ||
      pending[6]!=='20261028223000_feature3_pending_model_import.sql' ||
      pending[7]!=='20261028230000_feature3_gpu_private_output_cas.sql' ||
      pending[8]!=='20261028231000_feature3_gpu_outbox_recovery.sql' ||
      pending[9]!=='20261028232000_feature3_model_original_registration.sql')
    throw new Error('Unexpected pending migrations; refuse any unreviewed release');
  const source=readFileSync(resolve(migrationDir,FEATURE2_FILE),'utf8');
  const cleaned=source.replace(/^(?:\s*--[^\n]*(?:\n|$))*/, '').trimStart();
  if (!/^begin\s*;/i.test(cleaned) || !/\bcommit\s*;\s*$/i.test(source))
    throw new Error('AI ledger must be transaction wrapped');
  const required=[
    /create table public[.]shop_ai_budget_controls/i,
    /create table public[.]shop_ai_spend_reservations/i,
    /ai_unique_request_per_shop unique[(]shop_id,request_id[)]/i,
    /alter table public[.]shop_ai_budget_controls enable row level security/i,
    /alter table public[.]shop_ai_spend_reservations enable row level security/i,
    /revoke all on public[.]shop_ai_budget_controls from public,anon,authenticated/i,
    /revoke all on public[.]shop_ai_spend_reservations from public,anon,authenticated/i,
    /pg_catalog[.]ceil[(]p_upper_cost_usd/i,
    /AI_REQUEST_ALREADY_RESERVED/i,
    /grant execute on function public[.]feature2_reserve_ai_budget[(]uuid,uuid,text,numeric,uuid[)]\s+to service_role/i,
    /grant execute on function public[.]feature2_settle_ai_budget[(]uuid,numeric[)]\s+to service_role/i
  ];
  if (required.some(re=>!re.test(source)))
    throw new Error('Missing mandatory SQL tenant-cost security marker');
  if (/^\s*\\(?:connect|copy|!|i|ir)\b/im.test(source) ||
      /\b(?:drop\s+(?:table|schema|database)|truncate|delete\s+from\s+auth[.]users)\b/i.test(source))
    throw new Error('Destructive or client-side SQL not permitted');
  return {
    project_ref:DEV_PROJECT_REF,
    reviewed_applied_versions:view.appliedCount,
    source_file:FEATURE2_FILE,
    source_version:'20261026194000',
    source_name:'feature2_ai_cost_ledger',
    source_sha256:createHash('sha256').update(source).digest('hex'),
    other_pending_version_remains_unapplied:'20261028092346',
    selected_pending_count:1,
    backup_restore_verified:false,
    actual_hosted_sql_execution:false,
    authorized_to_apply:false,
    release_gate:'BACKUP_RESTORE_AND_EXACT_VERSION_EXECUTOR_REQUIRED',
  };
}

if (process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if (process.argv.length!==4 || process.argv[2]!=='--remote-history')
    throw new Error('Usage: node tests/security/feature2_scoped_dev_release_plan.mjs --remote-history <PRIVATE_READ_ONLY_SNAPSHOT.json>');
  const snapshot=JSON.parse(readFileSync(resolve(process.argv[3]),'utf8'));
  process.stdout.write(JSON.stringify(scopedFeature2Plan(snapshot),null,2)+'\n');
}
