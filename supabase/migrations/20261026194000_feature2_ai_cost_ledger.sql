-- RetailGrowthAI Feature2 AI cost approval ledger, versioned source migration: hosted DEV apply requires protected approval.
-- No default paid inference: new shops receive no budget approval. No client writes.
-- Serializes AI reservations against the existing shop_subscriptions row lock.
begin;

create table public.shop_ai_budget_controls (
  shop_id uuid primary key references public.shops(id) on delete cascade,
  enabled boolean not null default false,
  period_cap_usd numeric(10,6) not null default 0
    check (period_cap_usd >= 0 and period_cap_usd <= 10),
  approved_until timestamptz,
  approved_at timestamptz not null default now()
);

create table public.shop_ai_spend_reservations (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  request_id uuid not null,
  actor_id uuid not null references auth.users(id),
  operation text not null check (operation in ('prompt','campaign_copy')),
  period_start timestamptz not null,
  reserved_usd numeric(10,6) not null check (reserved_usd > 0 and reserved_usd <= 0.05),
  actual_usd numeric(10,6) check (actual_usd >= 0),
  state text not null default 'RESERVED' check (state in ('RESERVED','SETTLED')),
  created_at timestamptz not null default now(),
  constraint ai_unique_request_per_shop unique(shop_id,request_id),
  constraint ai_settlement_consistent check (
    (state='RESERVED' and actual_usd is null) or
    (state='SETTLED' and actual_usd is not null and actual_usd <= reserved_usd)
  )
);
create index shop_ai_spend_period
on public.shop_ai_spend_reservations (shop_id,period_start,state);

alter table public.shop_ai_budget_controls enable row level security;
alter table public.shop_ai_spend_reservations enable row level security;
revoke all on public.shop_ai_budget_controls from public,anon,authenticated;
revoke all on public.shop_ai_spend_reservations from public,anon,authenticated;
grant all on public.shop_ai_budget_controls to service_role;
grant all on public.shop_ai_spend_reservations to service_role;
-- Deliberately no permissive RLS policies: no user can mint billing rights.

create function public.feature2_reserve_ai_budget(
  p_shop_id uuid, p_actor_id uuid, p_operation text, p_upper_cost_usd numeric, p_request_id uuid)
returns uuid language plpgsql security definer set search_path = ''
as $$
declare
  sub public.shop_subscriptions%rowtype;
  approval public.shop_ai_budget_controls%rowtype;
  usage_usd numeric(10,6);
  used_count integer;
  max_count integer;
  new_reservation uuid;
  bounded_cost numeric(10,6);
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'Backend AI budget authorization required' using errcode='42501';
  end if;
  if p_shop_id is null or p_actor_id is null or p_request_id is null
     or p_operation not in ('prompt','campaign_copy')
     or p_upper_cost_usd is null or p_upper_cost_usd <= 0
     or p_upper_cost_usd > 0.05 then
    raise exception 'Invalid Feature2 AI budget request' using errcode='22023';
  end if;
  bounded_cost := pg_catalog.ceil(p_upper_cost_usd * 1000000) / 1000000;
  if bounded_cost <= 0 or bounded_cost > 0.05 then
    raise exception 'Invalid rounded AI cost' using errcode='22023';
  end if;
  -- The trusted server passes the JWT-verified actor. RLS-independent
  -- membership is checked again in SQL; no client-provided actor is trusted.
  if not exists (
    select 1 from public.shop_memberships m where m.shop_id=p_shop_id
      and m.user_id=p_actor_id and m.active and m.role in ('OWNER','EDITOR')
  ) then
    raise exception 'Active shop author permission required' using errcode='42501';
  end if;
  select * into sub from public.shop_subscriptions s
  where s.shop_id=p_shop_id for update;
  if not found or sub.status not in ('TRIAL','ACTIVE')
     or now()<sub.valid_from or now()>=sub.valid_until
     or now()<sub.period_start or now()>=sub.period_end then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001';
  end if;
  select * into approval from public.shop_ai_budget_controls b
  where b.shop_id=p_shop_id for update;
  if not found or not approval.enabled
     or approval.approved_until is null or now()>=approval.approved_until
     or approval.period_cap_usd<=0 then
    raise exception 'AI_COST_NOT_APPROVED' using errcode='RG003';
  end if;
  if exists (select 1 from public.shop_ai_spend_reservations r
             where r.shop_id=p_shop_id and r.request_id=p_request_id) then
    raise exception 'AI_REQUEST_ALREADY_RESERVED' using errcode='RG005';
  end if;
  max_count := case when sub.plan_code='TRIAL' then 1
                    when sub.plan_code='STARTER' then 15
                    when sub.plan_code='GROWTH' then 80
                    when sub.plan_code='BUSINESS' then 200
                    else 0 end;
  select coalesce(sum(case when r.state='SETTLED' then r.actual_usd
                           else r.reserved_usd end),0),
         count(*)
    into usage_usd,used_count
    from public.shop_ai_spend_reservations r
   where r.shop_id=p_shop_id and r.period_start=sub.period_start;
  if used_count>=max_count or
     usage_usd+bounded_cost>approval.period_cap_usd then
    raise exception 'AI_QUOTA_EXCEEDED' using errcode='RG004';
  end if;
  insert into public.shop_ai_spend_reservations
    (shop_id,request_id,actor_id,operation,period_start,reserved_usd)
  values(p_shop_id,p_request_id,p_actor_id,p_operation,sub.period_start,bounded_cost)
  returning id into new_reservation;
  return new_reservation;
end
$$;
revoke all on function public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid)
  from public,anon,authenticated;
grant execute on function public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid)
  to service_role;

create function public.feature2_settle_ai_budget(
  p_reservation_id uuid, p_actual_usd numeric)
returns boolean language plpgsql security definer set search_path = ''
as $$
declare
  current_row public.shop_ai_spend_reservations%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'Backend AI budget settlement required' using errcode='42501';
  end if;
  select * into current_row from public.shop_ai_spend_reservations
  where id=p_reservation_id for update;
  if not found or p_actual_usd is null or p_actual_usd<0
     or p_actual_usd>current_row.reserved_usd then
    raise exception 'Invalid or over-budget AI settlement' using errcode='22023';
  end if;
  if current_row.state='SETTLED' then
    return current_row.actual_usd=p_actual_usd;
  end if;
  update public.shop_ai_spend_reservations
     set actual_usd=p_actual_usd,state='SETTLED'
   where id=p_reservation_id and state='RESERVED';
  return found;
end
$$;
revoke all on function public.feature2_settle_ai_budget(uuid,numeric)
  from public,anon,authenticated;
grant execute on function public.feature2_settle_ai_budget(uuid,numeric)
  to service_role;
commit;
