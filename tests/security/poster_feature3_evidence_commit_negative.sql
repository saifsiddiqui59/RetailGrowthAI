-- P0: disposable Supabase test of service-only model evidence RPC, rollback.
-- Not licensed human evidence; SHA fixture is synthetic and does not exist
-- as a live Storage object. Real binary/rights inspection is server-owned.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at) values
('c3000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3e-owner@example.invalid','!',now(),now()),
('c3000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3e-viewer@example.invalid','!',now(),now()),
('c3000000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3e-other@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','c3000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('c3000000-0000-4000-8000-000000000011',
'c3000000-0000-4000-8000-000000000001','Evidence fixture shop','f3-evidence-fixture');
insert into public.shop_memberships(shop_id,user_id,role)
values('c3000000-0000-4000-8000-000000000011',
'c3000000-0000-4000-8000-000000000002','VIEWER');
select set_config('request.jwt.claim.sub','c3000000-0000-4000-8000-000000000003',true);
insert into public.shops(id,owner_user_id,name,slug)
values('c3000000-0000-4000-8000-000000000012',
'c3000000-0000-4000-8000-000000000003','Other evidence fixture','f3-evidence-other');
reset role;

insert into public.media_assets(
 id,shop_id,created_by,object_path,mime_type,source,license_name,attribution)
values(
 'c3000000-0000-4000-8000-000000000021',
 'c3000000-0000-4000-8000-000000000011',
 'c3000000-0000-4000-8000-000000000001',
 'c3000000-0000-4000-8000-000000000011/model-library/c3000000-0000-4000-8000-000000000031/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.png',
 'image/png','UPLOAD','owned','Only a test fixture image record');

insert into public.feature3_models(model_id,owner_shop_id,created_by,media_asset_id,
scope,source_kind,label,image_sha256,license_id,license_evidence_sha256)
values('c3000000-0000-4000-8000-000000000031',
'c3000000-0000-4000-8000-000000000011',
'c3000000-0000-4000-8000-000000000001',
'c3000000-0000-4000-8000-000000000021',
'shop','retailer_licensed','Fictional verified image',
repeat('a',64),'REVIEWED-COMMERCIAL',repeat('b',64));

-- A tenant OWNER may never write licensed evidence via browser RPC.
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','c3000000-0000-4000-8000-000000000001',true);
do $body$
declare denied boolean:=false;
begin
 begin
  perform public.feature3_commit_verified_evidence(
   'c3000000-0000-4000-8000-000000000011',
   'c3000000-0000-4000-8000-000000000031',
   'c3000000-0000-4000-8000-000000000021',
   'c3000000-0000-4000-8000-000000000001',
   repeat('a',64),repeat('b',64),'https://example.invalid/provenance',
   'front',true,true,true);
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'FAIL: authenticated fabricated trusted evidence'; end if;
end $body$;
reset role;

-- Trusted backend simulated as the database service_role, no bearer
-- impersonation of a retailer. All negative tests must produce null.
set local role service_role;
do $body$
declare
 v jsonb;
 shop uuid:='c3000000-0000-4000-8000-000000000011';
 model uuid:='c3000000-0000-4000-8000-000000000031';
 media uuid:='c3000000-0000-4000-8000-000000000021';
 owner uuid:='c3000000-0000-4000-8000-000000000001';
begin
 v:=public.feature3_commit_verified_evidence(
 shop,model,media,
 'c3000000-0000-4000-8000-000000000002',
 repeat('a',64),repeat('b',64),'https://example.invalid/provenance',
 'front',true,true,true);
 if v is not null then raise exception 'FAIL: VIEWER source attested'; end if;
 v:=public.feature3_commit_verified_evidence(
 shop,model,media,
 'c3000000-0000-4000-8000-000000000003',
 repeat('a',64),repeat('b',64),'https://example.invalid/provenance',
 'front',true,true,true);
 if v is not null then raise exception 'FAIL: foreign verifier attested'; end if;
 v:=public.feature3_commit_verified_evidence(
 shop,model,media,owner,
 repeat('0',64),repeat('b',64),'https://example.invalid/provenance',
 'front',true,true,true);
 if v is not null then raise exception 'FAIL: different original SHA accepted'; end if;
 v:=public.feature3_commit_verified_evidence(
 shop,model,media,owner,
 repeat('a',64),repeat('0',64),'https://example.invalid/provenance',
 'front',true,true,true);
 if v is not null then raise exception 'FAIL: different license evidence accepted'; end if;
 v:=public.feature3_commit_verified_evidence(
 shop,model,media,owner,
 repeat('a',64),repeat('b',64),'http://example.invalid/bad',
 'front',true,true,true);
 if v is not null then raise exception 'FAIL: unsafe provenance URL accepted'; end if;
 v:=public.feature3_commit_verified_evidence(
 shop,model,media,owner,
 repeat('a',64),repeat('b',64),'https://example.invalid/provenance',
 'front',true,false,true);
 if v is not null then raise exception 'FAIL: invalid commercial rights accepted'; end if;
 v:=public.feature3_commit_verified_evidence(
 shop,model,media,owner,
 repeat('a',64),repeat('b',64),'https://example.invalid/provenance',
 'front',null,true,true);
 if v is not null then raise exception 'FAIL: NULL adult check accepted'; end if;
 v:=public.feature3_commit_verified_evidence(
 shop,model,media,owner,
 null,repeat('b',64),'https://example.invalid/provenance',
 'front',true,true,true);
 if v is not null then raise exception 'FAIL: NULL original SHA accepted'; end if;

 v:=public.feature3_commit_verified_evidence(
 shop,model,media,owner,
 repeat('a',64),repeat('b',64),'https://example.invalid/provenance',
 'front',true,true,true);
 if v is null or v->>'persisted'<>'true' or v->>'evidence_revision'<>'1'
   or v->>'model_id'<>model::text
 then raise exception 'FAIL: valid one-time evidence commit'; end if;
 v:=public.feature3_commit_verified_evidence(
 shop,model,media,owner,
 repeat('a',64),repeat('b',64),'https://example.invalid/provenance',
 'front',true,true,true);
 if v is not null then raise exception 'FAIL: ambiguous duplicate evidence was replayed'; end if;
end $body$;
reset role;

do $body$
begin
 if (select count(*) from retail_private.feature3_model_evidence
     where model_id='c3000000-0000-4000-8000-000000000031')<>1
 then raise exception 'FAIL: evidence event count'; end if;
 if has_function_privilege('authenticated',
  'public.feature3_commit_verified_evidence(uuid,uuid,uuid,uuid,text,text,text,text,boolean,boolean,boolean)',
  'EXECUTE')
   or has_function_privilege('anon',
  'public.feature3_commit_verified_evidence(uuid,uuid,uuid,uuid,text,text,text,text,boolean,boolean,boolean)',
  'EXECUTE')
 then raise exception 'FAIL: public evidence permission'; end if;
 if has_table_privilege('authenticated',
  'retail_private.feature3_model_evidence','INSERT') then
  raise exception 'FAIL: browser can insert private evidence'; end if;
end $body$;
rollback;
\echo 'PASS: service-only Feature3 evidence identity / tenant / immutable commit / deny replay'
