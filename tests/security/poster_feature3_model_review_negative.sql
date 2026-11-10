-- Feature3 durable human review: disposable local Supabase only, rollback.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at) values
('b3000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3-review-owner@example.invalid','!',now(),now()),
('b3000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3-review-viewer@example.invalid','!',now(),now()),
('b3000000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3-review-other@example.invalid','!',now(),now()),
('b3000000-0000-4000-8000-000000000004','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f3-review-editor@example.invalid','!',now(),now());

-- Bootstrap shops through the REAL current signed owner, never superuser.
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','b3000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug) values
('b3000000-0000-4000-8000-000000000011',
 'b3000000-0000-4000-8000-000000000001','Model review shop','f3-model-review-test');
select set_config('request.jwt.claim.sub','b3000000-0000-4000-8000-000000000003',true);
insert into public.shops(id,owner_user_id,name,slug) values
('b3000000-0000-4000-8000-000000000012',
 'b3000000-0000-4000-8000-000000000003','Other shop','f3-other-review-test');
select set_config('request.jwt.claim.sub','b3000000-0000-4000-8000-000000000001',true);
insert into public.shop_memberships(shop_id,user_id,role) values
('b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000002','VIEWER'),
('b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000004','EDITOR');
reset role;

insert into public.media_assets(id,shop_id,created_by,object_path,mime_type,source,license_name,attribution)
values('b3000000-0000-4000-8000-000000000021',
'b3000000-0000-4000-8000-000000000011',
'b3000000-0000-4000-8000-000000000001',
'b3000000-0000-4000-8000-000000000011/model-library/b3000000-0000-4000-8000-000000000031/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.png',
'image/png','UPLOAD','owned','Reviewed fictional private model image');

insert into public.feature3_models(model_id,owner_shop_id,created_by,media_asset_id,
scope,status,source_kind,label,image_sha256,license_id,license_evidence_sha256,approved_uses)
values('b3000000-0000-4000-8000-000000000031',
'b3000000-0000-4000-8000-000000000011',
'b3000000-0000-4000-8000-000000000001',
'b3000000-0000-4000-8000-000000000021',
'shop','PENDING_REVIEW','retailer_licensed','Fictional adult model reference',
repeat('a',64),'REVIEWED-COMMERCIAL',repeat('b',64),
array['poster','try_on','video_reference']);

-- Even a direct service-role/postgres UPDATE cannot counterfeit approval
-- without a same-transaction reviewer event: this is not just an RPC check.
do $guard_test$
declare denied boolean := false;
begin
 begin
  update public.feature3_models set status='APPROVED',
   rights_verified=true,rights_revision=2
   where model_id='b3000000-0000-4000-8000-000000000031';
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'FAIL un-audited direct model promotion'; end if;
end $guard_test$;

-- Authentication alone cannot invent independent license verification.
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','b3000000-0000-4000-8000-000000000001',true);
do $$
declare r jsonb;
begin
 r := public.feature3_review_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 'APPROVE',1,repeat('a',64),1,
 '{"adult_synthetic":true,"approved_uses":true,"image_license":true,"likeness_and_consent":true,"private_media_integrity":true,"visual_quality":true}',
 'Real reviewer needs independent license proof');
 if r is not null then raise exception 'FAIL owner approved without independent evidence'; end if;
end $$;
reset role;

-- Simulates a *trusted worker's* verified private PNG+license record in local CI.
-- Not proof that real licensed media exists; browser cannot insert it.
insert into retail_private.feature3_model_evidence(
owner_shop_id,model_id,media_asset_id,image_sha256,license_id,
license_evidence_sha256,source_kind,source_uri,pose,
synthetic_adult_verified,component_rights_cleared,commercial_reuse_approved,verified_by)
values('b3000000-0000-4000-8000-000000000011',
'b3000000-0000-4000-8000-000000000031',
'b3000000-0000-4000-8000-000000000021',
repeat('a',64),'REVIEWED-COMMERCIAL',repeat('b',64),
'retailer_licensed','https://example.invalid/licensed-source','front',
true,true,true,'b3000000-0000-4000-8000-000000000004');

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
-- VIEWER is active same-shop but cannot approve.
select set_config('request.jwt.claim.sub','b3000000-0000-4000-8000-000000000002',true);
do $$
begin
 if public.feature3_review_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 'APPROVE',1,repeat('a',64),1,
 '{"adult_synthetic":true,"approved_uses":true,"image_license":true,"likeness_and_consent":true,"private_media_integrity":true,"visual_quality":true}',
 'Fake viewer tried to approve model') is not null
 then raise exception 'FAIL VIEWER approved'; end if;
end $$;
-- foreign user cannot approve another shop's image.
select set_config('request.jwt.claim.sub','b3000000-0000-4000-8000-000000000003',true);
do $$
begin
 if public.feature3_review_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 'APPROVE',1,repeat('a',64),1,
 '{"adult_synthetic":true,"approved_uses":true,"image_license":true,"likeness_and_consent":true,"private_media_integrity":true,"visual_quality":true}',
 'Fake other tenant tried to approve') is not null
 then raise exception 'FAIL foreign shop approved'; end if;
end $$;
select set_config('request.jwt.claim.sub','b3000000-0000-4000-8000-000000000001',true);
do $$
declare r jsonb; good jsonb:='{"adult_synthetic":true,"approved_uses":true,"image_license":true,"likeness_and_consent":true,"private_media_integrity":true,"visual_quality":true}'::jsonb;
begin
 if public.feature3_review_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 'APPROVE',1,repeat('a',64),1,
 jsonb_set(good,'{image_license}','false'::jsonb),
 'Reject claim when license check failed') is not null
 then raise exception 'FAIL false image license approved'; end if;
 if public.feature3_review_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 'APPROVE',1,repeat('c',64),1,good,
 'Mismatched image SHA cannot pass review') is not null
 then raise exception 'FAIL changed image SHA approved'; end if;
 if public.feature3_review_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 'APPROVE',1,repeat('a',64),1,'{"adult_synthetic":true}'::jsonb,
 'Incomplete six required checks denied') is not null
 then raise exception 'FAIL missing six checks approved'; end if;
 r := public.feature3_review_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 'APPROVE',1,repeat('a',64),1,good,
 'Human confirmed image rights and pose');
 if r is null or r->>'status'<>'APPROVED' or r->>'rights_revision'<>'2'
    or r->>'audit_persisted'<>'true' or
    coalesce(r->>'review_event_id','')='' then
   raise exception 'FAIL durable human approved CAS'; end if;
 if public.feature3_review_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 'APPROVE',1,repeat('a',64),1,good,
 'Replay exact initial human approval') is not null
 then raise exception 'FAIL duplicate approval'; end if;
 if public.feature3_revoke_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 1,repeat('a',64),'Stale revoked rights request') is not null
 then raise exception 'FAIL stale revision revoke'; end if;
end $$;
-- The editor can revoke a currently active model, not auto retry generation.
select set_config('request.jwt.claim.sub','b3000000-0000-4000-8000-000000000004',true);
do $$
declare r jsonb;
begin
 r := public.feature3_revoke_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 2,repeat('a',64),'Original commercial rights were withdrawn');
 if r is null or r->>'status'<>'REVOKED' or
  r->>'rights_revision'<>'3' or r->>'audit_persisted'<>'true'
 then raise exception 'FAIL approved model not durably revoked'; end if;
 if public.feature3_revoke_model(
 'b3000000-0000-4000-8000-000000000011','b3000000-0000-4000-8000-000000000031',
 2,repeat('a',64),'Attempted duplicate image revocation') is not null
 then raise exception 'FAIL duplicate revocation'; end if;
end $$;
reset role;

do $$
begin
 if (select status<>'REVOKED' or rights_verified or rights_revision<>3
  from public.feature3_models
  where model_id='b3000000-0000-4000-8000-000000000031') then
  raise exception 'FAIL final revoked rights not persisted'; end if;
 if (select count(*) from retail_private.feature3_model_review_events
 where model_id='b3000000-0000-4000-8000-000000000031')<>2
 then raise exception 'FAIL review audit events count'; end if;
 if has_table_privilege('authenticated','retail_private.feature3_model_evidence','INSERT')
 or has_table_privilege('authenticated','retail_private.feature3_model_review_events','INSERT')
 or has_table_privilege('authenticated','public.feature3_models','UPDATE')
 then raise exception 'FAIL untrusted browser write privilege'; end if;
end $$;
-- Authenticated caller cannot mutate private audit or source evidence.
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','b3000000-0000-4000-8000-000000000001',true);
do $$
declare denied boolean := false;
begin
 begin
  delete from retail_private.feature3_model_review_events
  where model_id='b3000000-0000-4000-8000-000000000031';
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'FAIL authenticated actor deleted audit'; end if;
end $$;
reset role;
rollback;
\echo 'PASS: Feature3 trusted private evidence, signed human review CAS, audit/revoke and tenant/VIEWER/stale denial'
