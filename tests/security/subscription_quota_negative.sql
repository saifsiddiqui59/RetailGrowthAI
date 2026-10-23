-- ONLY CI's disposable Supabase database. Never a hosted RetailGrowthAI project.
-- Prove tenant isolation, automatic trial, atomic job metering, and expiry.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('eb000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000',
'authenticated','authenticated','quota-owner@example.invalid','!',now(),now()),
('eb000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000',
'authenticated','authenticated','quota-foreign@example.invalid','!',now(),now());
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','eb000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug) values
('eb000000-0000-4000-8000-000000000011','eb000000-0000-4000-8000-000000000001',
'Quota owner shop','rg-quota-test-owner');
do $$
declare rows int;
begin
  select count(*) into rows from public.shop_subscriptions
  where shop_id='eb000000-0000-4000-8000-000000000011'
    and plan_code='TRIAL' and status='TRIAL'
    and valid_until>now()+interval '6 days'
    and valid_until<=now()+interval '8 days';
  if rows<>1 then raise exception 'FAIL: automatic seven-day trial missing'; end if;
  begin
    update public.shop_subscriptions set plan_code='BUSINESS'
    where shop_id='eb000000-0000-4000-8000-000000000011';
    raise exception 'FAIL: authenticated trial upgraded without service authority';
  exception when insufficient_privilege then null;
  end;
  begin
    insert into public.shop_usage_reservations(shop_id,operation,job_id,period_start)
    values('eb000000-0000-4000-8000-000000000011','campaign',
      'eb000000-0000-4000-8000-000000000999',now());
    raise exception 'FAIL: authenticated forged usage counter';
  exception when insufficient_privilege then null;
  end;
end $$;
-- Two new campaign reservations, but a third unique campaign must be refused.
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values
('eb000000-0000-4000-8000-000000000021',
 'eb000000-0000-4000-8000-000000000011',
 'eb000000-0000-4000-8000-000000000001','First metered campaign','2026-11-01'),
('eb000000-0000-4000-8000-000000000022',
 'eb000000-0000-4000-8000-000000000011',
 'eb000000-0000-4000-8000-000000000001','Second metered campaign','2026-11-01');
do $$
declare meter int;
begin
  select count(*) into meter from public.shop_usage_reservations
  where shop_id='eb000000-0000-4000-8000-000000000011'
    and operation='campaign';
  if meter<>2 then raise exception 'FAIL: campaign quota reservation count %',meter; end if;
  begin
    insert into public.campaigns(id,shop_id,created_by,brief,start_date)
    values('eb000000-0000-4000-8000-000000000023',
      'eb000000-0000-4000-8000-000000000011',
      'eb000000-0000-4000-8000-000000000001','Third exhausted campaign','2026-11-01');
    raise exception 'FAIL: campaign quota exhaustion bypassed';
  exception when sqlstate 'RG002' then null;
  end;
  select count(*) into meter from public.shop_usage_reservations
  where shop_id='eb000000-0000-4000-8000-000000000011'
    and operation='campaign';
  if meter<>2 then raise exception 'FAIL: denied campaign consumed extra quota'; end if;
end $$;
-- Non-owner cannot read another shop's server-owned entitlement or counters.
select set_config('request.jwt.claim.sub','eb000000-0000-4000-8000-000000000002',true);
do $$
begin
  if exists(select 1 from public.shop_subscriptions
     where shop_id='eb000000-0000-4000-8000-000000000011')
   or exists(select 1 from public.shop_usage_reservations
     where shop_id='eb000000-0000-4000-8000-000000000011')
  then raise exception 'FAIL: foreign shop quota RLS leak'; end if;
end $$;
-- Make one day under trusted service identity and exercise the *separate*
-- rendering allowance. A service role may not bypass actor shop membership.
reset role;
select set_config('request.jwt.claim.role','service_role',true);
set local role service_role;
insert into public.campaign_days
(id,campaign_id,shop_id,day_index,scheduled_date,topic)
values ('eb000000-0000-4000-8000-000000000031',
 'eb000000-0000-4000-8000-000000000021',
 'eb000000-0000-4000-8000-000000000011',
 1,'2026-11-01','Quota fixture');
insert into public.render_jobs(id,shop_id,campaign_id,day_id,requested_by,preset,idempotency_key)
values
('eb000000-0000-4000-8000-000000000041',
 'eb000000-0000-4000-8000-000000000011',
 'eb000000-0000-4000-8000-000000000021',
 'eb000000-0000-4000-8000-000000000031',
 'eb000000-0000-4000-8000-000000000001','instagram_reel_30s','quota-render-one'),
('eb000000-0000-4000-8000-000000000042',
 'eb000000-0000-4000-8000-000000000011',
 'eb000000-0000-4000-8000-000000000021',
 'eb000000-0000-4000-8000-000000000031',
 'eb000000-0000-4000-8000-000000000001','instagram_reel_30s','quota-render-two');
do $$
declare meter int;
begin
  select count(*) into meter from public.shop_usage_reservations
  where shop_id='eb000000-0000-4000-8000-000000000011'
    and operation='render';
  if meter<>2 then raise exception 'FAIL: render allowance count %',meter; end if;
  begin
    insert into public.render_jobs(id,shop_id,campaign_id,day_id,requested_by,preset,idempotency_key)
    values('eb000000-0000-4000-8000-000000000043',
      'eb000000-0000-4000-8000-000000000011',
      'eb000000-0000-4000-8000-000000000021',
      'eb000000-0000-4000-8000-000000000031',
      'eb000000-0000-4000-8000-000000000001',
      'instagram_reel_30s','quota-render-three');
    raise exception 'FAIL: render quota exhaustion bypassed';
  exception when sqlstate 'RG002' then null;
  end;
  if (select count(*) from public.shop_usage_reservations
      where shop_id='eb000000-0000-4000-8000-000000000011'
      and operation='render')<>2 then
    raise exception 'FAIL: denied render consumed quota';
  end if;
  begin
    insert into public.render_jobs(id,shop_id,campaign_id,day_id,requested_by,preset,idempotency_key)
    values('eb000000-0000-4000-8000-000000000044',
      'eb000000-0000-4000-8000-000000000011',
      'eb000000-0000-4000-8000-000000000021',
      'eb000000-0000-4000-8000-000000000031',
      'eb000000-0000-4000-8000-000000000002',
      'instagram_reel_30s','forged-other-actor');
    raise exception 'FAIL: foreign actor reservation bypass';
  exception when insufficient_privilege then null;
  end;
end $$;
-- Only service-owned administration can expire plans; expiry blocks new jobs.
update public.shop_subscriptions set
valid_from=now()-interval '8 days',
valid_until=now()-interval '1 minute',
period_start=now()-interval '8 days',
period_end=now()-interval '1 minute'
where shop_id='eb000000-0000-4000-8000-000000000011';
reset role;
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
select set_config('request.jwt.claim.sub','eb000000-0000-4000-8000-000000000001',true);
do $$
begin
  begin
    insert into public.campaigns(id,shop_id,created_by,brief,start_date)
    values('eb000000-0000-4000-8000-000000000024',
      'eb000000-0000-4000-8000-000000000011',
      'eb000000-0000-4000-8000-000000000001','Expired shop','2026-11-01');
    raise exception 'FAIL: expired trial still spends AI credits';
  exception when sqlstate 'RG001' then null;
  end;
end $$;
rollback;
\echo 'PASS subscription auto trial, OWNER RLS, denied forged upgrade/counters/tenant, atomic campaign/render quotas and expiry'
