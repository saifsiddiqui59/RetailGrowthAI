-- Feature3 offline disposable Supabase DB only; rollback, no hosted records.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at) values
('a3000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3owner@example.invalid','!',now(),now()),
('a3000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3viewer@example.invalid','!',now(),now()),
('a3000000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3foreign@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','a3000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('a3000000-0000-4000-8000-000000000011','a3000000-0000-4000-8000-000000000001','Feature3 shop','f3-test-private');
insert into public.shop_memberships(shop_id,user_id,role)
values('a3000000-0000-4000-8000-000000000011','a3000000-0000-4000-8000-000000000002','VIEWER');
reset role;
insert into public.campaigns(id,shop_id,created_by,brief,start_date,status)
values('a3000000-0000-4000-8000-000000000012','a3000000-0000-4000-8000-000000000011',
'a3000000-0000-4000-8000-000000000001','Approved brand campaign','2026-11-01','DRAFT');
insert into public.campaign_days(id,campaign_id,shop_id,day_index,scheduled_date,topic)
values('a3000000-0000-4000-8000-000000000013','a3000000-0000-4000-8000-000000000012',
'a3000000-0000-4000-8000-000000000011',1,'2026-11-01','Approved brand topic');
insert into public.media_assets(
id,shop_id,created_by,object_path,mime_type,source,license_name,attribution
) values(
'a3000000-0000-4000-8000-000000000014','a3000000-0000-4000-8000-000000000011',
'a3000000-0000-4000-8000-000000000001',
'a3000000-0000-4000-8000-000000000011/uploads/a3000000-0000-4000-8000-000000000014.png',
'image/png','UPLOAD','owned','Synthetic image owned by test merchant'
);
insert into public.feature3_models(model_id,owner_shop_id,created_by,media_asset_id,
 scope,source_kind,label,image_sha256,license_id,license_evidence_sha256)
values('a3000000-0000-4000-8000-000000000015','a3000000-0000-4000-8000-000000000011',
'a3000000-0000-4000-8000-000000000001','a3000000-0000-4000-8000-000000000014',
'shop','retailer_licensed','Synthetic local reference',repeat('a',64),'CC0-1.0',repeat('b',64));

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','a3000000-0000-4000-8000-000000000001',true);
do $$
declare design jsonb;
        saved_id uuid;
        v jsonb;
        rejected boolean:=false;
begin
 design := '{"schema":"retailgrowth.poster.v2","shop_id":"a3000000-0000-4000-8000-000000000011",
 "format":"square","template":"fashion","background":"#FFFFFF",
 "layers":[{"id":"headline","type":"text","x":0.1,"y":0.2,"w":0.8,"h":0.2,
 "text":"A genuine product message","color":"#333333","font_size":36,"bold":true}]}'::jsonb;
 v := public.save_feature3_poster_design(
 'a3000000-0000-4000-8000-000000000011','a3000000-0000-4000-8000-000000000012',
 'a3000000-0000-4000-8000-000000000013', design);
 if v is null or v->>'revision'<>'1' then raise exception 'FAIL: valid owner v2 draft rejected'; end if;
 saved_id := (v->>'design_id')::uuid;
 if not exists (select 1 from public.feature3_poster_designs pd where pd.id=saved_id) then
    raise exception 'FAIL: owner cannot see new draft'; end if;
 if public.save_feature3_poster_design(
 'a3000000-0000-4000-8000-000000000011','a3000000-0000-4000-8000-000000000012',
 'a3000000-0000-4000-8000-000000000013',design,saved_id,0) is not null then
    raise exception 'FAIL: stale compare-and-swap overwrote draft'; end if;
 v := public.save_feature3_poster_design(
 'a3000000-0000-4000-8000-000000000011','a3000000-0000-4000-8000-000000000012',
 'a3000000-0000-4000-8000-000000000013',design,saved_id,1);
 if v->>'revision'<>'2' then raise exception 'FAIL: valid compare-and-swap update denied'; end if;
 if public.save_feature3_poster_design(
 'a3000000-0000-4000-8000-000000000011','a3000000-0000-4000-8000-000000000012',
 'a3000000-0000-4000-8000-000000000013',
 jsonb_set(design,'{layers,0,text}',to_jsonb('Forged offer'::text)),saved_id,1)
 is not null then raise exception 'FAIL: stale edit accepted'; end if;
 if public.save_feature3_poster_design(
 'a3000000-0000-4000-8000-000000000011','a3000000-0000-4000-8000-000000000012',
 'a3000000-0000-4000-8000-000000000013',
 jsonb_set(design,'{layers,0,image_url}',to_jsonb('https://evil.invalid/photo'::text)))
 is not null then raise exception 'FAIL: forbidden remote URL accepted'; end if;
 if public.save_feature3_poster_design(
 'a3000000-0000-4000-8000-000000000011','a3000000-0000-4000-8000-000000000012',
 'a3000000-0000-4000-8000-000000000013',
 jsonb_set(design,'{layers}', '[{"id":"photo","type":"image","x":0,"y":0,"w":1,"h":1,
 "asset_id":"a3000000-0000-4000-8000-000000000099"}]'::jsonb))
 is not null then raise exception 'FAIL: nonexistent media accepted'; end if;
 begin
   insert into public.feature3_models(model_id,owner_shop_id,created_by,media_asset_id,
     scope,source_kind,label,image_sha256,license_id,license_evidence_sha256)
   values(gen_random_uuid(),'a3000000-0000-4000-8000-000000000011',
   'a3000000-0000-4000-8000-000000000001','a3000000-0000-4000-8000-000000000014',
   'platform','opensource_render','Fake globally licensed',repeat('f',64),'CC0-1.0',repeat('f',64));
 exception when insufficient_privilege then rejected:=true; end;
 if not rejected then raise exception 'FAIL: self-issued platform model approval'; end if;
 rejected:=false;
 begin
   update public.feature3_poster_designs set status='APPROVED' where id=saved_id;
 exception when insufficient_privilege then rejected:=true; end;
 if not rejected then raise exception 'FAIL: client promoted draft'; end if;
end $$;
select set_config('request.jwt.claim.sub','a3000000-0000-4000-8000-000000000002',true);
do $$
declare design jsonb;
begin
 if (select count(*) from public.feature3_poster_designs) <> 1 then
   raise exception 'FAIL: same-shop viewer cannot read drafts'; end if;
 design := '{"schema":"retailgrowth.poster.v2","shop_id":"a3000000-0000-4000-8000-000000000011",
 "format":"square","template":"fashion","background":"#FFFFFF",
 "layers":[{"id":"headline","type":"text","x":0.1,"y":0.2,"w":0.8,"h":0.2,
 "text":"Try to write","color":"#333333","font_size":36,"bold":true}]}'::jsonb;
 if public.save_feature3_poster_design(
 'a3000000-0000-4000-8000-000000000011','a3000000-0000-4000-8000-000000000012',
 'a3000000-0000-4000-8000-000000000013',design) is not null then
   raise exception 'FAIL: VIEWER wrote draft'; end if;
end $$;
select set_config('request.jwt.claim.sub','a3000000-0000-4000-8000-000000000003',true);
do $$
begin
 if (select count(*) from public.feature3_models) <> 0 or
    (select count(*) from public.feature3_poster_designs) <> 0 then
   raise exception 'FAIL: foreign shop saw private catalog/design'; end if;
end $$;
set local role anon;
select set_config('request.jwt.claim.role','anon',true);
select set_config('request.jwt.claim.sub','',true);
do $$
declare denied boolean:=false;
begin
 begin
   perform public.save_feature3_poster_design(
     'a3000000-0000-4000-8000-000000000011',
     'a3000000-0000-4000-8000-000000000012',
     'a3000000-0000-4000-8000-000000000013','{}'::jsonb);
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'FAIL: anon can call protected save RPC'; end if;
end $$;
reset role;
rollback;
\echo 'PASS: Feature3 tenant catalog metadata/private model, v2 CAS, viewer/foreign/anon denial, immutable client approval'
