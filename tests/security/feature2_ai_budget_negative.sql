-- Feature2 canonical AI ledger acceptance, strictly CI disposable PostgreSQL.
-- CI has applied canonical migrations only in the disposable DB.
-- This file has no effect on persistent data: every fixture rolls back.
\set ON_ERROR_STOP on
begin;

do $preflight$
begin
  if to_regclass('public.shop_ai_budget_controls') is null or
     to_regclass('public.shop_ai_spend_reservations') is null then
    raise exception 'Feature2 AI canonical cost schema missing in disposable DB';
  end if;
  if has_table_privilege('anon','public.shop_ai_budget_controls','SELECT') or
     has_table_privilege('authenticated','public.shop_ai_budget_controls','INSERT') or
     has_table_privilege('authenticated','public.shop_ai_spend_reservations','SELECT') or
     has_table_privilege('authenticated','public.shop_ai_spend_reservations','INSERT') or
     has_table_privilege('authenticated','public.shop_ai_spend_reservations','UPDATE') then
    raise exception 'Browser role can see/forge AI spend or approve budget';
  end if;
  if has_function_privilege('anon','public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid)','EXECUTE') or
     has_function_privilege('authenticated','public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid)','EXECUTE') or
     has_function_privilege('authenticated','public.feature2_settle_ai_budget(uuid,numeric)','EXECUTE') or
     not has_function_privilege('service_role','public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid)','EXECUTE') then
    raise exception 'Cost RPC is not strict service-role only';
  end if;
  if (select count(*) from pg_catalog.pg_proc p
        join pg_catalog.pg_namespace n on n.oid=p.pronamespace
        where n.nspname='public' and
          p.proname in ('feature2_reserve_ai_budget','feature2_settle_ai_budget')
          and p.prosecdef and p.provolatile='v'
          and exists (select 1 from pg_catalog.unnest(p.proconfig) as cfg(setting)
           where pg_catalog.split_part(cfg.setting,'=',1)='search_path'
             and pg_catalog.btrim(pg_catalog.split_part(cfg.setting,'=',2),'"')=''))<>2 then
    raise exception 'Missing volatile security definer or isolated search path';
  end if;
end
$preflight$;

insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('f2a00000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','f2-ai-budget-owner@example.invalid','!',now(),now()),
('f2a00000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','f2-ai-budget-viewer@example.invalid','!',now(),now()),
('f2a00000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','f2-ai-budget-foreign@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f2a00000-0000-4000-8000-000000000001","is_anonymous":false}',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f2b00000-0000-4000-8000-000000000001',
       'f2a00000-0000-4000-8000-000000000001',
       'Isolated AI budget test shop','f2-ai-budget-negative-ci');
insert into public.shop_memberships(shop_id,user_id,role)
values('f2b00000-0000-4000-8000-000000000001',
       'f2a00000-0000-4000-8000-000000000002','VIEWER');
do $public_denied$
begin
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000001','prompt',0.001,'f2d00000-0000-4000-8000-000000000001');
    raise exception 'Authenticated user executed privileged spend RPC';
  exception when insufficient_privilege then null;
  end;
  begin
    insert into public.shop_ai_budget_controls(shop_id,enabled,period_cap_usd)
    values('f2b00000-0000-4000-8000-000000000001',true,10);
    raise exception 'Authenticated user created its own spending budget';
  exception when insufficient_privilege then null;
  end;
end
$public_denied$;
reset role;
-- The backend service role alone owns approval rows and can reserve costs.
select set_config('request.jwt.claims',
 '{"role":"service_role","sub":"f2a00000-0000-4000-8000-000000000001"}',true);
set local role service_role;
do $disabled$
begin
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000001','prompt',0.001,'f2d00000-0000-4000-8000-000000000001');
    raise exception 'No approved budget unexpectedly enabled a paid model';
  exception when sqlstate 'RG003' then null;
  end;
end
$disabled$;

insert into public.shop_ai_budget_controls(shop_id,enabled,period_cap_usd,approved_until)
values('f2b00000-0000-4000-8000-000000000001',false,0.005,now()+interval '30 minutes');

do $disabled_row$
begin
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000001','prompt',0.001,'f2d00000-0000-4000-8000-000000000001');
    raise exception 'Explicit disabled budget row permitted paid inference';
  exception when sqlstate 'RG003' then null;
  end;
end
$disabled_row$;
update public.shop_ai_budget_controls set enabled=true
 where shop_id='f2b00000-0000-4000-8000-000000000001';

do $denied_actors$
begin
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000002','prompt',0.001,'f2d00000-0000-4000-8000-000000000001');
    raise exception 'VIEWER was permitted to spend tenant budget';
  exception when insufficient_privilege then null;
  end;
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000003','prompt',0.001,'f2d00000-0000-4000-8000-000000000001');
    raise exception 'Foreign actor was permitted to spend tenant budget';
  exception when insufficient_privilege then null;
  end;
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000001','unknown',0.001,'f2d00000-0000-4000-8000-000000000001');
    raise exception 'Unknown operation reached model ledger';
  exception when invalid_parameter_value then null;
  end;
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000001','prompt',0.051,'f2d00000-0000-4000-8000-000000000001');
    raise exception 'Over-USD0.05 attempt bypassed hard cap';
  exception when invalid_parameter_value then null;
  end;
end
$denied_actors$;

-- An *approved* real budget consumes a single atomic reservation.
create temp table feature2_test_receipt (id uuid) on commit drop;
insert into feature2_test_receipt
 select public.feature2_reserve_ai_budget(
   'f2b00000-0000-4000-8000-000000000001',
   'f2a00000-0000-4000-8000-000000000001','prompt',0.003,'f2d00000-0000-4000-8000-000000000001');

do $settlement$
declare
 receipt uuid;
begin
  select id into receipt from feature2_test_receipt;
  if receipt is null then raise exception 'Atomic reservation returned NULL'; end if;
  if not public.feature2_settle_ai_budget(receipt,0.002) then
    raise exception 'Provider token charge settlement returned false';
  end if;
  if not public.feature2_settle_ai_budget(receipt,0.002) then
    raise exception 'Idempotent same-cost settlement unexpectedly failed';
  end if;
  if public.feature2_settle_ai_budget(receipt,0.001) then
    raise exception 'Different-cost settlement was not rejected';
  end if;
  begin
    perform public.feature2_settle_ai_budget(receipt,0.004);
    raise exception 'Provider charge exceeded reserved max';
  exception when invalid_parameter_value then null;
  end;
  if (select actual_usd from public.shop_ai_spend_reservations where id=receipt)<>0.002 then
    raise exception 'Incorrect settled actual cost';
  end if;
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000001','prompt',0.003,'f2d00000-0000-4000-8000-000000000001');
    raise exception 'Same request nonce was permitted to bill twice';
  exception when sqlstate 'RG005' then null;
  end;
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000001','prompt',0.001,'f2d00000-0000-4000-8000-000000000002');
    raise exception 'Trial quota permitted second model request despite used-count';
  exception when sqlstate 'RG004' then null;
  end;
end
$settlement$;

update public.shop_ai_budget_controls set approved_until=now()-interval '1 second'
where shop_id='f2b00000-0000-4000-8000-000000000001';
do $expired$
begin
  begin
    perform public.feature2_reserve_ai_budget(
      'f2b00000-0000-4000-8000-000000000001',
      'f2a00000-0000-4000-8000-000000000001','campaign_copy',0.001,'f2d00000-0000-4000-8000-000000000001');
    raise exception 'Expired budget silently reactivated';
  exception when sqlstate 'RG003' then null;
  end;
end
$expired$;

rollback;
\echo 'FEATURE2_AI_BUDGET_POSTGRES_DENIAL_SETTLEMENT=PASS (disposable CI only)'
