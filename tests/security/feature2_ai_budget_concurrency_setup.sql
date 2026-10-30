-- Committed fixtures exclusively in CI's disposable Supabase Postgres.
-- The companion Python test pins localhost:54322 and opt-in marker to avoid
-- accidentally running against any hosted DEV/PROD instance.
\set ON_ERROR_STOP on
select 'public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid)'::regprocedure;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values('f2a00000-0000-4000-8000-000000000011',
       '00000000-0000-0000-0000-000000000000',
       'authenticated','authenticated',
       'f2-ai-budget-race-owner@example.invalid','!',now(),now());

begin;
set local role authenticated;
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f2a00000-0000-4000-8000-000000000011","is_anonymous":false}',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f2b00000-0000-4000-8000-000000000011',
       'f2a00000-0000-4000-8000-000000000011',
       'Disposable concurrent AI budget shop','f2-ai-budget-race-ci');
commit;

-- For synthetic security testing ONLY: a service-owned STARTER fixture with
-- a USD0.004 operator-style cap forces contention between two USD0.003 calls.
select set_config('request.jwt.claims',
 '{"role":"service_role","sub":"f2a00000-0000-4000-8000-000000000011"}',false);
update public.shop_subscriptions
set plan_code='STARTER', status='ACTIVE',
    valid_from=now()-interval '1 minute',
    valid_until=now()+interval '1 hour',
    period_start=now()-interval '1 minute',
    period_end=now()+interval '1 hour'
where shop_id='f2b00000-0000-4000-8000-000000000011';
insert into public.shop_ai_budget_controls(shop_id,enabled,period_cap_usd,approved_until)
values('f2b00000-0000-4000-8000-000000000011',true,0.004,
       now()+interval '1 hour');
do $$
begin
  if (select count(*) from public.shop_ai_spend_reservations
     where shop_id='f2b00000-0000-4000-8000-000000000011')<>0 then
    raise exception 'Budget race fixture had preexisting reservations';
  end if;
end $$;
\echo 'FEATURE2_AI_BUDGET_RACE_SETUP=PASS (disposable CI only)'
