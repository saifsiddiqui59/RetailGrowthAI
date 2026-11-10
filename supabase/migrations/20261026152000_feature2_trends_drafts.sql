-- Feature #2 additive schema after approved RetailGrowthAI migrations.
-- Source-only until DEV rollout is explicitly verified; never apply to PROD.
-- Shared signals are service-only; retailer content remains tenant-RLS scoped.
begin;

create table public.trend_collection_claims (
  region text not null check (region = 'IN'),
  utc_day date not null,
  lease_token uuid not null default gen_random_uuid(),
  lease_until timestamptz not null,
  attempts integer not null default 1 check (attempts between 1 and 3),
  state text not null default 'CLAIMED' check (state in ('CLAIMED','FINISHED')),
  primary key(region,utc_day)
);
create table public.trend_snapshots (
  region text not null check (region = 'IN'),
  utc_day date not null,
  snapshot jsonb not null check (
    jsonb_typeof(snapshot) = 'object'
    and jsonb_typeof(snapshot->'trends') = 'array'
    and jsonb_typeof(snapshot->'sources') = 'array'
    and pg_column_size(snapshot) <= 250000
  ),
  observed_at timestamptz not null,
  expires_at timestamptz not null,
  primary key(region,utc_day),
  check(expires_at > observed_at)
);
create index trend_snapshots_recent on public.trend_snapshots(region,utc_day desc);

alter table public.trend_collection_claims enable row level security;
alter table public.trend_snapshots enable row level security;
revoke all on public.trend_collection_claims,public.trend_snapshots from public,anon,authenticated;
grant select,insert,update on public.trend_collection_claims,public.trend_snapshots to service_role;
-- No anonymous or authenticated policies: public trends are read via verified
-- shop membership server-side, not via an unrestricted public REST table.

create function public.feature2_claim_collection(p_region text,p_day date)
returns uuid language plpgsql volatile security invoker set search_path=''
as $$
declare
  token uuid;
begin
  if p_region <> 'IN' or p_day <> (now() at time zone 'UTC')::date then
    raise exception 'invalid collection day' using errcode='22023';
  end if;
  insert into public.trend_collection_claims(region,utc_day,lease_token,lease_until,attempts,state)
  values(p_region,p_day,gen_random_uuid(),now()+interval '10 minutes',1,'CLAIMED')
  on conflict(region,utc_day) do update
    set lease_token=gen_random_uuid(),lease_until=now()+interval '10 minutes',
        attempts=public.trend_collection_claims.attempts+1,state='CLAIMED'
    where public.trend_collection_claims.state='CLAIMED'
      and public.trend_collection_claims.lease_until<now()
      and public.trend_collection_claims.attempts<3
  returning lease_token into token;
  return token; -- null on duplicate, completed or unexpired claim
end;
$$;
revoke all on function public.feature2_claim_collection(text,date) from public,anon,authenticated;
grant execute on function public.feature2_claim_collection(text,date) to service_role;

create function public.feature2_finish_collection(
  p_region text,p_day date,p_token uuid,p_snapshot jsonb
) returns boolean language plpgsql volatile security invoker set search_path=''
as $$
declare
  fenced integer;
begin
  if p_region <> 'IN' or p_day <> (now() at time zone 'UTC')::date
     or jsonb_typeof(p_snapshot) <> 'object'
     or jsonb_typeof(p_snapshot->'trends') <> 'array'
     or jsonb_typeof(p_snapshot->'sources') <> 'array'
     or pg_column_size(p_snapshot)>250000
     or (p_snapshot->>'observed_at')::timestamptz > now()+interval '5 minutes'
     or (p_snapshot->>'observed_at')::timestamptz < now()-interval '1 hour'
  then raise exception 'invalid snapshot' using errcode='22023'; end if;

  update public.trend_collection_claims
    set state='FINISHED'
    where region=p_region and utc_day=p_day and lease_token=p_token
      and state='CLAIMED' and lease_until>now();
  get diagnostics fenced = row_count;
  if fenced<>1 then return false; end if;

  insert into public.trend_snapshots(region,utc_day,snapshot,observed_at,expires_at)
    values(p_region,p_day,p_snapshot,(p_snapshot->>'observed_at')::timestamptz,
           (p_snapshot->>'observed_at')::timestamptz + interval '30 hours')
    on conflict(region,utc_day) do update
    set snapshot=excluded.snapshot,observed_at=excluded.observed_at,
        expires_at=excluded.expires_at;
  return true;
end;
$$;
revoke all on function public.feature2_finish_collection(text,date,uuid,jsonb)
  from public,anon,authenticated;
grant execute on function public.feature2_finish_collection(text,date,uuid,jsonb)
  to service_role;

create table public.shop_content_drafts (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  created_by uuid not null references auth.users(id),
  trend_id text not null check (trend_id ~ '^[a-f0-9]{32}$'),
  content jsonb not null check (
    jsonb_typeof(content)='object'
    and content->'review'->>'status'='DRAFT'
    and content->'review'->>'can_publish'='false'
    and pg_column_size(content)<=200000
  ),
  review_state text not null default 'DRAFT' check (review_state='DRAFT'),
  created_at timestamptz not null default now()
);
create index shop_content_drafts_recent on public.shop_content_drafts(shop_id,created_at desc);
alter table public.shop_content_drafts enable row level security;
revoke all on public.shop_content_drafts from public,anon,authenticated;
grant select on public.shop_content_drafts to authenticated;
grant select,insert on public.shop_content_drafts to service_role;
create policy feature2_draft_read on public.shop_content_drafts
  for select to authenticated
  using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']::text[]));
-- No authenticated INSERT: a direct client could forge trend evidence.
-- The verified backend checks JWT membership and source ID, then makes the
-- single service-role INSERT. RLS remains mandatory for tenant-facing reads.
-- No UPDATE/DELETE, no approval or publishing RPC. Human approval comes later
-- with a separately reviewed immutable version/usage contract.
commit;
