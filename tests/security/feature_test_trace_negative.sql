-- Disposable local Supabase CI only. Never run on hosted DEV/PROD.
-- Intentionally apply the staged schema in an isolated database WITHOUT
-- adding it to the protected canonical migration-inventory allowlist.
\set ON_ERROR_STOP on
\i supabase/release-candidates/20261029090000_feature_test_trace.sql
begin;
do $preflight$
begin
 if not (select relrowsecurity from pg_class where oid='public.feature_test_runs'::regclass)
    or not (select relrowsecurity from pg_class where oid='public.feature_test_events'::regclass)
 then raise exception 'Trace RLS missing'; end if;
 if has_table_privilege('anon','public.feature_test_runs','SELECT')
    or has_table_privilege('anon','public.feature_test_events','INSERT')
    or has_table_privilege('authenticated','public.feature_test_events','UPDATE')
    or has_table_privilege('authenticated','public.feature_test_events','DELETE')
    or has_table_privilege('authenticated','public.feature_test_runs','DELETE')
 then raise exception 'Trace table exposed unsafe grants'; end if;
end
$preflight$;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('f7a10000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000','authenticated','authenticated','trace-owner@example.invalid','!',now(),now()),
('f7a10000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000','authenticated','authenticated','trace-viewer@example.invalid','!',now(),now()),
('f7a10000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000','authenticated','authenticated','trace-foreign@example.invalid','!',now(),now()),
('f7a10000-0000-4000-8000-000000000004','00000000-0000-0000-0000-000000000000','authenticated','authenticated','trace-editor@example.invalid','!',now(),now());
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f7a10000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f7b10000-0000-4000-8000-000000000001',
  'f7a10000-0000-4000-8000-000000000001','Trace first business','rg-trace-a');
insert into public.shop_memberships(shop_id,user_id,role)
values
('f7b10000-0000-4000-8000-000000000001',
 'f7a10000-0000-4000-8000-000000000002','VIEWER'),
('f7b10000-0000-4000-8000-000000000001',
 'f7a10000-0000-4000-8000-000000000004','EDITOR');
insert into public.feature_test_runs(id,shop_id,created_by,prompt,mode)
values('f7c10000-0000-4000-8000-000000000001',
 'f7b10000-0000-4000-8000-000000000001',
 'f7a10000-0000-4000-8000-000000000001',
 'Create a test clothing campaign and track each stage','prompt');
insert into public.feature_test_events(
 shop_id,run_id,actor_user_id,event_seq,feature,action,status,summary,details,duration_ms)
values('f7b10000-0000-4000-8000-000000000001',
 'f7c10000-0000-4000-8000-000000000001',
 'f7a10000-0000-4000-8000-000000000001',
 1,'F2','prompt-check','PASS','Test prompt was returned','{"origin":"browser-observed"}',20);
do $owner$
begin
 if (select count(*) from public.feature_test_events
   where run_id='f7c10000-0000-4000-8000-000000000001')<>1 then
   raise exception 'Owner append-only trace could not be read back';
 end if;
end
$owner$;
-- Current editor can read same-shop run, but cannot impersonate its creator.
select set_config('request.jwt.claim.sub','f7a10000-0000-4000-8000-000000000004',true);
do $editor$
declare denied boolean:=false;
begin
 if (select count(*) from public.feature_test_runs
   where id='f7c10000-0000-4000-8000-000000000001')<>1 then
   raise exception 'Current EDITOR cannot read authorized shop trace';
 end if;
 begin
  insert into public.feature_test_events(
   shop_id,run_id,actor_user_id,event_seq,feature,action,status,summary)
  values('f7b10000-0000-4000-8000-000000000001',
   'f7c10000-0000-4000-8000-000000000001',
   'f7a10000-0000-4000-8000-000000000004',2,'F2','fake-actor','PASS','Editor forged owner');
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'EDITOR appended into another actors run'; end if;
end
$editor$;
-- VIEWER reads zero rows, has no CREATE or arbitrary PASS ability.
select set_config('request.jwt.claim.sub','f7a10000-0000-4000-8000-000000000002',true);
do $viewer$
declare denied boolean:=false;
begin
 if exists(select 1 from public.feature_test_runs)
    or exists(select 1 from public.feature_test_events) then
   raise exception 'VIEWER leaked private trace';
 end if;
 begin
  insert into public.feature_test_runs(id,shop_id,created_by,prompt,mode)
  values('f7c10000-0000-4000-8000-000000000002',
  'f7b10000-0000-4000-8000-000000000001',
  'f7a10000-0000-4000-8000-000000000002',
  'Viewer fake request for trace bypass','prompt');
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'VIEWER created a trace'; end if;
end
$viewer$;
-- Foreign principal has no access to first business.
select set_config('request.jwt.claim.sub','f7a10000-0000-4000-8000-000000000003',true);
do $foreign$
declare denied boolean:=false;
begin
 if exists(select 1 from public.feature_test_runs)
   or exists(select 1 from public.feature_test_events) then
   raise exception 'Foreign user leaked private trace';
 end if;
 begin
  insert into public.feature_test_events(
   shop_id,run_id,actor_user_id,event_seq,feature,action,status,summary)
  values('f7b10000-0000-4000-8000-000000000001',
   'f7c10000-0000-4000-8000-000000000001',
   'f7a10000-0000-4000-8000-000000000003',3,'F2','foreign-pass','PASS','Foreign forged success');
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Foreign user appended PASS'; end if;
end
$foreign$;
-- An identity claiming the owner user ID must still satisfy fresh membership.
select set_config('request.jwt.claim.sub','f7a10000-0000-4000-8000-000000000001',true);
update public.shop_memberships set active=false
 where shop_id='f7b10000-0000-4000-8000-000000000001'
 and user_id='f7a10000-0000-4000-8000-000000000004';
select set_config('request.jwt.claim.sub','f7a10000-0000-4000-8000-000000000004',true);
do $revoked$
declare denied boolean:=false;
begin
 if exists(select 1 from public.feature_test_runs)
  or exists(select 1 from public.feature_test_events) then
   raise exception 'Revoked EDITOR still reads traces';
 end if;
 begin
  insert into public.feature_test_runs(id,shop_id,created_by,prompt,mode)
  values('f7c10000-0000-4000-8000-000000000004',
   'f7b10000-0000-4000-8000-000000000001',
   'f7a10000-0000-4000-8000-000000000004',
   'Revoked editor attempted an unauthorized run','prompt');
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Revoked EDITOR can still create a trace'; end if;
end
$revoked$;
-- Anonymous role cannot read or write anything, even if it supplies IDs.
set local role anon;
select set_config('request.jwt.claim.role','anon',true);
select set_config('request.jwt.claim.sub','',true);
do $anon$
declare denied boolean:=false;
begin
 begin
   perform 1 from public.feature_test_runs;
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Anonymous read grant'; end if;
end
$anon$;
reset role;
rollback;
\echo 'FEATURE_TEST_TRACE_RLS_NEGATIVE=PASS (disposable local DB only)'
