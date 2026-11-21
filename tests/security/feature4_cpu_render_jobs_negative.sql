-- Real PostgreSQL rollback test for the F2/F4 source-only render job candidate.
-- Runs ONLY in disposable Supabase CI; never hosted DEV/PROD.
\set ON_ERROR_STOP on
\i supabase/candidates/feature4_cpu_render_jobs_20261121.sql
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
 ('f5010000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','f4-render-owner@example.invalid','!',now(),now()),
 ('f5010000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','f4-render-foreign@example.invalid','!',now(),now()),
 ('f5010000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','f4-render-viewer@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f5010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f5000000-0000-4000-8000-000000000001',
 'f5010000-0000-4000-8000-000000000001',
 'Video Shop A','feature4-video-shop-a');
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values('f5100000-0000-4000-8000-000000000001',
 'f5000000-0000-4000-8000-000000000001',
 'f5010000-0000-4000-8000-000000000001',
 'Approved test media and campaign',current_date);
insert into public.shop_memberships(shop_id,user_id,role)
values('f5000000-0000-4000-8000-000000000001',
 'f5010000-0000-4000-8000-000000000003','VIEWER');

select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f5010000-0000-4000-8000-000000000002","is_anonymous":false}',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f5000000-0000-4000-8000-000000000002',
 'f5010000-0000-4000-8000-000000000002',
 'Video Shop B','feature4-video-shop-b');
reset role;

-- Fix source test campaign and owned original. Test fixture only:
-- no actual licensed customer object or hosted video is represented.
update public.campaigns set status='DRAFT'
where id='f5100000-0000-4000-8000-000000000001';
insert into public.media_assets(id,shop_id,created_by,
  storage_bucket,object_path,mime_type,source,license_name)
values('f5200000-0000-4000-8000-000000000001',
 'f5000000-0000-4000-8000-000000000001',
 'f5010000-0000-4000-8000-000000000001',
 'retailgrowth-media',
 'f5000000-0000-4000-8000-000000000001/uploads/f5200000-0000-4000-8000-000000000001.png',
 'image/png','UPLOAD','owned');

-- Service-issued draft: clients cannot insert or forge source proposals.
with proposal as (
  select '{
   "version":"creative_direction_v1","source_feature":"feature2",
   "approved":false,"shop_id":"f5000000-0000-4000-8000-000000000001",
   "campaign_id":"f5100000-0000-4000-8000-000000000001",
   "duration_seconds":30,"template":"cinematic","cta":"Visit our shop",
   "script":{"source_feature":"feature2","approved":false,
      "approved_text":["Introducing our range","Visit our shop"],
      "cta":"Visit our shop"},
   "scenes":[
     {"duration":15,"headline":"Introducing our range",
       "asset_id":"f5200000-0000-4000-8000-000000000001",
       "animation_preset":"subtle_zoom","transition":"fade"},
     {"duration":15,"headline":"Visit our shop",
       "asset_id":"f5200000-0000-4000-8000-000000000001",
       "animation_preset":"subtle_zoom","transition":"fade"}
   ]
  }'::jsonb as data
)
insert into public.feature4_creative_plans(
 id,shop_id,campaign_id,issued_by,proposal,proposal_sha256,media_asset_ids)
select 'f5300000-0000-4000-8000-000000000001',
  'f5000000-0000-4000-8000-000000000001',
  'f5100000-0000-4000-8000-000000000001',
  'f5010000-0000-4000-8000-000000000001',
  p.data,pg_catalog.encode(extensions.digest(
    pg_catalog.convert_to(retail_private.python_json_v1(p.data),'UTF8'),
    'sha256'),'hex'),
  array['f5200000-0000-4000-8000-000000000001'::uuid]
from proposal p;

-- Unauthenticated calls and forged direct job writes fail closed.
set local role anon;
select set_config('request.jwt.claims','{"role":"anon"}',true);
do $test$
declare denied boolean := false;
begin
  begin
    perform public.feature4_submit_cpu_render(
      'f5300000-0000-4000-8000-000000000001','0'::text);
  exception when insufficient_privilege then denied := true; end;
  if not denied then raise exception 'FAIL: anon could submit CPU billable job'; end if;
end $test$;
reset role;

-- Current retailer, signed JWT, explicitly reviews source revision first.
set local role authenticated;
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f5010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
do $test$
declare
  plan_id uuid := 'f5300000-0000-4000-8000-000000000001';
  before_sha text;
  reviewed jsonb;
  answer jsonb;
  again jsonb;
  total integer;
begin
  select proposal_sha256 into before_sha
  from public.feature4_creative_plans where id=plan_id;
  reviewed := public.feature4_review_cpu_plan(plan_id,before_sha);
  if reviewed is null or reviewed->>'status'<>'APPROVED'
       or reviewed->>'review_hash' !~ '^[0-9a-f]{64}$'
  then raise exception 'FAIL: real owner review did not persist'; end if;
  answer := public.feature4_submit_cpu_render(
    plan_id,reviewed->>'review_hash');
  if answer is null or answer->>'status' <> 'QUEUED'
    or answer->>'shop_id' <> 'f5000000-0000-4000-8000-000000000001'
  then raise exception 'FAIL: reviewed CPU render was not inserted'; end if;
  again := public.feature4_submit_cpu_render(
    plan_id,reviewed->>'review_hash');
  if again is distinct from answer then
    raise exception 'FAIL: idempotent render replay created new job'; end if;
  if (select count(*) from public.feature4_cpu_render_jobs j
      where j.plan_id='f5300000-0000-4000-8000-000000000001')<>1
    or (select count(*) from public.shop_usage_reservations
      where operation='render' and job_id=(answer->>'job_id')::uuid)<>1

  then raise exception 'FAIL: job, quota and private outbox not atomic'; end if;
  if public.feature4_submit_cpu_render(plan_id,'0'::text) is not null then
    raise exception 'FAIL: stale digest accepted'; end if;
end $test$;

-- Browser can see only same-shop job status, cannot directly create jobs.
do $test$
declare denied boolean := false;
begin
  begin
    insert into public.feature4_cpu_render_jobs(shop_id,campaign_id,plan_id,
       requested_by,approved_review_sha256,idempotency_key)
    values('f5000000-0000-4000-8000-000000000001',
           'f5100000-0000-4000-8000-000000000001',
           'f5300000-0000-4000-8000-000000000001',
           'f5010000-0000-4000-8000-000000000001',
           repeat('0',64),repeat('0',64));
  exception when insufficient_privilege then denied:=true; end;
  if not denied then raise exception 'FAIL: authenticated direct job INSERT'; end if;
end $test$;

-- Viewer may read only active own-shop history; cannot spend quota.
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f5010000-0000-4000-8000-000000000003","is_anonymous":false}',true);
do $test$
declare digest text;
begin
  select review_sha256 into digest from public.feature4_creative_plans
    where id='f5300000-0000-4000-8000-000000000001';
  if (select count(*) from public.feature4_cpu_render_jobs)<>1
    then raise exception 'FAIL: viewer own-shop read missing'; end if;
  if public.feature4_submit_cpu_render(
     'f5300000-0000-4000-8000-000000000001',digest) is not null
    then raise exception 'FAIL: viewer created billable job'; end if;
end $test$;

-- Foreign shop can neither discover job nor submit it.
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f5010000-0000-4000-8000-000000000002","is_anonymous":false}',true);
do $test$
declare digest text;
begin
  if exists(select 1 from public.feature4_cpu_render_jobs)
    then raise exception 'FAIL: foreign shop saw job'; end if;
  select review_sha256 into digest from public.feature4_creative_plans
    where id='f5300000-0000-4000-8000-000000000001';
  -- Foreign user cannot even read digest through RLS.
  if digest is not null then raise exception 'FAIL: foreign source review visible'; end if;
  if public.feature4_submit_cpu_render(
    'f5300000-0000-4000-8000-000000000001',repeat('a',64)) is not null
    then raise exception 'FAIL: foreign JWT submitted billable F4 job'; end if;
end $test$;

reset role;
-- Private outbox is service-only: inspect it as DB owner, never through a
-- browser JWT. Verify it is the exact single transactionally created record.
do $test$
begin
  if (select count(*) from retail_private.feature4_cpu_outbox o
    join public.feature4_cpu_render_jobs j on j.id=o.job_id
    where j.plan_id='f5300000-0000-4000-8000-000000000001'
      and o.state='PENDING')<>1 then
    raise exception 'FAIL: private outbox not inserted atomically'; end if;
end $test$;
-- After an owned-media license has changed, EVEN idempotent readback fails.
update public.media_assets set license_name='unverified'
where id='f5200000-0000-4000-8000-000000000001';
set local role authenticated;
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f5010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
do $test$
declare digest text;
begin
  select review_sha256 into digest from public.feature4_creative_plans
    where id='f5300000-0000-4000-8000-000000000001';
  if public.feature4_submit_cpu_render(
      'f5300000-0000-4000-8000-000000000001',digest) is not null
  then raise exception 'FAIL: changed media rights allowed job reuse'; end if;
end $test$;

-- An approved plan must still be active; revocation denies future requests.
reset role;
update public.media_assets set license_name='owned'
where id='f5200000-0000-4000-8000-000000000001';
set local role authenticated;
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f5010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
do $test$
declare digest text;
begin
  select review_sha256 into digest from public.feature4_creative_plans
    where id='f5300000-0000-4000-8000-000000000001';
  if not public.feature4_revoke_cpu_plan(
     'f5300000-0000-4000-8000-000000000001')
    then raise exception 'FAIL: owner review revoke was rejected'; end if;
  if public.feature4_submit_cpu_render(
      'f5300000-0000-4000-8000-000000000001',digest) is not null
    then raise exception 'FAIL: revoked plan generated/replayed CPU job'; end if;
end $test$;

rollback;
\echo 'PASS: F4 atomic CPU job/quota/private outbox, replay/foreign/viewer/revoked media/plan denials'
