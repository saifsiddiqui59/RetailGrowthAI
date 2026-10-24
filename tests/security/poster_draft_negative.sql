-- Disposable CI-only role/rights regression for poster draft metadata.
-- Every write is transactionally rolled back. Never run against hosted DEV.
\set ON_ERROR_STOP on
begin;

insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('11111111-1111-4111-8111-111111111111','00000000-0000-0000-0000-000000000000','authenticated','authenticated','poster-owner@example.invalid','!',now(),now()),
('22222222-2222-4222-8222-222222222222','00000000-0000-0000-0000-000000000000','authenticated','authenticated','poster-viewer@example.invalid','!',now(),now()),
('99999999-9999-4999-8999-999999999999','00000000-0000-0000-0000-000000000000','authenticated','authenticated','poster-foreign@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
insert into public.shops(id,owner_user_id,name,slug)
values('33333333-3333-4333-8333-333333333333',
'11111111-1111-4111-8111-111111111111','Poster shop','rg-poster-a');
insert into public.shop_memberships(shop_id,user_id,role)
values('33333333-3333-4333-8333-333333333333',
'22222222-2222-4222-8222-222222222222','VIEWER');

reset role;
select set_config('request.jwt.claim.role','service_role',true);
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values('44444444-4444-4444-8444-444444444444',
'33333333-3333-4333-8333-333333333333',
'11111111-1111-4111-8111-111111111111','Create owned post','2026-11-01');
update public.campaigns set status='DRAFT'
where id='44444444-4444-4444-8444-444444444444';
insert into public.media_assets(
 id,shop_id,created_by,object_path,mime_type,source,license_name,attribution
) values
('55555555-5555-4555-8555-555555555555',
'33333333-3333-4333-8333-333333333333',
'11111111-1111-4111-8111-111111111111',
'33333333-3333-4333-8333-333333333333/uploads/55555555-5555-4555-8555-555555555555.png',
'image/png','UPLOAD','owned','Photo owned by poster merchant'),
('66666666-6666-4666-8666-666666666666',
'33333333-3333-4333-8333-333333333333',
'11111111-1111-4111-8111-111111111111',
'33333333-3333-4333-8333-333333333333/uploads/66666666-6666-4666-8666-666666666666.png',
'image/png','UPLOAD','owned','Unreferenced photo owned by merchant'),
('77777777-7777-4777-8777-777777777777',
'33333333-3333-4333-8333-333333333333',
'11111111-1111-4111-8111-111111111111',
'33333333-3333-4333-8333-333333333333/uploads/77777777-7777-4777-8777-777777777777.png',
'image/png','UPLOAD','owned',null);
insert into public.campaign_days(
 id,campaign_id,shop_id,day_index,scheduled_date,topic,linkedin,instagram
) values(
'88888888-8888-4888-8888-888888888888',
'44444444-4444-4444-8444-444444444444',
'33333333-3333-4333-8333-333333333333',
1,'2026-11-01','Everyday Clothing','{}'::jsonb,
'{"caption":"A new wardrobe","banner_asset_id":null,"reel":{"duration_seconds":30,"aspect_ratio":"9:16","storyboard":[{"asset_id":"55555555-5555-4555-8555-555555555555","overlay_text":"New season","start_seconds":0,"duration_seconds":30}],"music_asset_id":null,"cta":"Shop now"}}'::jsonb
);

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);

do $$
declare
  first_id uuid;
  duplicate_id uuid;
  rejected boolean := false;
begin
  first_id := public.create_poster_draft(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888',
    '55555555-5555-4555-8555-555555555555',
    null,'editorial','portrait','Clothing Studio','#AA6644','#F5F0E8',null);
  if first_id is null then raise exception 'FAIL: licensed owner poster denied'; end if;

  duplicate_id := public.create_poster_draft(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888',
    '55555555-5555-4555-8555-555555555555',
    null,'editorial','portrait','Clothing Studio','#AA6644','#F5F0E8',null);
  if duplicate_id is distinct from first_id then
    raise exception 'FAIL: identical request created duplicate poster';
  end if;

  if (select count(*) from public.poster_drafts where shop_id=
      '33333333-3333-4333-8333-333333333333') <> 1 then
    raise exception 'FAIL: poster idempotency not enforced';
  end if;

  if public.create_poster_draft(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888',
    '66666666-6666-4666-8666-666666666666',
    null,'editorial','portrait','Clothing Studio','#AA6644','#F5F0E8',null) is not null then
    raise exception 'FAIL: unreferenced photo accepted';
  end if;

  if public.create_poster_draft(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888',
    '55555555-5555-4555-8555-555555555555',
    '77777777-7777-4777-8777-777777777777',
    'bold','square','Clothing Studio','#AA6644','#F5F0E8',null) is not null then
    raise exception 'FAIL: logo missing rights evidence accepted';
  end if;

  if public.create_poster_draft(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888',
    '55555555-5555-4555-8555-555555555555',
    null,'invalid','square','Clothing Studio','#AA6644','#F5F0E8',null) is not null then
    raise exception 'FAIL: invalid preset accepted';
  end if;

  begin
    update public.poster_drafts set status='READY' where id=first_id;
  exception when insufficient_privilege then rejected := true;
  end;
  if not rejected then raise exception 'FAIL: browser promoted own poster to READY'; end if;
end $$;

select set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true);
do $$
begin
  if public.create_poster_draft(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888',
    '55555555-5555-4555-8555-555555555555',
    null,'minimal','square','Viewer bypass','#AA6644','#F5F0E8',null) is not null then
    raise exception 'FAIL: viewer created a poster';
  end if;
  if (select count(*) from public.poster_drafts where shop_id=
      '33333333-3333-4333-8333-333333333333') <> 1 then
    raise exception 'FAIL: viewer lost legitimate read access';
  end if;
end $$;

select set_config('request.jwt.claim.sub','99999999-9999-4999-8999-999999999999',true);
do $$
begin
  if public.create_poster_draft(
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '88888888-8888-4888-8888-888888888888',
    '55555555-5555-4555-8555-555555555555',
    null,'bold','square','Cross tenant','#AA6644','#F5F0E8',null) is not null then
    raise exception 'FAIL: foreign user created a poster';
  end if;
  if (select count(*) from public.poster_drafts) <> 0 then
    raise exception 'FAIL: foreign user could read poster drafts';
  end if;
end $$;

set local role anon;
select set_config('request.jwt.claim.role','anon',true);
select set_config('request.jwt.claim.sub','',true);
do $$
declare
  rejected boolean := false;
begin
  begin
    perform public.create_poster_draft(
      '33333333-3333-4333-8333-333333333333',
      '44444444-4444-4444-8444-444444444444',
      '88888888-8888-4888-8888-888888888888',
      '55555555-5555-4555-8555-555555555555',
      null,'bold','square','Anon','#AA6644','#F5F0E8',null);
  exception when insufficient_privilege then rejected := true;
  end;
  if not rejected then raise exception 'FAIL: anonymous RPC execution allowed'; end if;
end $$;

reset role;
select set_config('request.jwt.claim.role','service_role',true);
rollback;
\echo 'PASS: poster draft owner/idempotency, source rights, viewer/foreign/anon denial and immutable output'
