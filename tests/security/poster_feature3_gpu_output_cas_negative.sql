-- Disposable PostgreSQL only, transactional synthetic STORAGE METADATA.
-- No actual object bytes, commercial photos, cloud GPU or hosted SQL touched.
\set ON_ERROR_STOP on
begin;
do $safety$
declare p record;
begin
 if has_function_privilege('anon',
    'public.feature3_commit_gpu_private_output(uuid,uuid,integer,uuid,text,text,bigint,uuid[])','EXECUTE')
    or has_function_privilege('authenticated',
    'public.feature3_commit_gpu_private_output(uuid,uuid,integer,uuid,text,text,bigint,uuid[])','EXECUTE')
    or has_table_privilege('authenticated','retail_private.feature3_gpu_output_evidence','SELECT')
    or has_table_privilege('authenticated','retail_private.feature3_gpu_output_evidence','INSERT') then
   raise exception 'FAIL: browser can commit or read private GPU output evidence';
 end if;
 if not (select relrowsecurity from pg_class
   where oid='retail_private.feature3_gpu_output_evidence'::regclass) then
   raise exception 'FAIL: output provenance lacks RLS';
 end if;
 if (select count(*) from pg_policies
     where schemaname='storage' and tablename='objects'
       and policyname in ('feature3_generated_private_insert_only_service',
       'feature3_generated_private_update_only_service',
       'feature3_generated_private_delete_only_service')
       and permissive='RESTRICTIVE')<>3 then
   raise exception 'FAIL: retailer can create/replace/delete reserved GPU outputs';
 end if;
end $safety$;

insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values ('e3000000-0000-4000-8000-000000000001',
'00000000-0000-0000-0000-000000000000',
'authenticated','authenticated','f3-output-owner@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','e3000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('e3000000-0000-4000-8000-000000000011',
'e3000000-0000-4000-8000-000000000001',
'Fictional GPU output test shop','f3-output-fixture');
reset role;

set local role service_role;
select set_config('request.jwt.claim.role','service_role',true);
insert into public.campaigns
 (id,shop_id,created_by,brief,start_date)
values('e3000000-0000-4000-8000-000000000021',
 'e3000000-0000-4000-8000-000000000011',
 'e3000000-0000-4000-8000-000000000001',
 'Fictional kurti model test only',current_date);
insert into public.campaign_days
 (id,campaign_id,shop_id,day_index,scheduled_date,topic)
values('e3000000-0000-4000-8000-000000000022',
'e3000000-0000-4000-8000-000000000021',
'e3000000-0000-4000-8000-000000000011',1,current_date,'Synthetic Diwali kurti');
insert into public.feature3_poster_designs
 (id,shop_id,campaign_id,day_id,created_by,revision,status,design,server_document_sha256)
values('e3000000-0000-4000-8000-000000000023',
'e3000000-0000-4000-8000-000000000011',
'e3000000-0000-4000-8000-000000000021',
'e3000000-0000-4000-8000-000000000022',
'e3000000-0000-4000-8000-000000000001',1,'DRAFT',
jsonb_build_object('schema','retailgrowth.poster.v2',
  'shop_id','e3000000-0000-4000-8000-000000000011'),
repeat('a',64));
-- Shop onboarding trigger already creates the trial subscription.
update public.shop_subscriptions
set status='TRIAL', valid_from=now()-interval '1 hour',
    valid_until=now()+interval '1 day',
    period_start=now()-interval '1 day',
    period_end=now()+interval '1 day'
where shop_id='e3000000-0000-4000-8000-000000000011';
insert into public.shop_ai_spend_reservations
 (id,shop_id,request_id,actor_id,operation,period_start,reserved_usd)
values('e3000000-0000-4000-8000-000000000031',
'e3000000-0000-4000-8000-000000000011',
'e3000000-0000-4000-8000-000000000032',
'e3000000-0000-4000-8000-000000000001',
'image_generation',now()-interval '1 day',0.500000);
insert into public.feature3_gpu_jobs
 (id,shop_id,requested_by,design_id,design_revision,design_server_sha256,
 request_id,reservation_id,status,attempts,claim_token,lease_until)
values('e3000000-0000-4000-8000-000000000033',
'e3000000-0000-4000-8000-000000000011',
'e3000000-0000-4000-8000-000000000001',
'e3000000-0000-4000-8000-000000000023',1,repeat('a',64),
'e3000000-0000-4000-8000-000000000032',
'e3000000-0000-4000-8000-000000000031',
'RUNNING',1,'e3000000-0000-4000-8000-000000000034',now()+interval '15 minutes');
insert into public.media_assets(id,shop_id,created_by,object_path,mime_type,source,license_name,attribution)
values('e3000000-0000-4000-8000-000000000041',
'e3000000-0000-4000-8000-000000000011',
'e3000000-0000-4000-8000-000000000001',
'e3000000-0000-4000-8000-000000000011/uploads/e3000000-0000-4000-8000-000000000042.png',
'image/png','UPLOAD','owned','Fictional shop-only test source');
insert into storage.objects(bucket_id,name,metadata)
values('retailgrowth-media',
'e3000000-0000-4000-8000-000000000011/feature3/gpu/e3000000-0000-4000-8000-000000000033/'||repeat('c',64)||'.png',
jsonb_build_object('mimetype','image/png','size','200'));

do $checks$
declare
 s uuid:='e3000000-0000-4000-8000-000000000011';
 j uuid:='e3000000-0000-4000-8000-000000000033';
 t uuid:='e3000000-0000-4000-8000-000000000034';
 src uuid:='e3000000-0000-4000-8000-000000000041';
 p text;
 r jsonb;
begin
 p:=s::text||'/feature3/gpu/'||j::text||'/'||repeat('c',64)||'.png';
 r:=public.feature3_commit_gpu_private_output(s,j,1,
 'e3000000-0000-4000-8000-000000000044',p,repeat('c',64),200,array[src]);
 if r is not null then raise exception 'FAIL: forged claim accepted'; end if;
 r:=public.feature3_commit_gpu_private_output(s,j,1,t,p,repeat('c',64),200,
  array['e3000000-0000-4000-8000-000000000049'::uuid]);
 if r is not null then raise exception 'FAIL: foreign source accepted'; end if;
 r:=public.feature3_commit_gpu_private_output(s,j,1,t,p,repeat('d',64),200,array[src]);
 if r is not null then raise exception 'FAIL: changed output SHA accepted'; end if;
 r:=public.feature3_commit_gpu_private_output(s,j,1,t,p,repeat('c',64),199,array[src]);
 if r is not null then raise exception 'FAIL: changed output byte count accepted'; end if;
 r:=public.feature3_commit_gpu_private_output(s,j,1,t,p,repeat('c',64),200,array[src]);
 if r is null or r->>'review_status'<>'UNREVIEWED'
    or r->>'image_sha256'<>repeat('c',64)
    or r->>'source'<>'GENERATED' or r->>'private'<>'true' then
   raise exception 'FAIL: valid one-time source-only private receipt not committed';
 end if;
 if (select count(*) from retail_private.feature3_gpu_output_evidence
      where shop_id=s and job_id=j and review_status='UNREVIEWED')<>1 or
    (select count(*) from public.media_assets where shop_id=s
     and object_path=p and source='GENERATED' and license_name is null)<>1 then
   raise exception 'FAIL: immutable output evidence not registered';
 end if;
 r:=public.feature3_commit_gpu_private_output(s,j,1,t,p,repeat('c',64),200,array[src]);
 if r is not null then raise exception 'FAIL: duplicate response replay accepted'; end if;
 -- Paid settlement is separate but MUST consume exactly the fenced private
 -- evidence receipt, without manufacturing review/publish approval.
 if public.feature3_finish_gpu_job(
      j,t,0.125000,(select media_asset_id from
       retail_private.feature3_gpu_output_evidence where job_id=j)
    ) is distinct from true then
   raise exception 'FAIL: correctly attested private output not settled';
 end if;
 if (select status from public.feature3_gpu_jobs where id=j)<>'SUCCEEDED' or
    (select actual_usd from public.shop_ai_spend_reservations
     where id='e3000000-0000-4000-8000-000000000031')<>0.125000 then
    raise exception 'FAIL: exact one-shot attested GPU settlement was not durable';
 end if;
end $checks$;
reset role;
rollback;
\echo 'PASS: Feature3 private output one-time SQL CAS, lease/foreign/SHA denied, RLS + reserved Storage namespace'
