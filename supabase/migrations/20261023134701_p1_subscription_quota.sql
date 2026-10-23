-- RetailGrowthAI-only Part 1: server-owned trial and atomic plan/render quota.
-- All ten earlier versions already applied; apply this NEW version only after 4/4 CI.
-- No card payment, Razorpay, WineShopPOS or plan self-promotion.
begin;

create table public.shop_subscriptions (
  shop_id uuid primary key references public.shops(id) on delete cascade,
  plan_code text not null default 'TRIAL' check (plan_code in ('TRIAL','STARTER','GROWTH','BUSINESS')),
  status text not null default 'TRIAL' check (status in ('TRIAL','ACTIVE','SUSPENDED','EXPIRED')),
  valid_from timestamptz not null,
  valid_until timestamptz not null,
  period_start timestamptz not null,
  period_end timestamptz not null,
  created_at timestamptz not null default now(),
  constraint subscription_dates check (valid_from < valid_until and period_start < period_end),
  constraint trial_plan_status check (plan_code <> 'TRIAL' or status <> 'ACTIVE')
);
create table public.shop_usage_reservations (
  shop_id uuid not null references public.shops(id) on delete cascade,
  operation text not null check (operation in ('campaign','render')),
  job_id uuid not null,
  period_start timestamptz not null,
  reserved_at timestamptz not null default now(),
  primary key (shop_id,operation,job_id)
);
create index shop_usage_period on public.shop_usage_reservations
  (shop_id,operation,period_start);

-- Authenticated users may READ their OWN entitlement only; none can grant
-- paid status, alter periods, reset counters, or insert fake usage rows.
alter table public.shop_subscriptions enable row level security;
alter table public.shop_usage_reservations enable row level security;
revoke all on public.shop_subscriptions from public,anon,authenticated;
revoke all on public.shop_usage_reservations from public,anon,authenticated;
grant select on public.shop_subscriptions to authenticated;
grant select on public.shop_usage_reservations to authenticated;
grant all on public.shop_subscriptions to service_role;
grant all on public.shop_usage_reservations to service_role;
create policy subscription_owner_read on public.shop_subscriptions
  for select to authenticated
  using (retail_private.has_role(shop_id,array['OWNER']));
create policy subscription_usage_owner_read on public.shop_usage_reservations
  for select to authenticated
  using (retail_private.has_role(shop_id,array['OWNER']));

-- Grant seven calendar days only when a new RetailGrowthAI shop is created;
-- the initial trial cannot be forged by client-controlled profile claims.
create function retail_private.bootstrap_trial_subscription()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  insert into public.shop_subscriptions
    (shop_id,plan_code,status,valid_from,valid_until,period_start,period_end)
  values (new.id,'TRIAL','TRIAL',now(),now()+interval '7 days',
          now(),now()+interval '7 days');
  return new;
end
$$;
revoke all on function retail_private.bootstrap_trial_subscription() from public,anon,authenticated;
create trigger shop_trial_after_insert
after insert on public.shops for each row
execute function retail_private.bootstrap_trial_subscription();

-- Existing DEV shops get a trial from original shop creation (not migration day).
-- Do not overwrite service-owned entitlements if a future migration is rechecked.
insert into public.shop_subscriptions
  (shop_id,plan_code,status,valid_from,valid_until,period_start,period_end)
select id,'TRIAL','TRIAL',created_at,created_at + interval '7 days',
       created_at,created_at + interval '7 days'
from public.shops
on conflict (shop_id) do nothing;

-- Runs within the SAME transaction as campaigns/render_jobs INSERT.
-- SERIALIZES concurrent jobs for one shop by locking subscription PK row;
-- failed inserts rollback reservations. Client cannot change the quota meter.
create function retail_private.reserve_subscription_unit()
returns trigger language plpgsql security definer set search_path = ''
as $$
declare
  sub public.shop_subscriptions%rowtype;
  kind text;
  actor uuid;
  max_units integer;
  consumed integer;
  session_role text;
begin
  if tg_table_schema <> 'public' then
    raise exception 'Invalid subscription target' using errcode='42501';
  end if;
  if tg_table_name='campaigns' then
    kind:='campaign';
    actor:=new.created_by;
  elsif tg_table_name='render_jobs' then
    kind:='render';
    actor:=new.requested_by;
  else
    raise exception 'Invalid subscription target' using errcode='42501';
  end if;
  session_role:=(select auth.role());
  if session_role is distinct from 'authenticated'
     and session_role is distinct from 'service_role' then
    raise exception 'Authenticated request required' using errcode='42501';
  end if;
  if session_role='authenticated' and actor is distinct from (select auth.uid()) then
    raise exception 'Actor must match JWT' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=new.shop_id and m.user_id=actor and m.active
      and m.role in ('OWNER','EDITOR')
  ) then
    raise exception 'Active shop write role required' using errcode='42501';
  end if;
  select * into sub from public.shop_subscriptions s
  where s.shop_id=new.shop_id for update;
  if not found or sub.status not in ('TRIAL','ACTIVE')
     or now()<sub.valid_from or now()>=sub.valid_until
     or now()<sub.period_start or now()>=sub.period_end then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001';
  end if;
  max_units:=case
    when sub.plan_code='TRIAL' then 2
    when sub.plan_code='STARTER' and kind='campaign' then 15
    when sub.plan_code='STARTER' and kind='render' then 10
    when sub.plan_code='GROWTH' and kind='campaign' then 60
    when sub.plan_code='GROWTH' and kind='render' then 45
    when sub.plan_code='BUSINESS' and kind='campaign' then 200
    when sub.plan_code='BUSINESS' and kind='render' then 150
    else null end;
  if max_units is null then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001';
  end if;
  if exists (
    select 1 from public.shop_usage_reservations u where
    u.shop_id=new.shop_id and u.operation=kind and u.job_id=new.id
  ) then
    return new;
  end if;
  select count(*) into consumed from public.shop_usage_reservations u
  where u.shop_id=new.shop_id and u.operation=kind
    and u.period_start=sub.period_start;
  if consumed>=max_units then
    raise exception 'QUOTA_EXCEEDED' using errcode='RG002';
  end if;
  insert into public.shop_usage_reservations
    (shop_id,operation,job_id,period_start)
  values (new.shop_id,kind,new.id,sub.period_start);
  return new;
end
$$;
revoke all on function retail_private.reserve_subscription_unit() from public,anon,authenticated;
create trigger subscription_reserve_campaign
before insert on public.campaigns for each row
execute function retail_private.reserve_subscription_unit();
create trigger subscription_reserve_render
before insert on public.render_jobs for each row
execute function retail_private.reserve_subscription_unit();
commit;
