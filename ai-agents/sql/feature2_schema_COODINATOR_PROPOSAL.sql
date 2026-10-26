-- Feature #2 schema proposal for COORDINATOR REVIEW ONLY.
-- This is intentionally NOT in supabase/migrations and is NEVER auto-applied.
-- Submit as a separate migration/security PR after coordinated API freeze.
-- Reviewed RetailGrowthAI DEV only; do not touch WineShopPOS/PROD.
begin;

create table public.trend_collection_claims (
  region char(2) not null check (region = 'IN'),
  utc_day date not null,
  claimed_at timestamptz not null default now(),
  finished_at timestamptz,
  state text not null default 'CLAIMED'
    check (state in ('CLAIMED','PARTIAL','SUCCEEDED','FAILED')),
  primary key (region,utc_day)
);
create table public.trend_snapshots (
  id uuid primary key default gen_random_uuid(),
  region char(2) not null check (region = 'IN'),
  utc_day date not null,
  provider text not null check (provider in ('google_rss','youtube','festival_calendar')),
  observed_at timestamptz not null,
  expires_at timestamptz not null,
  status text not null check (status in ('ok','disabled','unavailable','quota_limited','incomplete')),
  signals jsonb not null default '[]'::jsonb
    check (jsonb_typeof(signals) = 'array' and pg_column_size(signals) <= 250000),
  created_at timestamptz not null default now(),
  unique(region,utc_day,provider),
  check (expires_at > observed_at)
);
create index trend_snapshots_region_recent on public.trend_snapshots (region,utc_day desc);

-- Global observed trend data are service-owned, never tenant-writable or
-- directly exposed via PostgREST. RLS has no anon/authenticated policies.
alter table public.trend_collection_claims enable row level security;
alter table public.trend_snapshots enable row level security;
revoke all on public.trend_collection_claims, public.trend_snapshots from public, anon, authenticated;
grant select, insert, update on public.trend_collection_claims to service_role;
grant select, insert, update on public.trend_snapshots to service_role;

create table public.shop_content_recommendations (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  campaign_id uuid,
  day_id uuid,
  trend_id text check (trend_id ~ '^[a-f0-9]{32}$'),
  trend_source text check (trend_source in ('google_rss','youtube','festival_calendar')),
  trend_observed_at timestamptz,
  evidence_url text check (evidence_url is null or length(evidence_url) <= 600),
  draft jsonb not null check (jsonb_typeof(draft) = 'object'
    and pg_column_size(draft) <= 100000),
  review_state text not null default 'DRAFT'
    check (review_state in ('DRAFT','APPROVED','REJECTED')),
  review_version int not null default 1 check (review_version > 0),
  created_by uuid not null references auth.users(id),
  reviewed_by uuid references auth.users(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  foreign key (shop_id,campaign_id) references public.campaigns(shop_id,id) on delete cascade,
  foreign key (shop_id,day_id) references public.campaign_days(shop_id,id) on delete cascade,
  check ((campaign_id is null and day_id is null) or (campaign_id is not null and day_id is not null)),
  check (review_state = 'DRAFT' or (reviewed_by is not null and reviewed_at is not null))
);
create index shop_content_recommendations_recent
  on public.shop_content_recommendations(shop_id,created_at desc);
alter table public.shop_content_recommendations enable row level security;

revoke all on public.shop_content_recommendations from public, anon, authenticated;
grant select on public.shop_content_recommendations to authenticated;
grant select, insert, update on public.shop_content_recommendations to service_role;

create policy shop_content_recommendations_read
  on public.shop_content_recommendations for select to authenticated
  using (retail_private.has_role(shop_id, array['OWNER','EDITOR','VIEWER']::text[]));

-- Users cannot insert arbitrary "verified" trend evidence or update reviews
-- directly. Approval RPC is JWT-identity-bound and version-fenced.
create function public.review_shop_content_recommendation(
  p_id uuid, p_expected_version integer, p_decision text
)
returns jsonb language plpgsql volatile security definer set search_path = ''
as $$
declare
  target public.shop_content_recommendations%rowtype;
begin
  if p_decision not in ('APPROVED','REJECTED') or p_expected_version < 1 then
    raise exception 'invalid review' using errcode='22023';
  end if;
  select * into target from public.shop_content_recommendations where id=p_id for update;
  if target.id is null or not retail_private.has_role(target.shop_id, array['OWNER','EDITOR']::text[]) then
    raise exception 'not permitted' using errcode='42501';
  end if;
  if target.review_state <> 'DRAFT' or target.review_version <> p_expected_version then
    raise exception 'stale or final review' using errcode='40001';
  end if;
  update public.shop_content_recommendations
     set review_state=p_decision, reviewed_by=(select auth.uid()), reviewed_at=now(),
         review_version=review_version+1
   where id=p_id;
  return jsonb_build_object('id',target.id, 'shop_id',target.shop_id,
                            'review_state',p_decision,'review_version',p_expected_version+1);
end;
$$;
revoke all on function public.review_shop_content_recommendation(uuid,int,text)
  from public, anon;
grant execute on function public.review_shop_content_recommendation(uuid,int,text)
  to authenticated;
commit;
