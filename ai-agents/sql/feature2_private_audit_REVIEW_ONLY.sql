-- RetailGrowthAI F2-08/F2-12 audited source schema proposal.
-- REVIEW ONLY: do not run in DEV/PROD; do not create hosted test identities,
-- disable RLS, approve reviewer identities, publish media or enable paid models.
-- This is NOT a durable CAS implementation. An independently reviewed
-- SERIALIZABLE/unique/immutable service writer and human-attestation signer
-- must exist BEFORE accepting real review or workflow append evidence.
-- Uses the existing OWNER/EDITOR tenant role function.
--
-- Intended downstream use:
--  Feature2PrivateAuditStore -> Feature2PrivateAuditGateway ->
--  existing ai_agents.feature2_creative_quality HMAC validators,
--  subject to protected ZIP allowlist, secret and operator security review.

create table public.feature2_private_trace_sources (
  shop_id uuid not null references public.shops(id),
  campaign_id uuid not null references public.campaigns(id),
  workflow_id uuid not null,
  source_sha256 text not null check (source_sha256 ~ '^[0-9a-f]{64}$'),
  private boolean not null default true check (private is true),
  can_publish boolean not null default false check (can_publish is false),
  revoked_at timestamptz,
  revision bigint not null default 0 check (revision >= 0),
  primary key (shop_id,campaign_id,workflow_id)
);
create index feature2_private_trace_sources_campaign_idx on
  public.feature2_private_trace_sources(shop_id,campaign_id);
alter table public.feature2_private_trace_sources enable row level security;
revoke all on public.feature2_private_trace_sources from public,anon,authenticated;
grant select on public.feature2_private_trace_sources to authenticated;
grant all on public.feature2_private_trace_sources to service_role;
create policy feature2_private_trace_source_reader
on public.feature2_private_trace_sources for select to authenticated
using (revoked_at is null and
  retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));

create table public.feature2_private_trace_events (
  shop_id uuid not null,
  campaign_id uuid not null,
  workflow_id uuid not null,
  sequence smallint not null check (sequence between 1 and 100),
  event_id uuid not null unique,
  event_json jsonb not null check (
    jsonb_typeof(event_json)='object' and
    event_json->>'schema'='retailgrowth.feature2-private-trace.v1' and
    event_json->>'shop_id'=shop_id::text and
    event_json->>'campaign_id'=campaign_id::text and
    event_json->>'workflow_id'=workflow_id::text and
    event_json->>'sequence'=sequence::text and
    event_json->>'event_id'=event_id::text and
    event_json->'can_publish'='false'::jsonb and
    event_json->'customer_data_in_event'='false'::jsonb and
    event_json->>'server_mac' ~ '^[0-9a-f]{64}$' and
    event_json->>'event_sha256' ~ '^[0-9a-f]{64}$'
  ),
  primary key(shop_id,campaign_id,workflow_id,sequence),
  foreign key(shop_id,campaign_id,workflow_id)
  references public.feature2_private_trace_sources(
    shop_id,campaign_id,workflow_id
  )
);
create index feature2_private_trace_events_scope_idx on
  public.feature2_private_trace_events(shop_id,campaign_id,workflow_id,sequence);
alter table public.feature2_private_trace_events enable row level security;
revoke all on public.feature2_private_trace_events from public,anon,authenticated;
grant select on public.feature2_private_trace_events to authenticated;
grant all on public.feature2_private_trace_events to service_role;
create policy feature2_private_trace_event_reader
on public.feature2_private_trace_events for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[])
  and exists (select 1 from public.feature2_private_trace_sources s
    where s.shop_id=feature2_private_trace_events.shop_id
      and s.campaign_id=feature2_private_trace_events.campaign_id
      and s.workflow_id=feature2_private_trace_events.workflow_id
      and s.revoked_at is null));

create table public.feature2_private_blind_scores (
  shop_id uuid not null references public.shops(id),
  campaign_id uuid not null references public.campaigns(id),
  experiment_id text not null check (
    length(experiment_id) between 10 and 120 and
    experiment_id ~ '^[A-Za-z0-9_-]+$'
  ),
  revision smallint not null check (revision between 1 and 50),
  review_record jsonb not null check (
    jsonb_typeof(review_record)='object' and
    review_record->>'shop_id'=shop_id::text and
    review_record->>'campaign_id'=campaign_id::text and
    review_record->>'experiment_id'=experiment_id and
    review_record->>'revision'=revision::text and
    review_record->>'review_status'='HUMAN_SCORE_ONLY' and
    review_record->'private'='true'::jsonb and
    review_record->'can_publish'='false'::jsonb
  ),
  primary key(shop_id,campaign_id,experiment_id,revision)
);
create index feature2_private_blind_scores_scope_idx on
  public.feature2_private_blind_scores(shop_id,campaign_id,experiment_id,revision);
alter table public.feature2_private_blind_scores enable row level security;
revoke all on public.feature2_private_blind_scores from public,anon,authenticated;
grant select on public.feature2_private_blind_scores to authenticated;
grant all on public.feature2_private_blind_scores to service_role;
create policy feature2_private_blind_score_reader
on public.feature2_private_blind_scores for select to authenticated
using (retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));

create table public.feature2_private_blind_attestations (
  shop_id uuid not null,
  campaign_id uuid not null,
  experiment_id text not null,
  revision smallint not null check (revision between 1 and 50),
  receipt_digest text not null check (receipt_digest ~ '^[0-9a-f]{64}$'),
  candidate_digests jsonb not null check (
    jsonb_typeof(candidate_digests)='object' and
    candidate_digests ? 'A' and candidate_digests ? 'B'
  ),
  review_record jsonb not null,
  server_mac text not null check (server_mac ~ '^[0-9a-f]{64}$'),
  revoked_at timestamptz,
  primary key(shop_id,campaign_id,experiment_id,revision),
  foreign key(shop_id,campaign_id,experiment_id,revision)
  references public.feature2_private_blind_scores(
    shop_id,campaign_id,experiment_id,revision
  )
);
alter table public.feature2_private_blind_attestations enable row level security;
revoke all on public.feature2_private_blind_attestations from public,anon,authenticated;
grant select on public.feature2_private_blind_attestations to authenticated;
grant all on public.feature2_private_blind_attestations to service_role;
create policy feature2_private_blind_attestation_reader
on public.feature2_private_blind_attestations for select to authenticated
using (revoked_at is null and
  retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));

-- Mandatory independently reviewed production follow-up:
-- (1) Authoritative writer must verify actual signed human scores from
--     separate reviewer identity, sign the COMPLETE frozen score record using
--     a private operator-managed key, and commit score+attestation atomically.
-- (2) Immutable trace append via SQL RPC transaction: one event ID, monotonic
--     sequence, previous_sha256 CAS, HMAC and source revision fence.
-- (3) Revoke/grant changes must atomically invalidate readback and audit keys;
--     immutable rows must reject UPDATE/DELETE for all normal roles.
-- (4) No user-facing route should return raw event_json, review_record,
--     server_mac, signatures or internal reviewer IDs.
-- (5) Secure signer's key rotation, RLS policy tests, migration review and
--     fresh DEV signed two-shop negative verification required before deploy.
