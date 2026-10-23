-- Runs only against CI's disposable Supabase instance. Never hosted projects.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('11111111-1111-4111-8111-111111111111','00000000-0000-0000-0000-000000000000','authenticated','authenticated','draft-a@example.invalid','!',now(),now()),
('22222222-2222-4222-8222-222222222222','00000000-0000-0000-0000-000000000000','authenticated','authenticated','draft-b@example.invalid','!',now(),now());
set local role authenticated;
-- Simulate the signed JWT role accurately for auth.role() in guarded triggers.
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
insert into public.shops(id,owner_user_id,name,slug)
values('33333333-3333-4333-8333-333333333333','11111111-1111-4111-8111-111111111111','Draft A','rg-draft-shop-a');
insert into public.shop_memberships(shop_id,user_id,role)
values('33333333-3333-4333-8333-333333333333','22222222-2222-4222-8222-222222222222','VIEWER');
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values('44444444-4444-4444-8444-444444444444','33333333-3333-4333-8333-333333333333',
'11111111-1111-4111-8111-111111111111','Seven day campaign','2026-11-01');
reset role;
update public.campaigns set status='DRAFT' where id='44444444-4444-4444-8444-444444444444';
insert into public.campaign_days(id,shop_id,campaign_id,day_index,scheduled_date,topic,linkedin,instagram)
values(
'55555555-5555-4555-8555-555555555555',
'33333333-3333-4333-8333-333333333333',
'44444444-4444-4444-8444-444444444444',
1,'2026-11-01','Before',
'{"post_text":"Original content","hashtags":["#Sample"]}'::jsonb,
'{"caption":"Original caption","banner_asset_id":null,"reel":{"duration_seconds":30,"aspect_ratio":"9:16","storyboard":[],"music_asset_id":null,"cta":"Visit"}}'::jsonb
);
set local role authenticated;
-- Simulate the signed JWT role accurately for auth.role() in guarded triggers.
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
do $$
declare
  was_saved boolean;
  previous jsonb := jsonb_build_object(
    'topic','Before',
    'linkedin','{"post_text":"Original content","hashtags":["#Sample"]}'::jsonb,
    'instagram','{"caption":"Original caption","banner_asset_id":null,"reel":{"duration_seconds":30,"aspect_ratio":"9:16","storyboard":[],"music_asset_id":null,"cta":"Visit"}}'::jsonb);
  revision jsonb;
  rejected boolean := false;
begin
  revision := jsonb_set(previous,'{topic}','"After"'::jsonb);
  was_saved := public.save_campaign_day(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '55555555-5555-4555-8555-555555555555',previous,revision);
  if was_saved is distinct from true then raise exception 'FAIL: owner save denied'; end if;
  if public.save_campaign_day(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '55555555-5555-4555-8555-555555555555',previous,revision) is not false then
    raise exception 'FAIL: stale edit overwrote newer content';
  end if;
  if (select topic from public.campaign_days where id='55555555-5555-4555-8555-555555555555') <> 'After' then
    raise exception 'FAIL: draft did not persist';
  end if;
  begin
    update public.campaign_days set topic='BYPASS' where id='55555555-5555-4555-8555-555555555555';
  exception when insufficient_privilege then rejected := true;
  end;
  if not rejected then raise exception 'FAIL: direct browser update allowed'; end if;
end $$;

select set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true);
do $$
begin
  if public.save_campaign_day(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '55555555-5555-4555-8555-555555555555',
    '{"topic":"After","linkedin":{},"instagram":{}}'::jsonb,
    '{"topic":"STOLEN","linkedin":{},"instagram":{}}'::jsonb
  ) is not false then raise exception 'FAIL: viewer edited a draft'; end if;
end $$;

reset role;
insert into public.render_jobs(id,shop_id,campaign_id,day_id,requested_by,preset,idempotency_key)
values(
'66666666-6666-4666-8666-666666666666',
'33333333-3333-4333-8333-333333333333',
'44444444-4444-4444-8444-444444444444',
'55555555-5555-4555-8555-555555555555',
'11111111-1111-4111-8111-111111111111','instagram_reel_30s','test-render-queue');
set local role authenticated;
-- Simulate the signed JWT role accurately for auth.role() in guarded triggers.
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
do $$
begin
  if public.save_campaign_day(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '55555555-5555-4555-8555-555555555555',
    '{"topic":"After","linkedin":{"post_text":"Original content","hashtags":["#Sample"]},"instagram":{"caption":"Original caption","banner_asset_id":null,"reel":{"duration_seconds":30,"aspect_ratio":"9:16","storyboard":[],"music_asset_id":null,"cta":"Visit"}}}'::jsonb,
    '{"topic":"After render","linkedin":{},"instagram":{}}'::jsonb
  ) is not false then raise exception 'FAIL: edit allowed during queued render'; end if;
end $$;
reset role;
rollback;
\echo 'PASS: draft save owner, viewer denial, stale-write, direct-bypass and queued-render tests'
