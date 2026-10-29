-- CI disposable Postgres ONLY. Do not run against hosted RetailGrowthAI DEV.
\set ON_ERROR_STOP on
\i supabase/release-candidates/20261029120000_feature_worker_trace_spans.sql
begin;
do $preflight$
begin
 if not (select relrowsecurity from pg_class where oid='retail_private.feature_worker_spans'::regclass)
 then raise exception 'Worker span RLS missing'; end if;
 if has_table_privilege('anon','retail_private.feature_worker_spans','SELECT') or
    has_table_privilege('authenticated','retail_private.feature_worker_spans','SELECT') or
    has_table_privilege('authenticated','retail_private.feature_worker_spans','INSERT') or
    has_function_privilege('authenticated',
      'public.retail_feature_worker_append(text,uuid,integer,text,text,integer,jsonb)','EXECUTE') or
    has_function_privilege('anon',
      'public.retail_feature_worker_spans(uuid,uuid,integer)','EXECUTE')
 then raise exception 'Worker span service-only access was exposed'; end if;
end
$preflight$;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('f8a10000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','worker-span-owner@example.invalid','!',now(),now()),
('f8a10000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','worker-span-foreign@example.invalid','!',now(),now()),
('f8a10000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','worker-span-viewer@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f8a10000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f8b10000-0000-4000-8000-000000000001',
 'f8a10000-0000-4000-8000-000000000001','Trace ledger shop','rg-worker-ledger');
insert into public.shop_memberships(shop_id,user_id,role) values(
 'f8b10000-0000-4000-8000-000000000001',
 'f8a10000-0000-4000-8000-000000000003','VIEWER');
reset role;

-- Service-only creation of a terminal factual fixture, not an actual model call.
select set_config('request.jwt.claim.role','service_role',true);
set local role service_role;
insert into public.campaigns(
 id,shop_id,created_by,brief,start_date,status,planning_attempts)
values('f8c10000-0000-4000-8000-000000000001',
 'f8b10000-0000-4000-8000-000000000001',
 'f8a10000-0000-4000-8000-000000000001',
 'Test planned text and rights evidence','2026-11-01','DRAFT',1);
insert into public.campaign_days(
 id,campaign_id,shop_id,day_index,scheduled_date,topic,linkedin,instagram)
select ('f8d10000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'f8c10000-0000-4000-8000-000000000001',
 'f8b10000-0000-4000-8000-000000000001',
 i,('2026-11-01'::date+i-1),'Outfit tip', '{}'::jsonb,'{}'::jsonb
from generate_series(1,7) as days(i);

do $success$
declare r jsonb; prior jsonb;
begin
 r:=public.retail_feature_worker_append('F2',
  'f8c10000-0000-4000-8000-000000000001',1,
  'planning.complete','SUCCEEDED',100,
  '{"planner_mode":"dev_mock","generated_days":7}');
 if r->>'persisted'<>'true' or r->>'feature'<>'F2'
 then raise exception 'Real terminal job did not create worker span'; end if;
 prior:=public.retail_feature_worker_append('F2',
  'f8c10000-0000-4000-8000-000000000001',1,
  'planning.complete','SUCCEEDED',100,
  '{"planner_mode":"dev_mock","generated_days":7}');
 if prior->>'id' is distinct from r->>'id' then
  raise exception 'Same span not idempotent'; end if;
end
$success$;

-- No caller can fabricate another operation for the same terminal DRAFT.
do $service_denials$
declare denied boolean;
begin
 denied:=false;
 begin
  perform public.retail_feature_worker_append('F2',
   'f8c10000-0000-4000-8000-000000000001',2,
   'planning.complete','SUCCEEDED',100,
   '{"planner_mode":"dev_mock","generated_days":7}');
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Wrong claim attempt accepted'; end if;
 denied:=false;
 begin
  perform public.retail_feature_worker_append('F2',
   'f8c10000-0000-4000-8000-000000000001',1,
   'planning.failed','FAILED',100,'{}'::jsonb);
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Forged failure on successful job accepted'; end if;
 denied:=false;
 begin
  perform public.retail_feature_worker_append('F5',
   'f8c10000-0000-4000-8000-000000000001',1,
   'planning.complete','SUCCEEDED',100,'{}'::jsonb);
 exception when invalid_parameter_value then denied:=true;
 end;
 if not denied then raise exception 'Unsupported F5 operation inserted'; end if;
 denied:=false;
 begin
  perform public.retail_feature_worker_append('F2',
   'f8c10000-0000-4000-8000-000000000001',1,
   'planning.complete','SUCCEEDED',100,'{"token":"secret"}'::jsonb);
 exception when invalid_parameter_value then denied:=true;
 end;
 if not denied then raise exception 'Unapproved metadata accepted'; end if;
end
$service_denials$;
reset role;

-- Signed owner may READ verified private events but cannot mint one.
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f8a10000-0000-4000-8000-000000000001',true);
do $owner$
declare result jsonb; denied boolean:=false;
begin
 result:=public.retail_feature_worker_spans(
   'f8b10000-0000-4000-8000-000000000001',
   'f8c10000-0000-4000-8000-000000000001',30);
 if jsonb_array_length(result->'events')<>1 or
    result->>'source'<>'trusted_backend_persisted' then
  raise exception 'Authorized owner cannot read trusted worker span'; end if;
 begin
  perform public.retail_feature_worker_append('F2',
   'f8c10000-0000-4000-8000-000000000001',1,
   'planning.complete','SUCCEEDED',100,
   '{"planner_mode":"dev_mock","generated_days":7}');
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Browser forged worker span'; end if;
end
$owner$;
-- VIEWER and foreign user cannot read private worker provenance.
select set_config('request.jwt.claim.sub','f8a10000-0000-4000-8000-000000000003',true);
do $viewer$
declare denied boolean:=false;
begin
 begin
  perform public.retail_feature_worker_spans(
   'f8b10000-0000-4000-8000-000000000001',
   'f8c10000-0000-4000-8000-000000000001',30);
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'VIEWER read trusted spans'; end if;
end
$viewer$;
select set_config('request.jwt.claim.sub','f8a10000-0000-4000-8000-000000000002',true);
do $foreign$
declare denied boolean:=false;
begin
 begin
  perform public.retail_feature_worker_spans(
   'f8b10000-0000-4000-8000-000000000001',
   'f8c10000-0000-4000-8000-000000000001',30);
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Foreign user read trusted spans'; end if;
end
$foreign$;
set local role anon;
select set_config('request.jwt.claim.role','anon',true);
select set_config('request.jwt.claim.sub','',true);
do $anonymous$
declare denied boolean:=false;
begin
 begin
  perform public.retail_feature_worker_spans(
   'f8b10000-0000-4000-8000-000000000001',
   'f8c10000-0000-4000-8000-000000000001',30);
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Anon read worker spans'; end if;
end
$anonymous$;
reset role;
rollback;
\echo 'WORKER_TRACE_PRIVATE_LEDGER_NEGATIVE=PASS (disposable CI only)'
