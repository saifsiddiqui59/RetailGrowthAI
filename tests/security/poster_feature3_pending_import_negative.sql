-- Feature3 signed PENDING_REVIEW model import. Disposable only; ROLLBACK.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('d3000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3-import-owner@example.invalid','!',now(),now()),
('d3000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3-import-viewer@example.invalid','!',now(),now()),
('d3000000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3-import-other@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','d3000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('d3000000-0000-4000-8000-000000000011',
'd3000000-0000-4000-8000-000000000001','Fictional private import','f3-import-private-1');
insert into public.shop_memberships(shop_id,user_id,role) values
('d3000000-0000-4000-8000-000000000011',
'd3000000-0000-4000-8000-000000000002','VIEWER');

select set_config('request.jwt.claim.sub','d3000000-0000-4000-8000-000000000003',true);
insert into public.shops(id,owner_user_id,name,slug)
values('d3000000-0000-4000-8000-000000000012',
'd3000000-0000-4000-8000-000000000003','Fictional other shop','f3-import-private-2');
reset role;

-- Fixture media row; the private PNG is NOT uploaded and is NOT rights-cleared.
insert into public.media_assets(id,shop_id,created_by,object_path,
 mime_type,source,license_name,attribution)
values('d3000000-0000-4000-8000-000000000021',
'd3000000-0000-4000-8000-000000000011',
'd3000000-0000-4000-8000-000000000001',
'd3000000-0000-4000-8000-000000000011/model-library/d3000000-0000-4000-8000-000000000031/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.png',
'image/png','UPLOAD','owned','Original fictional model photo test');

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','d3000000-0000-4000-8000-000000000002',true);
do $check$
declare r jsonb;
begin
 r:=public.feature3_import_pending_model(
  'd3000000-0000-4000-8000-000000000011',
  'd3000000-0000-4000-8000-000000000031',
  'd3000000-0000-4000-8000-000000000021',
  'retailer_licensed','Fictional model',repeat('a',64),
  'REVIEWED-COMMERCIAL',repeat('b',64),'Original fictional model portrait',
  array['poster','try_on']);
 if r is not null then raise exception 'FAIL: VIEWER imported model'; end if;
end $check$;
select set_config('request.jwt.claim.sub','d3000000-0000-4000-8000-000000000003',true);
do $check$
begin
 if public.feature3_import_pending_model(
  'd3000000-0000-4000-8000-000000000011',
  'd3000000-0000-4000-8000-000000000031',
  'd3000000-0000-4000-8000-000000000021',
  'retailer_licensed','Fictional model',repeat('a',64),
  'REVIEWED-COMMERCIAL',repeat('b',64),'Original fictional model portrait',
  array['poster']) is not null
 then raise exception 'FAIL: foreign tenant imported model'; end if;
end $check$;
select set_config('request.jwt.claim.sub','d3000000-0000-4000-8000-000000000001',true);
do $check$
declare
 r jsonb;
 shop uuid:='d3000000-0000-4000-8000-000000000011';
 model uuid:='d3000000-0000-4000-8000-000000000031';
 media uuid:='d3000000-0000-4000-8000-000000000021';
begin
 r:=public.feature3_import_pending_model(
  shop,model,media,'retailer_licensed','Fictional model',repeat('0',64),
  'REVIEWED-COMMERCIAL',repeat('b',64),'Original fictional model portrait',
  array['poster']);
 if r is not null then raise exception 'FAIL: original SHA mismatch imported'; end if;
 r:=public.feature3_import_pending_model(
  shop,model,media,'retailer_licensed','Fictional model',repeat('a',64),
  'REVIEWED-COMMERCIAL',repeat('b',64),'Original fictional model portrait',
  array['poster','poster']);
 if r is not null then raise exception 'FAIL: repeated approved use imported'; end if;
 r:=public.feature3_import_pending_model(
  shop,model,media,'retailer_licensed','Fictional model',repeat('a',64),
  'REVIEWED-COMMERCIAL',repeat('b',64),'Original fictional model portrait',
  array['poster','try_on','video_reference']);
 if r is null or r->>'status'<>'PENDING_REVIEW'
    or r->>'rights_verified'<>'false' or r->>'evidence_verified'<>'false'
    or r->>'gpu_authorized'<>'false' or r->>'rights_revision'<>'1'
 then raise exception 'FAIL: valid pending-only import not persisted'; end if;
 r:=public.feature3_import_pending_model(
  shop,model,media,'retailer_licensed','Fictional model',repeat('a',64),
  'REVIEWED-COMMERCIAL',repeat('b',64),'Original fictional model portrait',
  array['poster']);
 if r is not null then raise exception 'FAIL: duplicate import replay accepted'; end if;
end $check$;
reset role;

do $check$
begin
 if (select count(*) from public.feature3_models
   where model_id='d3000000-0000-4000-8000-000000000031'
   and owner_shop_id='d3000000-0000-4000-8000-000000000011'
   and status='PENDING_REVIEW' and rights_verified=false
   and rights_revision=1 and scope='shop')<>1
 then raise exception 'FAIL: pending model exact state'; end if;
 if (select count(*) from retail_private.feature3_model_evidence
   where model_id='d3000000-0000-4000-8000-000000000031')<>0
 then raise exception 'FAIL: import manufactured verified evidence'; end if;
 if has_table_privilege('authenticated','public.feature3_models','INSERT')
    or has_table_privilege('authenticated','public.feature3_models','UPDATE')
 then raise exception 'FAIL: authenticated direct model INSERT/UPDATE'; end if;
 if has_function_privilege('anon',
    'public.feature3_import_pending_model(uuid,uuid,uuid,text,text,text,text,text,text,text[])','EXECUTE')
 then raise exception 'FAIL: anonymous signed import exposed'; end if;
end $check$;
rollback;
\echo 'PASS: Feature3 signed pending model import, viewer/foreign/SHA/duplicate denied, no rights or GPU'
