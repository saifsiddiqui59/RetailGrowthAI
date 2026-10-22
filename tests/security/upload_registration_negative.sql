-- Disposable local Supabase test. Synthetic Storage records; transaction rolls back.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('a1111111-1111-4111-8111-111111111111','00000000-0000-0000-0000-000000000000','authenticated','authenticated','upload-a@example.invalid','!',now(),now()),
('b2222222-2222-4222-8222-222222222222','00000000-0000-0000-0000-000000000000','authenticated','authenticated','upload-b@example.invalid','!',now(),now()),
('c3333333-3333-4333-8333-333333333333','00000000-0000-0000-0000-000000000000','authenticated','authenticated','upload-viewer@example.invalid','!',now(),now());
set local role authenticated;
select set_config('request.jwt.claim.sub','a1111111-1111-4111-8111-111111111111',true);
insert into public.shops(id,owner_user_id,name,slug)
values('d4444444-4444-4444-8444-444444444444','a1111111-1111-4111-8111-111111111111','Upload owner A','rg-upload-a');
insert into public.shop_memberships(shop_id,user_id,role)
values('d4444444-4444-4444-8444-444444444444','c3333333-3333-4333-8333-333333333333','VIEWER');
insert into storage.objects(bucket_id,name,owner_id,metadata)
values(
'retailgrowth-media',
'd4444444-4444-4444-8444-444444444444/uploads/e5555555-5555-4555-8555-555555555555.png',
'a1111111-1111-4111-8111-111111111111',
'{"mimetype":"image/png","size":2048}'::jsonb
);
insert into storage.objects(bucket_id,name,owner_id,metadata)
values(
'retailgrowth-media',
'd4444444-4444-4444-8444-444444444444/uploads/f6666666-6666-4666-8666-666666666666.png',
'b2222222-2222-4222-8222-222222222222',
'{"mimetype":"image/png","size":2048}'::jsonb
);
insert into storage.objects(bucket_id,name,owner_id,metadata)
values(
'retailgrowth-media',
'd4444444-4444-4444-8444-444444444444/uploads/a7777777-7777-4777-8777-777777777777.png',
'a1111111-1111-4111-8111-111111111111',
'{"mimetype":"application/octet-stream","size":2048}'::jsonb
);

do $$
declare
  asset_id uuid; rejection boolean := false; changed integer;
  target_path text := 'd4444444-4444-4444-8444-444444444444/uploads/e5555555-5555-4555-8555-555555555555.png';
begin
  begin
    insert into public.media_assets(shop_id,created_by,object_path,mime_type,source,license_name)
    values('d4444444-4444-4444-8444-444444444444',
           'a1111111-1111-4111-8111-111111111111',
           'd4444444-4444-4444-8444-444444444444/uploads/fake.png',
           'image/png','UPLOAD','owned');
  exception when insufficient_privilege then rejection := true;
  end;
  if not rejection then raise exception 'FAIL: direct authenticated media INSERT allowed'; end if;

  asset_id := public.register_uploaded_image(
    'd4444444-4444-4444-8444-444444444444',
    target_path, 'owned', null, 'Original photo shot by the business owner');
  if asset_id is null or not exists (
    select 1 from public.media_assets a
     where a.id = asset_id
       and a.shop_id='d4444444-4444-4444-8444-444444444444'
       and a.created_by='a1111111-1111-4111-8111-111111111111'
       and a.source='UPLOAD' and a.mime_type='image/png'
  ) then raise exception 'FAIL: authorized uploaded object not registered'; end if;

  -- A registered blob is immutable through user-facing Storage policies.
  -- This protects the registered MIME, identity and rights evidence.
  changed := -1;
  begin
    update storage.objects
       set metadata='{"mimetype":"image/jpeg","size":300}'::jsonb
     where bucket_id='retailgrowth-media' and name=target_path;
    get diagnostics changed = row_count;
  exception when insufficient_privilege then changed := 0;
  end;
  if changed <> 0 then raise exception 'FAIL: registered image overwritten'; end if;

  changed := -1;
  begin
    delete from storage.objects
     where bucket_id='retailgrowth-media' and name=target_path;
    get diagnostics changed = row_count;
  exception when insufficient_privilege then changed := 0;
  end;
  if changed <> 0 then raise exception 'FAIL: registered storage object deleted'; end if;

  -- Deleting the database registration first must not bypass Storage protection.
  changed := -1;
  begin
    delete from public.media_assets where id=asset_id;
    get diagnostics changed = row_count;
  exception when insufficient_privilege then changed := 0;
  end;
  if changed <> 0 then raise exception 'FAIL: user removed media registration'; end if;
  if not exists (select 1 from public.media_assets where id=asset_id) then
    raise exception 'FAIL: registered metadata vanished';
  end if;

  if public.register_uploaded_image(
    'd4444444-4444-4444-8444-444444444444',
    target_path, 'owned', null, 'Duplicate owned photograph') is not null then
    raise exception 'FAIL: duplicate registration accepted'; end if;
  if public.register_uploaded_image(
    'd4444444-4444-4444-8444-444444444444',
    'd4444444-4444-4444-8444-444444444444/uploads/f6666666-6666-4666-8666-666666666666.png',
    'owned', null, 'Other uploader media object') is not null then
    raise exception 'FAIL: another user storage object registered'; end if;
  if public.register_uploaded_image(
    'd4444444-4444-4444-8444-444444444444',
    'd4444444-4444-4444-8444-444444444444/uploads/a7777777-7777-4777-8777-777777777777.png',
    'owned', null, 'Bad MIME photo' ) is not null then
    raise exception 'FAIL: unsupported MIME accepted'; end if;
  if public.register_uploaded_image(
    'd4444444-4444-4444-8444-444444444444',
    'd4444444-4444-4444-8444-444444444444/uploads/missing.png',
    'owned', null, 'Missing object evidence') is not null then
    raise exception 'FAIL: missing object accepted'; end if;
  if public.register_uploaded_image(
    'd4444444-4444-4444-8444-444444444444',
    target_path, 'commercial', 'http://invalid/license', 'Vendor license on file') is not null then
    raise exception 'FAIL: non-HTTPS rights evidence accepted'; end if;
end $$;

select set_config('request.jwt.claim.sub','c3333333-3333-4333-8333-333333333333',true);
do $$
begin
  if public.register_uploaded_image(
    'd4444444-4444-4444-8444-444444444444',
    'd4444444-4444-4444-8444-444444444444/uploads/e5555555-5555-4555-8555-555555555555.png',
    'owned', null, 'Viewer cannot register image') is not null then
      raise exception 'FAIL: viewer registered media'; end if;
end $$;

select set_config('request.jwt.claim.sub','b2222222-2222-4222-8222-222222222222',true);
insert into public.shops(id,owner_user_id,name,slug)
values('b8888888-8888-4888-8888-888888888888','b2222222-2222-4222-8222-222222222222','Upload owner B','rg-upload-b');
do $$
begin
  if public.register_uploaded_image(
    'd4444444-4444-4444-8444-444444444444',
    'd4444444-4444-4444-8444-444444444444/uploads/e5555555-5555-4555-8555-555555555555.png',
    'owned', null, 'Cross-shop register attempt') is not null then
      raise exception 'FAIL: cross-shop registration allowed'; end if;
end $$;
reset role;
set local role anon;
select set_config('request.jwt.claim.sub','',true);
do $$
declare denied boolean := false;
begin
  begin
    perform public.register_uploaded_image(
      'd4444444-4444-4444-8444-444444444444',
      'd4444444-4444-4444-8444-444444444444/uploads/e5555555-5555-4555-8555-555555555555.png',
      'owned', null, 'Anonymous registration');
  exception when insufficient_privilege then denied := true;
  end;
  if not denied then raise exception 'FAIL: anonymous RPC execute allowed'; end if;
end $$;
reset role;
rollback;
\echo 'PASS: authenticated object binding, owner, tenant, MIME, rights and anon denial'
