-- RetailGrowthAI-only tenant-scoped browser-observed feature-test receipts.
-- Additive SOURCE ONLY until an independently authorized DEV release applies this migration.
-- NOT a server-side audit trail: user-controlled receipts and subjective quality reviews.
begin;
create table public.feature_test_runs(
  id uuid primary key,
  shop_id uuid not null references public.shops(id) on delete cascade,
  created_by uuid not null references auth.users(id) on delete cascade,
  prompt text not null check(length(trim(prompt)) between 10 and 1500),
  mode text not null check(mode in ('prompt','campaign','campaign_reel')),
  created_at timestamptz not null default now(),
  unique(shop_id,id)
);
create index feature_test_runs_shop_recent on public.feature_test_runs(shop_id,created_at desc);
create table public.feature_test_events(
  id bigint generated always as identity primary key,
  shop_id uuid not null,
  run_id uuid not null,
  actor_user_id uuid not null references auth.users(id) on delete cascade,
  event_seq integer not null check(event_seq between 1 and 1000),
  feature text not null check(feature in ('F1','F2','F3','F4','F5','F7')),
  action text not null check(length(action) between 3 and 80),
  status text not null check(status in ('PASS','FAIL','UNKNOWN','NOT_RUN','QUALITY_REVIEW')),
  summary text not null check(length(summary) between 4 and 600),
  details jsonb not null default '{}'::jsonb check(jsonb_typeof(details)='object' and octet_length(details::text) <= 8000),
  duration_ms integer check(duration_ms is null or duration_ms between 0 and 3600000),
  created_at timestamptz not null default now(),
  foreign key(shop_id,run_id) references public.feature_test_runs(shop_id,id) on delete cascade,
  unique(shop_id,run_id,event_seq)
);
create index feature_test_events_run_sequence on public.feature_test_events(shop_id,run_id,event_seq);
alter table public.feature_test_runs enable row level security;
alter table public.feature_test_events enable row level security;
-- Only real signed-in active OWNER/EDITOR members may read and write test receipts.
-- A VIEWER, revoked user or user from another tenant has no access.
create policy feature_test_runs_read on public.feature_test_runs for select to authenticated
using(retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy feature_test_runs_insert on public.feature_test_runs for insert to authenticated
with check(created_by=(select auth.uid()) and
  retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy feature_test_events_read on public.feature_test_events for select to authenticated
using(retail_private.has_role(shop_id,array['OWNER','EDITOR']));
create policy feature_test_events_insert on public.feature_test_events for insert to authenticated
with check(actor_user_id=(select auth.uid()) and
  retail_private.has_role(shop_id,array['OWNER','EDITOR']) and
  exists(select 1 from public.feature_test_runs r where r.id=run_id and
    r.shop_id=shop_id and r.created_by=(select auth.uid())));
revoke all on public.feature_test_runs,public.feature_test_events from public,anon,authenticated;
grant select,insert on public.feature_test_runs,public.feature_test_events to authenticated;
-- For PostgREST INSERT returning representation the identity is read via SELECT grant.
-- Sequence consumption is scoped to authenticated, still subject to table RLS.
grant usage,select on sequence public.feature_test_events_id_seq to authenticated;
-- Append-only: no UPDATE or DELETE grant and no update/delete RLS policy.
comment on table public.feature_test_events is
'Browser-observed testing receipts and human opinions, NOT independent worker telemetry/audited execution.';
commit;
