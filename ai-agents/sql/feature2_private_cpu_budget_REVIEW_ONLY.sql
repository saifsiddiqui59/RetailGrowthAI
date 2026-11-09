-- Feature2 F2-21 private CPU-only local voice budget PREP proposal.
-- REVIEW ONLY. Do not apply to hosted DEV/PROD, start Kokoro, GPU or paid AI.
-- Not an atomic budget/worker lease implementation by itself.
-- Required: reviewed serializable CAS transaction plus immutable request UUID,
-- claim/renew/settle fence, signed user membership, worker budget accounting.

create table public.feature2_private_cpu_budgets (
  shop_id uuid not null references public.shops(id),
  campaign_id uuid not null references public.campaigns(id),
  quota_policy jsonb not null check (
    jsonb_typeof(quota_policy)='object' and
    quota_policy->>'shop_id'=shop_id::text and
    quota_policy->>'campaign_id'=campaign_id::text and
    quota_policy->>'provider'='kokoro-onnx' and
    quota_policy->'paid_api_calls_allowed'='false'::jsonb and
    quota_policy->>'policy_state'='ACTIVE'
  ),
  revoked_at timestamptz,
  primary key(shop_id,campaign_id)
);
alter table public.feature2_private_cpu_budgets enable row level security;
revoke all on public.feature2_private_cpu_budgets
  from public,anon,authenticated;
grant select on public.feature2_private_cpu_budgets to authenticated;
grant all on public.feature2_private_cpu_budgets to service_role;
create policy feature2_private_cpu_editor_read
on public.feature2_private_cpu_budgets for select to authenticated
using (revoked_at is null and
  retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));

create table public.feature2_private_cpu_reservations (
  shop_id uuid not null,
  campaign_id uuid not null,
  job_key uuid not null,
  request_sha256 text not null check(request_sha256 ~ '^[0-9a-f]{64}$'),
  budget_revision bigint not null check(budget_revision >= 0),
  reserved_cpu_ms integer not null check(
    reserved_cpu_ms between 2000 and 180000),
  lease_fence bigint not null check(lease_fence > 0),
  lease_expires_ms bigint not null check(lease_expires_ms > 0),
  period_id text not null check(period_id ~ '^\d{4}-(0[1-9]|1[0-2])$'),
  status text not null check(
    status in ('RESERVED','RUNNING','SETTLED','FAILED','DENIED','BLOCKED')),
  paid_api_calls integer not null default 0 check(paid_api_calls=0),
  can_publish boolean not null default false check(can_publish is false),
  private boolean not null default true check(private is true),
  primary key(shop_id,campaign_id,job_key),
  foreign key(shop_id,campaign_id)
  references public.feature2_private_cpu_budgets(shop_id,campaign_id)
);
create index feature2_cpu_reservations_active_scope on
  public.feature2_private_cpu_reservations(shop_id,campaign_id,status);
alter table public.feature2_private_cpu_reservations enable row level security;
revoke all on public.feature2_private_cpu_reservations
  from public,anon,authenticated;
grant select on public.feature2_private_cpu_reservations to authenticated;
grant all on public.feature2_private_cpu_reservations to service_role;
create policy feature2_private_cpu_reservation_editor_read
on public.feature2_private_cpu_reservations for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));

-- Production work not included in this review-only proposal:
-- 1. Reuse the reviewed durable Supabase lease/claim/outbox transaction
--    implementation, or implement a proper SECURITY DEFINER RPC with
--    verified auth.uid(), locked quota row, current plan/source SHA check,
--    unique job UUID and exact request fingerprint under a single commit.
-- 2. Atomically increment reserved CPU and active worker count, never merely
--    trust caller's earlier policy SELECT; independently checked tenant rates.
-- 3. Lease token must fence claim/renew/settle and original WAV write.
-- 4. A 503/timeout must be reconciled with signed GET by original job UUID,
--    NOT blindly re-reserved with a new UUID or auto-promoted to Azure.
-- 5. No upload, private bucket, model weights, commercial or publishing grant.
