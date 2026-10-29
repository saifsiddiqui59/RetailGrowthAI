-- Disposable CI ONLY. This deliberately applies a release candidate without
-- adding it to protected canonical Supabase migrations. All fixtures rollback.
\set ON_ERROR_STOP on
\i supabase/release-candidates/20261029133000_feature_test_worker_spans.sql
begin;
do $privilege$
begin
 if has_table_privilege('anon','public.feature_test_worker_spans','SELECT')
    or has_table_privilege('authenticated','public.feature_test_worker_spans','INSERT')
    or has_table_privilege('authenticated','public.feature_test_worker_spans','UPDATE')
    or has_table_privilege('authenticated','public.feature_test_worker_spans','DELETE')
    or not has_table_privilege('service_role','public.feature_test_worker_spans','INSERT')
    or not (select relrowsecurity from pg_class where oid='public.feature_test_worker_spans'::regclass)
 then raise exception 'Unsafe worker span role/RLS grants'; end if;
end $privilege$;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('d0a00000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000','authenticated','authenticated','span-owner@example.invalid','!',now(),now()),
('d0a00000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000','authenticated','authenticated','span-viewer@example.invalid','!',now(),now()),
('d0a00000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000','authenticated','authenticated','span-foreign@example.invalid','!',now(),now()),
('d0a00000-0000-4000-8000-000000000004','00000000-0000-0000-0000-000000000000','authenticated','authenticated','span-editor@example.invalid','!',now(),now());
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','d0a00000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('d0b00000-0000-4000-8000-000000000001',
       'd0a00000-0000-4000-8000-000000000001','Trace business','rg-worker-trace-ci');
reset role;
select set_config('request.jwt.claim.role','service_role',true);
set local role service_role;
insert into public.shop_memberships(shop_id,user_id,role)
values('d0b00000-0000-4000-8000-000000000001','d0a00000-0000-4000-8000-000000000002','VIEWER'),
      ('d0b00000-0000-4000-8000-000000000001','d0a00000-0000-4000-8000-000000000004','EDITOR');
insert into public.campaigns(
 id,shop_id,created_by,brief,start_date,status,planning_attempts)
values('d0c00000-0000-4000-8000-000000000001',
       'd0b00000-0000-4000-8000-000000000001',
       'd0a00000-0000-4000-8000-000000000001',
       'Seven day test garment campaign','2026-11-01','DRAFT',1);
insert into public.campaign_days(id,shop_id,campaign_id,day_index,scheduled_date,topic)
select pg_catalog.gen_random_uuid(),
 'd0b00000-0000-4000-8000-000000000001',
 'd0c00000-0000-4000-8000-000000000001',
 n, '2026-11-01'::date + n-1, 'Day '||n::text
from pg_catalog.generate_series(1,7) as s(n);
insert into public.media_assets(id,shop_id,created_by,object_path,mime_type,source,license_name,attribution)
values('d0d00000-0000-4000-8000-000000000001',
 'd0b00000-0000-4000-8000-000000000001',
 'd0a00000-0000-4000-8000-000000000001',
 'd0b00000-0000-4000-8000-000000000001/renders/demo.mp4',
 'video/mp4','GENERATED','owned','owner-created test source');
insert into public.render_jobs(
 id,shop_id,campaign_id,day_id,requested_by,preset,status,idempotency_key,attempts,output_asset_id)
select 'd0e00000-0000-4000-8000-000000000001',
 'd0b00000-0000-4000-8000-000000000001',
 'd0c00000-0000-4000-8000-000000000001',cd.id,
 'd0a00000-0000-4000-8000-000000000001',
 'instagram_reel_30s','SUCCEEDED','span-ci-test-1',1,
 'd0d00000-0000-4000-8000-000000000001'
from public.campaign_days cd
where cd.campaign_id='d0c00000-0000-4000-8000-000000000001' and cd.day_index=1;
insert into public.feature_test_worker_spans(shop_id,job_id,feature,operation,status,attempt,elapsed_ms,metadata)
values('d0b00000-0000-4000-8000-000000000001',
'd0c00000-0000-4000-8000-000000000001','F2','planning.complete','SUCCEEDED',1,100,
'{"generated_days":7,"planner_mode":"dev_mock"}'::jsonb),
('d0b00000-0000-4000-8000-000000000001',
'd0e00000-0000-4000-8000-000000000001','F4','render.complete','SUCCEEDED',1,250,
'{"codec":"h264/aac","video_width":1080,"video_height":1920,"duration_seconds":30}'::jsonb);
do $verified$
declare failed boolean;
begin
 if (select count(*) from public.feature_test_worker_spans)<>2 then
    raise exception 'Real F2/F4 server span inserts rejected'; end if;
 failed := false;
 begin
  insert into public.feature_test_worker_spans(shop_id,job_id,feature,operation,status,attempt,elapsed_ms,metadata)
  values('d0b00000-0000-4000-8000-000000000001',
   'd0c00000-0000-4000-8000-000000000001','F2','planning.complete','SUCCEEDED',2,20,
   '{"generated_days":7,"planner_mode":"dev_mock"}');
 exception when insufficient_privilege then failed:=true;
 end;
 if not failed then raise exception 'Wrong fenced attempt forged success'; end if;
 failed := false;
 begin
  insert into public.feature_test_worker_spans(shop_id,job_id,feature,operation,status,attempt,elapsed_ms,metadata)
  values('d0b00000-0000-4000-8000-000000000001',
   'd0c00000-0000-4000-8000-000000000001','F2','planning.failed','FAILED',1,20,'{}');
 exception when invalid_parameter_value then failed:=true;
 end;
 if not failed then raise exception 'Forged failure ignored DB status'; end if;
 failed := false;
 begin
  insert into public.feature_test_worker_spans(shop_id,job_id,feature,operation,status,attempt,elapsed_ms,metadata)
  values('d0b00000-0000-4000-8000-000000000001',
   'd0e00000-0000-4000-8000-000000000001','F4','render.failed','FAILED',1,20,'{}');
 exception when invalid_parameter_value then failed:=true;
 end;
 if not failed then raise exception 'Fake FFmpeg failure bypassed DB result'; end if;
 failed := false;
 begin
  insert into public.feature_test_worker_spans(shop_id,job_id,feature,operation,status,attempt,elapsed_ms,metadata)
  values('d0b00000-0000-4000-8000-000000000001',
   'd0e00000-0000-4000-8000-000000000001','F4','render.complete','SUCCEEDED',1,20,
   '{"codec":"h264/aac","video_width":720,"video_height":1920,"duration_seconds":30}');
 exception when invalid_parameter_value then failed:=true;
 end;
 if not failed then raise exception 'Forged 720p output passed 1080p gate'; end if;
end $verified$;
-- Same-shop OWNER can read verified trusted rows but not forge them.
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','d0a00000-0000-4000-8000-000000000001',true);
do $owner$
declare denied boolean:=false;
begin
 if (select count(*) from public.feature_test_worker_spans)<>2
 then raise exception 'Owner cannot read own verified worker spans'; end if;
 begin
  insert into public.feature_test_worker_spans(shop_id,job_id,feature,operation,status,attempt,elapsed_ms)
  values('d0b00000-0000-4000-8000-000000000001',
   'd0e00000-0000-4000-8000-000000000001','F4','render.failed','FAILED',1,1);
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Browser OWNER forged trusted worker span'; end if;
end $owner$;
select set_config('request.jwt.claim.sub','d0a00000-0000-4000-8000-000000000004',true);
do $editor$
begin
 if (select count(*) from public.feature_test_worker_spans)<>2
 then raise exception 'Active EDITOR denied legitimate read'; end if;
end $editor$;
select set_config('request.jwt.claim.sub','d0a00000-0000-4000-8000-000000000002',true);
do $viewer$
begin
 if exists(select 1 from public.feature_test_worker_spans)
 then raise exception 'VIEWER leaked private worker spans'; end if;
end $viewer$;
select set_config('request.jwt.claim.sub','d0a00000-0000-4000-8000-000000000003',true);
do $foreign$
begin
 if exists(select 1 from public.feature_test_worker_spans)
 then raise exception 'Foreign tenant leaked private worker spans'; end if;
end $foreign$;
-- Revocation of an authorized editor immediately removes read rights.
reset role;
set local role service_role;
update public.shop_memberships set active=false
where shop_id='d0b00000-0000-4000-8000-000000000001'
 and user_id='d0a00000-0000-4000-8000-000000000004';
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','d0a00000-0000-4000-8000-000000000004',true);
do $revoked$
begin
 if exists(select 1 from public.feature_test_worker_spans)
 then raise exception 'Revoked editor retained trusted span read'; end if;
end $revoked$;
set local role anon;
select set_config('request.jwt.claim.role','anon',true);
select set_config('request.jwt.claim.sub','',true);
do $anon$
declare denied boolean:=false;
begin
 begin
  perform 1 from public.feature_test_worker_spans;
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'Anonymous role received worker span read'; end if;
end $anon$;
reset role;
rollback;
\echo 'FEATURE_TEST_WORKER_SPAN_RLS=PASS (disposable PostgreSQL only)'
