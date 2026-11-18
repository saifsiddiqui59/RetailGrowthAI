-- Disposable-only fictional PNG Storage metadata. No image binary, rights or GPU.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('f3000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3-src-owner@example.invalid','!',now(),now()),
('f3000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3-src-viewer@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f3000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f3000000-0000-4000-8000-000000000011',
'f3000000-0000-4000-8000-000000000001','Fictional approved original fixture','f3-source-fixture');
insert into public.shop_memberships(shop_id,user_id,role) values
('f3000000-0000-4000-8000-000000000011',
'f3000000-0000-4000-8000-000000000002','VIEWER');
reset role;

insert into storage.objects(bucket_id,name,metadata,owner_id)
values('retailgrowth-media',
'f3000000-0000-4000-8000-000000000011/model-library/f3000000-0000-4000-8000-000000000031/'||repeat('a',64)||'.png',
jsonb_build_object('mimetype','image/png','size','32768'),
'f3000000-0000-4000-8000-000000000001');

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f3000000-0000-4000-8000-000000000002',true);
do $test$
begin
 if public.feature3_register_model_original(
 'f3000000-0000-4000-8000-000000000011',
 'f3000000-0000-4000-8000-000000000031',
 repeat('a',64),'owned',null,'Fictional model PNG original') is not null then
   raise exception 'FAIL: VIEWER registered model';
 end if;
end $test$;
select set_config('request.jwt.claim.sub','f3000000-0000-4000-8000-000000000001',true);

-- Real RLS insertion contract (not just fake SQL registration): the current
-- signed OWNER can create a new immutable canonical model-library PNG. VIEWER,
-- foreign, wrong-hash paths and generated GPU namespaces must be denied.
do $storage_rls$
declare denied boolean;
begin
 insert into storage.objects(bucket_id,name,owner_id,metadata)
 values('retailgrowth-media',
 'f3000000-0000-4000-8000-000000000011/model-library/f3000000-0000-4000-8000-000000000032/'||repeat('c',64)||'.png',
 'f3000000-0000-4000-8000-000000000001',
 '{"mimetype":"image/png","size":4096}'::jsonb);
 denied:=false;
 begin
  insert into storage.objects(bucket_id,name,owner_id,metadata)
  values('retailgrowth-media',
  'f3000000-0000-4000-8000-000000000011/model-library/f3000000-0000-4000-8000-000000000033/'||repeat('d',64)||'.png',
  'f3000000-0000-4000-8000-000000000002',
  '{"mimetype":"image/png","size":4096}'::jsonb);
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'FAIL: owner forged another model-original Storage owner'; end if;
 denied:=false;
 begin
  insert into storage.objects(bucket_id,name,owner_id,metadata)
  values('retailgrowth-media',
  'f3000000-0000-4000-8000-000000000011/model-library/f3000000-0000-4000-8000-000000000034/bad.png',
  'f3000000-0000-4000-8000-000000000001',
  '{"mimetype":"image/png","size":4096}'::jsonb);
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'FAIL: noncanonical model-original SHA accepted'; end if;
 denied:=false;
 begin
  insert into storage.objects(bucket_id,name,owner_id,metadata)
  values('retailgrowth-media',
  'f3000000-0000-4000-8000-000000000011/feature3/gpu/f3000000-0000-4000-8000-000000000035/'||repeat('e',64)||'.png',
  'f3000000-0000-4000-8000-000000000001',
  '{"mimetype":"image/png","size":4096}'::jsonb);
 exception when insufficient_privilege then denied:=true;
 end;
 if not denied then raise exception 'FAIL: browser uploaded generated GPU output'; end if;
end $storage_rls$;

do $test$
declare
 r jsonb;
 media uuid;
begin
 r:=public.feature3_register_model_original(
 'f3000000-0000-4000-8000-000000000011',
 'f3000000-0000-4000-8000-000000000031',
 repeat('b',64),'owned',null,'Fictional model PNG original');
 if r is not null then raise exception 'FAIL: replaced source SHA accepted'; end if;
 r:=public.feature3_register_model_original(
 'f3000000-0000-4000-8000-000000000011',
 'f3000000-0000-4000-8000-000000000031',
 repeat('a',64),'owned',null,'Fictional model PNG original');
 if r is null or r->>'status'<>'SOURCE_REGISTERED_PENDING_EVIDENCE' or
     r->>'byte_sha_verified'<>'false' or r->>'license_verified'<>'false' or
     r->>'gpu_authorized'<>'false' then
   raise exception 'FAIL: original registration falsely verified source';
 end if;
 media:=(r->>'media_asset_id')::uuid;
 if (select count(*) from public.media_assets where id=media
   and source='UPLOAD' and shop_id='f3000000-0000-4000-8000-000000000011')<>1 then
   raise exception 'FAIL: original same-tenant media row missing';
 end if;
 r:=public.feature3_register_model_original(
 'f3000000-0000-4000-8000-000000000011',
 'f3000000-0000-4000-8000-000000000031',
 repeat('a',64),'owned',null,'Fictional model PNG original');
 if r is not null then raise exception 'FAIL: repeated model original registration'; end if;
 r:=public.feature3_import_pending_model(
 'f3000000-0000-4000-8000-000000000011',
 'f3000000-0000-4000-8000-000000000031',
 media,'retailer_licensed','Fictional adult model',
 repeat('a',64),'REVIEWED-COMMERCIAL',repeat('b',64),
 'Fictional studio-owned garment portrait',array['poster','try_on']);
 if r is null or r->>'status'<>'PENDING_REVIEW' or
   r->>'rights_verified'<>'false' then
   raise exception 'FAIL: original-to-pending import signed source path';
 end if;
end $test$;
reset role;
do $test$
begin
 if has_function_privilege('anon',
  'public.feature3_register_model_original(uuid,uuid,text,text,text,text)','EXECUTE')
  or has_table_privilege('authenticated','public.media_assets','INSERT') then
    raise exception 'FAIL: public model original direct write';
 end if;
end $test$;
rollback;
\echo 'PASS: Source-only signed model original registration, pending importer, viewer/duplicate/SHA denied'
