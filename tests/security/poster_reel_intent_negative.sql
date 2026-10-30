-- GitHub Actions disposable local Supabase Postgres ONLY, never hosted DEV/PROD.
-- Existing CI applies the versioned migration, then runs this SQL transaction.
-- This test's fixtures ROLLBACK. The migrated schema lives only in disposable CI Postgres.
\set ON_ERROR_STOP on
begin;
-- Canonical migration is applied by disposable `supabase db start` first.
-- Abort if the versioned RPC is missing; never load a second proposal copy.
select 'public.request_reel_render_job(uuid,uuid)'::regprocedure;

-- Runtime fixture must use current PostgREST request.jwt.claims JSON, NOT the
-- legacy request.jwt.claim.role/sub GUCs (removed on PostgreSQL 14+).
-- The Python hash serializer must match ensure_ascii=True (incl. emoji/Hindi).
do $$
declare serialised text;
begin
  serialised:=retail_private.python_json_v1('{"z":"हिंदी","a":"🎉"}'::jsonb);
  if serialised <> '{"a":"\ud83c\udf89","z":"\u0939\u093f\u0902\u0926\u0940"}' then
    raise exception 'Python Unicode/sorted-key canonicalization mismatch: %',serialised;
  end if;
  if has_function_privilege('anon','public.request_reel_render_job(uuid,uuid)','EXECUTE') then
    raise exception 'anonymous can execute privileged Reel SQL RPC';
  end if;
  if not has_function_privilege('authenticated','public.request_reel_render_job(uuid,uuid)','EXECUTE') then
    raise exception 'authenticated cannot execute narrowed Reel SQL RPC';
  end if;
  if exists (
    select 1 from pg_catalog.pg_proc p
    join pg_catalog.pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname='request_reel_render_job'
      and p.prosecdef
  ) then raise exception 'exposed public Reel RPC must NOT be security definer'; end if;
  if not exists (
    select 1 from pg_catalog.pg_proc p
    join pg_catalog.pg_namespace n on n.oid=p.pronamespace
    where n.nspname='retail_private' and p.proname='request_reel_render_job_internal'
      and p.prosecdef
  ) then raise exception 'private implementation needs scoped definer for DB INSERT'; end if;
  if has_table_privilege('authenticated','public.render_jobs','INSERT') then
    raise exception 'unreviewed broad authenticated render_jobs INSERT grant';
  end if;
end $$;

insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('11111111-1111-4111-8111-111111111111','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','reel-rpc-owner@example.invalid','!',now(),now()),
('22222222-2222-4222-8222-222222222222','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','reel-rpc-viewer@example.invalid','!',now(),now()),
('99999999-9999-4999-8999-999999999999','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','reel-rpc-foreign@example.invalid','!',now(),now());

set local role authenticated;
-- auth claims set through request.jwt.claims JSON below (PostgREST >= 14).
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
insert into public.shops(id,owner_user_id,name,slug) values
('33333333-3333-4333-8333-333333333333',
 '11111111-1111-4111-8111-111111111111','Reel RPC isolated shop','rg-reel-rpc-ci');
insert into public.shop_memberships(shop_id,user_id,role) values
('33333333-3333-4333-8333-333333333333',
 '22222222-2222-4222-8222-222222222222','VIEWER');

reset role;
select set_config('request.jwt.claims','{"role":"service_role","sub":"11111111-1111-4111-8111-111111111111"}',true);
insert into public.campaigns(id,shop_id,created_by,brief,start_date) values
('44444444-4444-4444-8444-444444444444',
 '33333333-3333-4333-8333-333333333333',
 '11111111-1111-4111-8111-111111111111',
 'Disposable test, no actual video generation','2026-11-01');
update public.campaigns set status='DRAFT'
 where id='44444444-4444-4444-8444-444444444444';
insert into public.media_assets(id,shop_id,created_by,object_path,mime_type,source,
   license_name,attribution) values
('55555555-5555-4555-8555-555555555555',
 '33333333-3333-4333-8333-333333333333',
 '11111111-1111-4111-8111-111111111111',
 '33333333-3333-4333-8333-333333333333/uploads/55555555-5555-4555-8555-555555555555.png',
 'image/png','UPLOAD','owned','Retail owner-created and reviewed'),
('66666666-6666-4666-8666-666666666666',
 '33333333-3333-4333-8333-333333333333',
 '11111111-1111-4111-8111-111111111111',
 '33333333-3333-4333-8333-333333333333/uploads/66666666-6666-4666-8666-666666666666.png',
 'image/png','UPLOAD',null,'Unreviewed media');

insert into public.campaign_days(id,campaign_id,shop_id,day_index,scheduled_date,
  topic,linkedin,instagram) values
('88888888-8888-4888-8888-888888888888',
 '44444444-4444-4444-8444-444444444444',
 '33333333-3333-4333-8333-333333333333',
 1,'2026-11-01','Fashion sale',
 '{"post_text":"Shop Diwali","hashtags":["#Diwali"]}'::jsonb,
 '{"caption":"Diwali Sale","banner_asset_id":null,"reel":{"duration_seconds":30,"aspect_ratio":"9:16","storyboard":[{"asset_id":"55555555-5555-4555-8555-555555555555","overlay_text":"Festival 🎉 हिंदी","start_seconds":0,"duration_seconds":30}],"music_asset_id":null,"cta":"आज Shop now"}}'::jsonb);

-- Worker-side legacy job from Python's exact SHA-256 compact sorted JSON
-- must be FOUND, not charged again or duplicated, on Node/client request.
insert into public.render_jobs(id,shop_id,campaign_id,day_id,requested_by,preset,
  status,idempotency_key) values
('77777777-7777-4777-8777-777777777777',
 '33333333-3333-4333-8333-333333333333',
 '44444444-4444-4444-8444-444444444444',
 '88888888-8888-4888-8888-888888888888',
 '11111111-1111-4111-8111-111111111111',
 'instagram_reel_30s','QUEUED',
 '73593202305f3dec115aaf8e851e5aac9045fb751b3587641b9ec5713efcb3c6');

set local role authenticated;
-- auth claims set through request.jwt.claims JSON below (PostgREST >= 14).
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
do $$
declare result jsonb;
begin
  result:=public.request_reel_render_job(
   '44444444-4444-4444-8444-444444444444',
   '88888888-8888-4888-8888-888888888888');
  if result->>'job_id'<>'77777777-7777-4777-8777-777777777777' or
     result->>'status'<>'QUEUED' then
    raise exception 'legacy Python digest not reused: %',result;
  end if;
  result:=public.request_reel_render_job(
   '44444444-4444-4444-8444-444444444444',
   '88888888-8888-4888-8888-888888888888');
  if result->>'job_id'<>'77777777-7777-4777-8777-777777777777' then
    raise exception 'same Reel input double queued despite Python key';
  end if;
  if (select count(*) from public.render_jobs)<>1 then
    raise exception 'legacy identical request created a duplicate render row';
  end if;
end $$;

-- Distinct MIME-role regression: same music AUDIO UUID cannot also occupy an
-- image storyboard frame, even if licensing and tenant ownership are valid.
-- A broken implementation might check only music MIME for this shared ID.
reset role;
select set_config('request.jwt.claims','{"role":"service_role","sub":"11111111-1111-4111-8111-111111111111"}',true);
insert into public.media_assets(id,shop_id,created_by,object_path,mime_type,
  source,license_name,attribution)
values ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  '33333333-3333-4333-8333-333333333333',
  '11111111-1111-4111-8111-111111111111',
  '33333333-3333-4333-8333-333333333333/uploads/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa.mp3',
  'audio/mpeg','UPLOAD','owned','Owned audio track and reviewed licensing');
update public.campaign_days set instagram=
  jsonb_set(jsonb_set(instagram,'{reel,storyboard,0,asset_id}',
    '"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"'::jsonb),
    '{reel,music_asset_id}',
    '"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"'::jsonb)
where id='88888888-8888-4888-8888-888888888888';
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
do $p0249_music_frame$
begin
  if public.request_reel_render_job(
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888') is not null then
    raise exception 'audio file reused in storyboard image slot got a render job';
  end if;
end $p0249_music_frame$;
reset role;
select set_config('request.jwt.claims','{"role":"service_role","sub":"11111111-1111-4111-8111-111111111111"}',true);
update public.campaign_days set instagram=
  jsonb_set(jsonb_set(instagram,'{reel,storyboard,0,asset_id}',
    '"55555555-5555-4555-8555-555555555555"'::jsonb),
    '{reel,music_asset_id}', 'null'::jsonb)
where id='88888888-8888-4888-8888-888888888888';
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);

-- Private quota and outbox are intentionally INVISIBLE to authenticated users.
-- Assert under disposable-test postgres identity only; never grant them SELECT.
reset role;
do $$
begin
  if (select count(*) from public.shop_usage_reservations where operation='render')<>1 or
     (select count(*) from public.job_outbox where kind='render')<>1 then
    raise exception 'legacy identical request double billed/outboxed';
  end if;
end $$;
set local role authenticated;
-- auth claims set through request.jwt.claims JSON below (PostgREST >= 14).
-- Forbidden VIEWER/foreign user cannot cause any additional job or usage.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"22222222-2222-4222-8222-222222222222","is_anonymous":false}',true);
do $$
begin
  if public.request_reel_render_job(
     '44444444-4444-4444-8444-444444444444',
     '88888888-8888-4888-8888-888888888888') is not null then
    raise exception 'VIEWER requested a privileged Reel job';
  end if;
end $$;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"99999999-9999-4999-8999-999999999999","is_anonymous":false}',true);
do $$
begin
  if public.request_reel_render_job(
     '44444444-4444-4444-8444-444444444444',
     '88888888-8888-4888-8888-888888888888') is not null then
    raise exception 'foreign shop requested private render';
  end if;
end $$;

-- One edited storyboard produces ONE fresh job/reservation/outbox.
reset role;
select set_config('request.jwt.claims','{"role":"service_role","sub":"11111111-1111-4111-8111-111111111111"}',true);
update public.campaign_days set instagram=jsonb_set(instagram,
  '{reel,cta}','"Edited CTA"'::jsonb)
 where id='88888888-8888-4888-8888-888888888888';
set local role authenticated;
-- auth claims set through request.jwt.claims JSON below (PostgREST >= 14).
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
do $$
declare a jsonb; b jsonb;
begin
  a:=public.request_reel_render_job(
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888');
  b:=public.request_reel_render_job(
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888');
  if a->>'job_id' is null or a->>'job_id'='77777777-7777-4777-8777-777777777777'
     or b->>'job_id' is distinct from a->>'job_id' then
    raise exception 'edited Reel job not new-and-idempotent';
  end if;
  if (select count(*) from public.render_jobs)<>2 then
    raise exception 'same modified Reel inserted duplicate jobs';
  end if;
end $$;

reset role;
do $$
begin
  if (select count(*) from public.shop_usage_reservations where operation='render')<>2 or
     (select count(*) from public.job_outbox where kind='render')<>2 then
    raise exception 'not exactly one subscription unit and outbox per edited job';
  end if;
end $$;
-- Editing to unlicensed (but same-shop) source cannot bypass rights.
reset role;
select set_config('request.jwt.claims','{"role":"service_role","sub":"11111111-1111-4111-8111-111111111111"}',true);
update public.campaign_days set instagram=jsonb_set(instagram,
  '{reel,storyboard,0,asset_id}',
  '"66666666-6666-4666-8666-666666666666"'::jsonb)
 where id='88888888-8888-4888-8888-888888888888';
set local role authenticated;
-- auth claims set through request.jwt.claims JSON below (PostgREST >= 14).
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
do $$
begin
  if public.request_reel_render_job(
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888') is not null then
    raise exception 'unlicensed source allowed new render';
  end if;
end $$;

-- Validate strict SQL privileges: no anonymous entry or direct user inserts.
set local role anon;
select set_config('request.jwt.claims','{"role":"anon"}',true);
-- No actor sub for anonymous request.
do $$
declare denied boolean:=false;
begin
  begin
    perform public.request_reel_render_job(
      '44444444-4444-4444-8444-444444444444',
      '88888888-8888-4888-8888-888888888888');
  exception when insufficient_privilege then denied:=true; end;
  if not denied then raise exception 'anonymous render RPC reachable'; end if;
end $$;

reset role;
do $$
begin
  if (select count(*) from public.render_jobs)<>2 then
    raise exception 'denied source bypass inserted another job'; end if;
end $$;
-- Subscription/no-replay guards, executed under the *same disposable rollback*
-- as all legacy idempotency and tenant tests above.
reset role;
select set_config('request.jwt.claims','{"role":"service_role","sub":"11111111-1111-4111-8111-111111111111"}',true);
update public.campaign_days set instagram=
  jsonb_set(
    jsonb_set(instagram,'{reel,storyboard,0,asset_id}',
              '"55555555-5555-4555-8555-555555555555"'::jsonb),
    '{reel,cta}', '"Fresh third render for quota check"'::jsonb)
where id='88888888-8888-4888-8888-888888888888';
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
do $$
begin
  begin
    perform public.request_reel_render_job(
      '44444444-4444-4444-8444-444444444444',
      '88888888-8888-4888-8888-888888888888');
    raise exception 'fresh third Reel bypassed exhausted trial quota';
  exception when sqlstate 'RG002' then null;
  end;
end $$;
reset role;
do $$
begin
  if (select count(*) from public.render_jobs)<>2
     or (select count(*) from public.shop_usage_reservations where operation='render')<>2
     or (select count(*) from public.job_outbox where kind='render')<>2 then
    raise exception 'quota denial changed jobs, usage or outbox';
  end if;
end $$;

-- Account expiry must deny NEW distinct render intents before billing.
select set_config('request.jwt.claims','{"role":"service_role","sub":"11111111-1111-4111-8111-111111111111"}',true);
update public.shop_subscriptions set status='EXPIRED',
  valid_from=now()-interval '2 days',
  valid_until=now()-interval '1 minute'
where shop_id='33333333-3333-4333-8333-333333333333';
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
do $$
begin
  begin
    perform public.request_reel_render_job(
      '44444444-4444-4444-8444-444444444444',
      '88888888-8888-4888-8888-888888888888');
    raise exception 'expired subscription requested new Reel';
  exception when sqlstate 'RG001' then null;
  end;
end $$;

-- Revoke the OWNER membership: claimed JWT alone must not authorize writes.
reset role;
select set_config('request.jwt.claims','{"role":"service_role","sub":"11111111-1111-4111-8111-111111111111"}',true);
update public.shop_memberships set active=false
 where shop_id='33333333-3333-4333-8333-333333333333'
 and user_id='11111111-1111-4111-8111-111111111111';
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
do $$
begin
  if public.request_reel_render_job(
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888') is not null then
    raise exception 'revoked OWNER membership allowed render';
  end if;
end $$;

-- Force existing AFTER INSERT outbox trigger to fail. BEFORE INSERT quota
-- reservation MUST roll back in the same statement: no orphaned usage.
reset role;
select set_config('request.jwt.claims','{"role":"service_role","sub":"11111111-1111-4111-8111-111111111111"}',true);
update public.shop_memberships set active=true
 where shop_id='33333333-3333-4333-8333-333333333333'
 and user_id='11111111-1111-4111-8111-111111111111';
update public.shop_subscriptions set
  plan_code='BUSINESS',status='ACTIVE',
  valid_from=now()-interval '2 days',valid_until=now()+interval '7 days'
where shop_id='33333333-3333-4333-8333-333333333333';
alter table public.job_outbox
  add constraint disposable_render_outbox_failure check (kind <> 'render') not valid;
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
do $$
begin
  begin
    perform public.request_reel_render_job(
      '44444444-4444-4444-8444-444444444444',
      '88888888-8888-4888-8888-888888888888');
    raise exception 'render returned success while outbox INSERT blocked';
  exception when check_violation then null;
  end;
end $$;
reset role;
do $$
begin
  if (select count(*) from public.render_jobs)<>2
     or (select count(*) from public.shop_usage_reservations where operation='render')<>2
     or (select count(*) from public.job_outbox where kind='render')<>2 then
    raise exception 'failed outbox persisted orphaned job or quota reservation';
  end if;
end $$;
alter table public.job_outbox drop constraint disposable_render_outbox_failure;
-- Final stale state: planner has reclaimed the campaign, no Reel mutation.
update public.campaigns set status='PLANNING'
 where id='44444444-4444-4444-8444-444444444444';
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
do $$
begin
  if public.request_reel_render_job(
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888') is not null then
    raise exception 'non-DRAFT campaign allowed stale render';
  end if;
end $$;

rollback;
\echo 'PASS: Python SHA256, legacy reuse, 2-session gate separate, tenant/VIEWER/license denial, quota exhaustion, expired subscription, revoked membership, outbox-rollback atomicity, non-DRAFT denial'

