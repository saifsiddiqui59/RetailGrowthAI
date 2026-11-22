-- Real disposable Postgres test of F2→F4 service-issued + human-reviewed
-- persisted immutable plan, shop-RLS, frozen digest and owner revocation.
-- Always rolled back. NEVER run on hosted DEV/PROD.
\set ON_ERROR_STOP on
-- Only disposable isolated CI loads this candidate; the main migration inventory
-- and protected Feature3/DEV migration gates must NOT change.
\i supabase/candidates/feature4_reviewed_cpu_plans_20261121.sql
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
 ('f4010000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','f4-a@example.invalid','!',now(),now()),
 ('f4010000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','f4-b@example.invalid','!',now(),now()),
 ('f4010000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','f4-viewer@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f4000000-0000-4000-8000-000000000001',
       'f4010000-0000-4000-8000-000000000001','Feature4 A','feature4-test-a');
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values('f4100000-0000-4000-8000-000000000001',
       'f4000000-0000-4000-8000-000000000001',
       'f4010000-0000-4000-8000-000000000001','F4 fictional creative',current_date);
insert into public.shop_memberships(shop_id,user_id,role)
values('f4000000-0000-4000-8000-000000000001',
       'f4010000-0000-4000-8000-000000000003','VIEWER');
select set_config('request.jwt.claims','{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000002","is_anonymous":false}',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f4000000-0000-4000-8000-000000000002',
       'f4010000-0000-4000-8000-000000000002','Feature4 B','feature4-test-b');

reset role;
select set_config('request.jwt.claims','{"role":"service_role","sub":"f4010000-0000-4000-8000-000000000001"}',true);
-- The fixture intentionally tests approved draft selection, not a pending
-- planning campaign that has not yet produced a valid storyboard.
update public.campaigns set status='DRAFT'
 where id='f4100000-0000-4000-8000-000000000001';
insert into public.media_assets(id,shop_id,created_by,
    storage_bucket,object_path,mime_type,source,license_name)
values('f4200000-0000-4000-8000-000000000001',
       'f4000000-0000-4000-8000-000000000001',
       'f4010000-0000-4000-8000-000000000001',
       'retailgrowth-media',
       'f4000000-0000-4000-8000-000000000001/uploads/f4200000-0000-4000-8000-000000000001.png',
       'image/png','UPLOAD','owned');
insert into public.feature4_creative_plans(
 id,shop_id,campaign_id,issued_by,proposal,proposal_sha256,media_asset_ids)
values(
 'f4300000-0000-4000-8000-000000000001',
 'f4000000-0000-4000-8000-000000000001',
 'f4100000-0000-4000-8000-000000000001',
 'f4010000-0000-4000-8000-000000000001',
 '{
   "version":"creative_direction_v1","source_feature":"feature2",
   "approved":false,"shop_id":"f4000000-0000-4000-8000-000000000001",
   "campaign_id":"f4100000-0000-4000-8000-000000000001",
   "duration_seconds":30,"template":"cinematic","cta":"Visit our studio",
   "script":{"source_feature":"feature2","approved":false,
      "approved_text":["New arrivals","Visit our studio"],"cta":"Visit our studio"},
   "scenes":[
     {"duration":15,"headline":"New arrivals",
       "asset_id":"f4200000-0000-4000-8000-000000000001",
       "animation_preset":"subtle_zoom","transition":"fade"},
     {"duration":15,"headline":"Visit our studio",
       "asset_id":"f4200000-0000-4000-8000-000000000001",
       "animation_preset":"subtle_zoom","transition":"fade"}
   ]
 }'::jsonb,
 '63aa02ddf00c76b7d0e65068dc14176f302d733802731cc7867051b54180b5c4',
 array['f4200000-0000-4000-8000-000000000001'::uuid]);

-- Deny any direct browser plan forging even if the logged-in actor owns the shop.
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
do $$
declare refused boolean := false;
begin
  begin
    insert into public.feature4_creative_plans(
      shop_id,campaign_id,issued_by,proposal,proposal_sha256,media_asset_ids)
    select shop_id,campaign_id,issued_by,proposal,proposal_sha256,media_asset_ids
      from public.feature4_creative_plans where id='f4300000-0000-4000-8000-000000000001';
  exception when insufficient_privilege then refused := true; end;
  if not refused then raise exception 'FAIL: browser minted its own F2 plan'; end if;
  if (select count(*) from public.feature4_creative_plans)<>1
    then raise exception 'FAIL: valid shop cannot read own source proposal'; end if;
  if public.feature4_review_cpu_plan(
    'f4300000-0000-4000-8000-000000000001',
    '0000000000000000000000000000000000000000000000000000000000000000') is not null
    then raise exception 'FAIL: forged proposal hash was reviewed'; end if;
end $$;

-- Foreign authenticated owner cannot approve or discover shop A proposals.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000002","is_anonymous":false}',true);
do $$
begin
  if exists(select 1 from public.feature4_creative_plans)
    then raise exception 'FAIL: cross-shop Feature4 approval leaked'; end if;
  if public.feature4_review_cpu_plan(
    'f4300000-0000-4000-8000-000000000001',
    '63aa02ddf00c76b7d0e65068dc14176f302d733802731cc7867051b54180b5c4') is not null
    then raise exception 'FAIL: foreign owner approved Feature2 content'; end if;
  if public.feature4_revoke_cpu_plan('f4300000-0000-4000-8000-000000000001')
    then raise exception 'FAIL: foreign owner revoked Feature2 content'; end if;
end $$;

-- VIEWER may read same-shop draft but cannot authorize spend, review or revoke.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000003","is_anonymous":false}',true);
do $$
begin
  if (select count(*) from public.feature4_creative_plans)<>1
    then raise exception 'FAIL: authorized same-shop viewer cannot read'; end if;
  if public.feature4_review_cpu_plan(
    'f4300000-0000-4000-8000-000000000001',
    '63aa02ddf00c76b7d0e65068dc14176f302d733802731cc7867051b54180b5c4') is not null
    then raise exception 'FAIL: VIEWER approved F2 plan'; end if;
end $$;

-- A changed or nonexistent campaign day must not authorize a stale
-- signed source, even when proposal SHA, shop and licensed media all match.
reset role;
insert into public.feature4_creative_plans(
 id,shop_id,campaign_id,issued_by,proposal,proposal_sha256,media_asset_ids)
select 'f4300000-0000-4000-8000-000000000002',
       shop_id,campaign_id,issued_by,
       proposal || jsonb_build_object(
         'day_id','f4400000-0000-4000-8000-000000000099',
         'music_asset_id',null,
         'source_reel',jsonb_build_object('duration_seconds',30)),
       pg_catalog.encode(extensions.digest(
         pg_catalog.convert_to(retail_private.python_json_v1(
           proposal || jsonb_build_object(
             'day_id','f4400000-0000-4000-8000-000000000099',
             'music_asset_id',null,
             'source_reel',jsonb_build_object('duration_seconds',30))
         ),'UTF8'),'sha256'),'hex'),
       media_asset_ids
from public.feature4_creative_plans
where id='f4300000-0000-4000-8000-000000000001';
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
do $$
begin
  if public.feature4_review_cpu_plan(
      'f4300000-0000-4000-8000-000000000002',
      (select proposal_sha256 from public.feature4_creative_plans
       where id='f4300000-0000-4000-8000-000000000002')) is not null then
     raise exception 'FAIL: stale or nonexistent F2 campaign day approved';
  end if;
end $$;

-- JWT owner cannot review malformed-but-resealed original F2 proposals.
-- Postgres CHECK permits UNKNOWN, hence the explicit SQL reviewer guards.
reset role;
savepoint feature4_null_source_approved;
with altered as (
 select id,proposal - 'approved' as payload from public.feature4_creative_plans
 where id='f4300000-0000-4000-8000-000000000001'
)
update public.feature4_creative_plans p set proposal=altered.payload,
 proposal_sha256=pg_catalog.encode(extensions.digest(
   pg_catalog.convert_to(retail_private.python_json_v1(altered.payload),'UTF8'),
   'sha256'),'hex')
from altered where p.id=altered.id;
set local role authenticated;
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
do $no_source_approved$
declare digest text;
begin
 select proposal_sha256 into digest from public.feature4_creative_plans
 where id='f4300000-0000-4000-8000-000000000001';
 if public.feature4_review_cpu_plan('f4300000-0000-4000-8000-000000000001',digest) is not null
 then raise exception 'FAIL: source missing approval field passed review'; end if;
end $no_source_approved$;
reset role;
rollback to savepoint feature4_null_source_approved;

savepoint feature4_null_script_approved;
with altered as (
 select id,pg_catalog.jsonb_set(proposal,'{script}',(proposal->'script')-'approved') as payload
 from public.feature4_creative_plans
 where id='f4300000-0000-4000-8000-000000000001'
)
update public.feature4_creative_plans p set proposal=altered.payload,
 proposal_sha256=pg_catalog.encode(extensions.digest(
   pg_catalog.convert_to(retail_private.python_json_v1(altered.payload),'UTF8'),
   'sha256'),'hex')
from altered where p.id=altered.id;
set local role authenticated;
select set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
do $no_script_approved$
declare digest text;
begin
 select proposal_sha256 into digest from public.feature4_creative_plans
 where id='f4300000-0000-4000-8000-000000000001';
 if public.feature4_review_cpu_plan('f4300000-0000-4000-8000-000000000001',digest) is not null
 then raise exception 'FAIL: source script missing approval field passed review'; end if;
end $no_script_approved$;
reset role;
rollback to savepoint feature4_null_script_approved;

-- Owner explicitly approves only its current saved source, no automatic fixture
-- promotion. Hash is independently predetermined by Python serializer.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000001","is_anonymous":false}',true);
do $$
declare result jsonb;
        second jsonb;
begin
  result := public.feature4_review_cpu_plan(
    'f4300000-0000-4000-8000-000000000001',
    '63aa02ddf00c76b7d0e65068dc14176f302d733802731cc7867051b54180b5c4');
  if result is null or result->>'status' <> 'APPROVED'
      or result->>'review_hash' <> 
         'c59b66bf6402afb634fc383f1b8254f7e19de5a4bafcb14d8cc21b175969e138' then
    raise exception 'FAIL: reviewed F2 direction SHA did not match Python: actual=%, expected=%', result->>'review_hash', 'c59b66bf6402afb634fc383f1b8254f7e19de5a4bafcb14d8cc21b175969e138'; end if;
  if not exists(select 1 from public.feature4_creative_plans
    where id='f4300000-0000-4000-8000-000000000001'
      and state='APPROVED' and reviewed_by=auth.uid()
      and media_snapshot->0->>'id'='f4200000-0000-4000-8000-000000000001'
      and approved_direction->>'review_hash'=result->>'review_hash'
      and approved_direction->'approved'='true'::jsonb)
    then raise exception 'FAIL: immutable approved direction/media missing'; end if;
  second := public.feature4_review_cpu_plan(
    'f4300000-0000-4000-8000-000000000001',
    '63aa02ddf00c76b7d0e65068dc14176f302d733802731cc7867051b54180b5c4');
  if second is distinct from result then
    raise exception 'FAIL: idempotent approved review changed'; end if;
  if not public.feature4_revoke_cpu_plan('f4300000-0000-4000-8000-000000000001')
    then raise exception 'FAIL: owner could not revoke approved plan'; end if;
  if public.feature4_review_cpu_plan(
    'f4300000-0000-4000-8000-000000000001',
    '63aa02ddf00c76b7d0e65068dc14176f302d733802731cc7867051b54180b5c4') is not null
    then raise exception 'FAIL: revoked approval became active again'; end if;
end $$;

-- A backend role performs the test-only revocation; an authenticated
-- browser must NOT have direct membership UPDATE privilege.
reset role;
update public.shop_memberships set active=false
 where shop_id='f4000000-0000-4000-8000-000000000001'
   and user_id='f4010000-0000-4000-8000-000000000003';
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"f4010000-0000-4000-8000-000000000003","is_anonymous":false}',true);
do $$
begin
  if exists(select 1 from public.feature4_creative_plans)
    then raise exception 'FAIL: inactive viewer read review history'; end if;
end $$;
reset role;
set local role anon;
select set_config('request.jwt.claims','{"role":"anon"}',true);
do $$
declare denied boolean := false;
begin
  begin
    if public.feature4_review_cpu_plan(
        'f4300000-0000-4000-8000-000000000001',
        '63aa02ddf00c76b7d0e65068dc14176f302d733802731cc7867051b54180b5c4')
      is not null then raise exception 'FAIL: anonymous approved creative plan'; end if;
  exception when insufficient_privilege then denied:=true; end;
  if not denied then
    raise exception 'FAIL: anonymous function EXECUTE was unexpectedly granted';
  end if;
end $$;
reset role;
rollback;
\echo 'PASS: F2→F4 persisted SHA, real owner review/revoke, foreign and viewer denial, RLS revocation'
