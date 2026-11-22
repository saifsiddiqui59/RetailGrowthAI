-- Real PostgreSQL rollback test for the F2/F4 source-only render job candidate.
-- Runs ONLY in disposable Supabase CI; never hosted DEV/PROD.
\set ON_ERROR_STOP on
\i supabase/candidates/feature4_cpu_render_jobs_20261121.sql
\i supabase/candidates/feature4_cpu_worker_claim_20261122.sql
\i supabase/candidates/feature4_cpu_worker_outbox_20261122.sql
\i supabase/candidates/feature4_cpu_worker_finish_20261122.sql
\i supabase/candidates/feature4_cpu_worker_poison_20261122.sql
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

-- Prove a *re-sealed* synthetic approved direction with a missing required
-- top-level approval flag cannot bypass SQL's three-valued OR guard.
-- Savepoint rollback preserves the valid fixture for normal worker coverage.
reset role;
savepoint feature4_null_approval_guard;
with stripped as (
  select id,approved_direction - 'approved' - 'review_hash' as direction
  from public.feature4_creative_plans
  where id='f5300000-0000-4000-8000-000000000001'
), sealed as (
  select id,direction,pg_catalog.encode(extensions.digest(
    pg_catalog.convert_to('rgai-f2-f4-approved-v1','UTF8') ||
    pg_catalog.decode('00','hex') ||
    pg_catalog.convert_to(retail_private.python_json_v1(direction),'UTF8'),
    'sha256'),'hex') as digest
  from stripped
)
update public.feature4_creative_plans p set
  approved_direction=sealed.direction ||
    pg_catalog.jsonb_build_object('review_hash',sealed.digest),
  review_sha256=sealed.digest
from sealed where p.id=sealed.id;
update public.feature4_cpu_render_jobs j
  set approved_review_sha256=p.review_sha256
from public.feature4_creative_plans p where j.plan_id=p.id
  and p.id='f5300000-0000-4000-8000-000000000001';
set local role service_role;
do $missing_approval$
declare jid uuid;
begin
  select id into jid from public.feature4_cpu_render_jobs
  where plan_id='f5300000-0000-4000-8000-000000000001';
  if (select retail_private.feature4_cpu_authorized(jid)) is not false
    or public.feature4_claim_cpu_render(jid) is not null
  then raise exception
    'FAIL: missing approval flag authorized a re-sealed CPU plan';
  end if;
end $missing_approval$;
reset role;
rollback to savepoint feature4_null_approval_guard;

-- Worker service role may claim exactly one dedicated outbox event; stale
-- ACK/lease may not finalize or steal any other worker's claim.
reset role;
set local role service_role;
do $worker$
declare evt jsonb; item jsonb; job jsonb; token uuid;
        jid uuid := 'f5300000-0000-4000-8000-000000000001';
        render_id uuid;
begin
 evt:=public.feature4_claim_cpu_outbox(10);
 if pg_catalog.jsonb_array_length(evt)<>1 then
    raise exception 'FAIL: F4 independent outbox missing'; end if;
 item:=evt->0;
 if public.feature4_confirm_cpu_outbox(
      (item->>'id')::uuid,gen_random_uuid(),true) then
    raise exception 'FAIL: stale outbox ACK succeeded'; end if;
 if not public.feature4_confirm_cpu_outbox(
      (item->>'id')::uuid,(item->>'lease_token')::uuid,true) then
    raise exception 'FAIL: rightful outbox ACK was denied'; end if;
 select id into render_id from public.feature4_cpu_render_jobs where plan_id=jid;
 job:=public.feature4_claim_cpu_render(render_id);
 if job is null or job->>'preset'<>'feature4_reel_v1'
      or job->>'status'<>'RUNNING'
      or public.feature4_claim_cpu_render(render_id) is not null then
    raise exception 'FAIL: lease is not exclusive'; end if;
 token:=(job->>'render_claim_token')::uuid;
 if not public.feature4_cpu_claim_current(render_id,token)
      or public.feature4_cpu_claim_current(render_id,gen_random_uuid())
      or public.feature4_complete_cpu_render(
           render_id,gen_random_uuid(),'wrong','0'::text) then
    raise exception 'FAIL: forged or live worker lease validation'; end if;
 if public.feature4_complete_cpu_render(
       render_id,token,'/foreign/key.mp4',repeat('a',64)) then
    raise exception 'FAIL: completion accepted a foreign object path'; end if;
 if public.feature4_fail_cpu_render(render_id,gen_random_uuid(),'RENDER_FAILED') then
    raise exception 'FAIL: stale failure overwrote current claim'; end if;
 -- A volatile insert and its verification MUST be separate SQL
 -- statements; PostgreSQL does not guarantee boolean OR evaluation order.
 if public.feature4_record_cpu_poison(repeat('b',64),render_id) is not true then
   raise exception 'FAIL: F4 poison recording rejected'; end if;
 if (select count(*) from retail_private.feature4_cpu_poison_receipts
     where fingerprint=repeat('b',64))<>1 then
   raise exception 'FAIL: durable F4 CPU poison receipt absent'; end if;
 if public.feature4_record_cpu_poison(repeat('b',64),render_id) is not true then
   raise exception 'FAIL: F4 poison replay rejected'; end if;
 if (select count(*) from retail_private.feature4_cpu_poison_receipts
     where fingerprint=repeat('b',64))<>1 then
   raise exception 'FAIL: F4 poison replay was not idempotent'; end if;
 if not public.feature4_fail_cpu_render(render_id,token,'RENDER_FAILED') then
    raise exception 'FAIL: current worker failed to release lease for retry'; end if;
 if (select status from public.feature4_cpu_render_jobs where id=render_id)<>'QUEUED'
   or (select state from retail_private.feature4_cpu_outbox where job_id=render_id)<>'PENDING'
 then raise exception 'FAIL: bounded retry not persisted'; end if;
end $worker$;
reset role;
set local role authenticated;
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f5010000-0000-4000-8000-000000000001","is_anonymous":false}',true);


-- A NULL lease expiry is never a valid worker authorization. PostgreSQL
-- IF ... OR (lease <= now()) otherwise produces SQL UNKNOWN, which can skip
-- the rejection entirely. Keep this rollback-only corruption fixture isolated.
reset role;
savepoint feature4_null_render_lease_guard;
update public.feature4_cpu_render_jobs set
 status='RUNNING',
 render_claim_token='f5400000-0000-4000-8000-000000000001',
 render_lease_until=null
where plan_id='f5300000-0000-4000-8000-000000000001';
set local role service_role;
do $null_lease$
declare
  jid uuid;
  tok uuid := 'f5400000-0000-4000-8000-000000000001';
begin
  select id into jid from public.feature4_cpu_render_jobs
   where plan_id='f5300000-0000-4000-8000-000000000001';
  if public.feature4_cpu_claim_current(jid,tok) is not false then
    raise exception 'FAIL: NULL lease passed current-worker authorization';
  end if;
  if public.feature4_fail_cpu_render(jid,tok,'RENDER_FAILED') is not false then
    raise exception 'FAIL: NULL lease allowed stale worker failure';
  end if;
  if (select status from public.feature4_cpu_render_jobs where id=jid)
        is distinct from 'RUNNING' then
    raise exception 'FAIL: NULL lease mutated job after stale worker denial';
  end if;
end $null_lease$;
reset role;
rollback to savepoint feature4_null_render_lease_guard;

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
-- Exhausted F4 outbox must terminally reconcile a QUEUED job. Without
-- this, all eight failed sends could leave a charged job stuck indefinitely.
-- Both fixture mutations are isolated in savepoints (no hosted writes).
reset role;
savepoint feature4_dead_outbox_guard;
update retail_private.feature4_cpu_outbox o set state='DEAD',attempts=8,
  lease_token=null,lease_until=null
where job_id=(select id from public.feature4_cpu_render_jobs
  where plan_id='f5300000-0000-4000-8000-000000000001');
set local role service_role;
do $dead_outbox$
declare jid uuid; reconciled integer;
begin
  select id into jid from public.feature4_cpu_render_jobs
  where plan_id='f5300000-0000-4000-8000-000000000001';
  -- Invoke the VOLATILE SQL mutation in a distinct SPI statement. Reading
  -- statuses in the same OR expression can observe an old statement snapshot.
  reconciled := public.feature4_reconcile_cpu_render(20);
  if reconciled is distinct from 1 then
    raise exception 'FAIL: dead outbox stranded queued CPU job (reconciler did not select exactly one row)';
  end if;
  if not exists(
       select 1 from public.feature4_cpu_render_jobs
       where id=jid and status='FAILED' and error_code='RETRY_EXHAUSTED')
     or not exists(
       select 1 from retail_private.feature4_cpu_outbox
       where job_id=jid and state='DEAD')
  then raise exception 'FAIL: dead outbox stranded queued CPU job'; end if;
end $dead_outbox$;
reset role;
rollback to savepoint feature4_dead_outbox_guard;

-- The last lease may expire without a confirm() RPC (lost ACK/crash).
savepoint feature4_expired_eighth_send_guard;
update retail_private.feature4_cpu_outbox o set state='CLAIMED',
  attempts=8,lease_token=gen_random_uuid(),
  lease_until=now()-interval '1 minute'
where job_id=(select id from public.feature4_cpu_render_jobs
  where plan_id='f5300000-0000-4000-8000-000000000001');
set local role service_role;
do $expired_eighth$
declare jid uuid; reconciled integer;
begin
  select id into jid from public.feature4_cpu_render_jobs
  where plan_id='f5300000-0000-4000-8000-000000000001';
  -- Invoke the VOLATILE SQL mutation in a distinct SPI statement. Reading
  -- statuses in the same OR expression can observe an old statement snapshot.
  reconciled := public.feature4_reconcile_cpu_render(20);
  if reconciled is distinct from 1 then
    raise exception 'FAIL: lost eighth queue ACK stranded CPU job (reconciler did not select exactly one row)';
  end if;
  if not exists(
       select 1 from public.feature4_cpu_render_jobs
       where id=jid and status='FAILED' and error_code='RETRY_EXHAUSTED')
     or not exists(
       select 1 from retail_private.feature4_cpu_outbox
       where job_id=jid and state='DEAD')
  then raise exception 'FAIL: lost eighth queue ACK stranded CPU job'; end if;
end $expired_eighth$;
reset role;
rollback to savepoint feature4_expired_eighth_send_guard;

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
