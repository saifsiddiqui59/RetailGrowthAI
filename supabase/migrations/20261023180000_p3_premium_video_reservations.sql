-- Part 3 source-only additive migration. NOT authorized/applied to hosted DEV.
-- Extends the EXISTING Part 1 subscription meter. No payment provider and no
-- second billing system. All premium allowances default to ZERO (fail closed).
begin;

alter table public.shop_subscriptions
  add column premium_video_seconds integer not null default 0
    check (premium_video_seconds between 0 and 3600),
  add column premium_video_budget_usd numeric(12,4) not null default 0
    check (premium_video_budget_usd between 0 and 10000);

-- Existing rows stay operation=campaign/render with units=1.
alter table public.shop_usage_reservations
  add column units integer not null default 1 check (units between 1 and 3600);
alter table public.shop_usage_reservations
  drop constraint shop_usage_reservations_operation_check;
alter table public.shop_usage_reservations
  add constraint shop_usage_reservations_operation_check
  check (operation in ('campaign','render','premium_video'));

create table public.premium_video_jobs (
  id uuid primary key,
  shop_id uuid not null references public.shops(id) on delete cascade,
  campaign_id uuid not null references public.campaigns(id) on delete cascade,
  day_id uuid not null references public.campaign_days(id) on delete cascade,
  requested_by uuid not null references auth.users(id),
  input_asset_id uuid references public.media_assets(id),
  mode text not null check (mode in ('text','image')),
  model_id text not null check (model_id in (
    'wan2.7-t2v-2026-06-12', 'wan2.7-i2v-2026-04-25'
  )),
  resolution text not null check (resolution in ('720P','1080P')),
  seconds integer not null check (seconds between 2 and 15),
  -- Based on vendor Singapore list price, updated by reviewed migration only.
  reserved_usd numeric(12,4) not null default 0,
  idempotency_key text not null check (idempotency_key ~ '^[a-f0-9]{64}$'),
  status text not null default 'QUEUED'
    check (status in ('QUEUED','SUBMITTING','PENDING','RUNNING',
                     'IMPORTING','SUCCEEDED','FAILED','CANCELED','UNKNOWN')),
  provider_task_id text,
  output_asset_id uuid references public.media_assets(id),
  error_code text,
  attempt_token uuid,
  lease_until timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint premium_video_image_input check (
    (mode='image' and input_asset_id is not null
      and model_id='wan2.7-i2v-2026-04-25')
    or (mode='text' and input_asset_id is null
      and model_id='wan2.7-t2v-2026-06-12')
  ),
  constraint premium_video_shop_idempotency unique (shop_id,idempotency_key)
);
create index premium_video_jobs_shop_created on public.premium_video_jobs
  (shop_id,created_at desc);
create index premium_video_jobs_due on public.premium_video_jobs
  (status,lease_until) where status in ('QUEUED','PENDING','RUNNING','UNKNOWN');

alter table public.premium_video_jobs enable row level security;
revoke all on public.premium_video_jobs from public,anon,authenticated;
grant select on public.premium_video_jobs to authenticated;
grant all on public.premium_video_jobs to service_role;
create policy premium_video_job_tenant_read on public.premium_video_jobs
  for select to authenticated
  using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));

-- Atomic premium reservation, same row lock and existing ledger as Part 1.
-- Worker inserts ONLY after verified user JWT, tenant rights and asset provenance.
-- Enforced again here; no TRIAL or other existing shop can use the paid provider.
create function retail_private.reserve_premium_video()
returns trigger language plpgsql security definer set search_path=''
as $$
declare
  sub public.shop_subscriptions%rowtype;
  used_seconds bigint;
  used_usd numeric(12,4);
  amount numeric(12,4);
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'Backend-only premium reservation' using errcode='42501';
  end if;
  if new.status <> 'QUEUED' or new.provider_task_id is not null
    or new.output_asset_id is not null or new.attempt_token is not null then
    raise exception 'Invalid initial premium job' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=new.shop_id and m.user_id=new.requested_by
      and m.active and m.role in ('OWNER','EDITOR')
  ) then
    raise exception 'Active tenant write role required' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.campaign_days d
      join public.campaigns c on c.id=d.campaign_id
    where d.id=new.day_id and d.campaign_id=new.campaign_id
      and d.shop_id=new.shop_id and c.shop_id=new.shop_id
      and c.status='DRAFT' and d.review_status <> 'REJECTED'
  ) then
    raise exception 'Invalid reviewed campaign day' using errcode='42501';
  end if;
  if new.mode='image' and not exists (
    select 1 from public.media_assets a
    where a.id=new.input_asset_id and a.shop_id=new.shop_id
      and a.mime_type in ('image/png','image/jpeg','image/webp')
  ) then
    raise exception 'Invalid tenant image' using errcode='42501';
  end if;
  select * into sub from public.shop_subscriptions s
    where s.shop_id=new.shop_id for update;
  if not found or sub.status<>'ACTIVE' or sub.plan_code='TRIAL'
     or now() < sub.valid_from or now() >= sub.valid_until
     or now() < sub.period_start or now() >= sub.period_end
     or sub.premium_video_seconds=0 or sub.premium_video_budget_usd=0 then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001';
  end if;
  if exists (
    select 1 from public.premium_video_jobs j
    where j.shop_id=new.shop_id and j.idempotency_key=new.idempotency_key
  ) then
    raise exception 'Already reserved premium request' using errcode='23505';
  end if;
  amount := (new.seconds * (case when new.resolution='720P'
                                  then 0.1000 else 0.1500 end));
  select coalesce(sum(u.units),0) into used_seconds
    from public.shop_usage_reservations u
    where u.shop_id=new.shop_id and u.period_start=sub.period_start
      and u.operation='premium_video';
  select coalesce(sum(j.reserved_usd),0) into used_usd
    from public.premium_video_jobs j
    join public.shop_usage_reservations u on u.shop_id=j.shop_id
      and u.job_id=j.id and u.operation='premium_video'
      and u.period_start=sub.period_start
    where j.shop_id=new.shop_id;
  if used_seconds + new.seconds > sub.premium_video_seconds
     or used_usd + amount > sub.premium_video_budget_usd then
    raise exception 'QUOTA_EXCEEDED' using errcode='RG002';
  end if;
  new.reserved_usd:=amount;
  insert into public.shop_usage_reservations
    (shop_id,operation,job_id,period_start,units)
  values (new.shop_id,'premium_video',new.id,sub.period_start,new.seconds);
  return new;
end
$$;
revoke all on function retail_private.reserve_premium_video()
  from public,anon,authenticated;
create trigger premium_job_reserve before insert on public.premium_video_jobs
  for each row execute function retail_private.reserve_premium_video();

-- A user (including a shop OWNER) can inspect their own job but cannot
-- edit allowance, forge reservations, change providers, or inject task URLs.
-- Existing premium ledger is still OWNER-only, unchanged by this migration.
commit;
