-- RetailGrowthAI Part 2 publishing quota, STAGED SOURCE ONLY. NOT HOSTED.
-- Apply only after approved P2 foundations and independent owner approval.
-- No default publish allowance: the operator must explicitly approve plan caps.
begin;

create table retail_private.social_publish_plan_limits (
  plan_code text primary key
    check (plan_code in ('TRIAL','STARTER','GROWTH','BUSINESS')),
  max_posts_per_period integer not null check (max_posts_per_period between 1 and 10000),
  approved_at timestamptz not null default now()
);
-- Intentionally EMPTY. Do not infer publishing credits from P1 campaign/render caps.
alter table retail_private.social_publish_plan_limits enable row level security;
revoke all on retail_private.social_publish_plan_limits from public,anon,authenticated;
grant select,insert,update,delete on retail_private.social_publish_plan_limits to service_role;

-- Serializes all concurrent publishing reservations for one shop by locking
-- the authoritative P1 subscription row. No browser/user token may execute it.
-- The already unique ledger PK (publish_job_id) makes retries idempotent.
create function public.p2_reserve_social_publish_quota(p_shop uuid,p_job uuid)
returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  s public.shop_subscriptions%rowtype;
  cap integer;
  used_units integer;
  ledger_period timestamptz;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service role required' using errcode='42501';
  end if;

  select * into j from public.social_publish_jobs
    where id=p_job and shop_id=p_shop for update;
  if not found or j.status not in ('APPROVED','QUEUED','RETRYABLE')
      or j.approved_by is null or j.approved_at is null
      or j.approved_content_sha256 is null
      or octet_length(j.approved_content_sha256)<>32 then
    return false;
  end if;
  -- Role recheck at reservation time: an old approval from a removed editor
  -- cannot silently spend a current business subscription.
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=j.approved_by
      and m.active and m.role in ('OWNER','EDITOR')
  ) then
    return false;
  end if;
  if not exists (
    select 1 from public.social_accounts a
    where a.id=j.social_account_id and a.shop_id=p_shop
      and a.provider=j.provider and a.connection_status='CONNECTED'
  ) then
    return false;
  end if;

  select * into s from public.shop_subscriptions
    where shop_id=p_shop for update;
  if not found or s.status not in ('TRIAL','ACTIVE')
     or now()<s.valid_from or now()>=s.valid_until
     or now()<s.period_start or now()>=s.period_end then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001';
  end if;
  select l.max_posts_per_period into cap
    from retail_private.social_publish_plan_limits l
    where l.plan_code=s.plan_code;
  if cap is null then
    -- No hardcoded or fabricated trial/paid publish quota. Disabled by default.
    raise exception 'SOCIAL_PUBLISH_QUOTA_NOT_APPROVED' using errcode='RG001';
  end if;

  select period_start into ledger_period
    from retail_private.social_publish_quota_ledger
    where publish_job_id=p_job;
  if found then
    return ledger_period=s.period_start;
  end if;
  select count(*) into used_units
    from retail_private.social_publish_quota_ledger l
    where l.shop_id=p_shop and l.period_start=s.period_start;
  if used_units>=cap then
    raise exception 'SOCIAL_PUBLISH_QUOTA_EXCEEDED' using errcode='RG002';
  end if;
  insert into retail_private.social_publish_quota_ledger(
    publish_job_id,shop_id,period_start)
  values(p_job,p_shop,s.period_start);
  insert into public.social_publish_audit(
    shop_id,job_id,actor_user_id,event_code)
  values(p_shop,p_job,j.approved_by,'SOCIAL_QUOTA_RESERVED');
  return true;
end
$$;

revoke all on function public.p2_reserve_social_publish_quota(uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_reserve_social_publish_quota(uuid,uuid)
  to service_role;
commit;
