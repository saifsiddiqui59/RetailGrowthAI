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
declare pid uuid; jid uuid; second uuid; v jsonb;
begin
 pid := public.create_poster_draft(
 '33333333-3333-4333-8333-333333333333',
 '44444444-4444-4444-8444-444444444444',
 '88888888-8888-4888-8888-888888888888',
 '55555555-5555-4555-8555-555555555555',
 null,'editorial','portrait','Clothing Studio','#AA6644','#F5F0E8',null);
 if pid is null then raise exception 'poster draft setup denied'; end if;
 jid := public.request_poster_job(pid);
 second := public.request_poster_job(pid);
 if jid is null or jid is distinct from second then
   raise exception 'non-idempotent poster queue intent'; end if;
 if (select count(*) from public.poster_jobs where poster_id=pid) <> 1
   or (select count(*) from retail_private.poster_outbox) <> 1 then
   raise exception 'poster job/outbox not atomically persisted'; end if;
 -- Reject browser-crafted terminal states even for the legitimate owner.
 begin
   update public.poster_jobs set status='SUCCEEDED' where id=jid;
   raise exception 'browser updated private poster job';
 exception when insufficient_privilege then null; end;
 begin
   perform public.claim_poster_job(jid);
   raise exception 'browser claimed service lease';
 exception when insufficient_privilege then null; end;
end $$;

select set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true);
do $$
declare pid uuid;
begin
 select id into pid from public.poster_drafts limit 1;
 if public.request_poster_job(pid) is not null then
   raise exception 'VIEWER started poster rendering'; end if;
end $$;

select set_config('request.jwt.claim.sub','99999999-9999-4999-8999-999999999999',true);
do $$
declare pid uuid;
begin
 select id into pid from public.poster_drafts limit 1;
 if public.request_poster_job(pid) is not null
   or (select count(*) from public.poster_jobs)<>0 then
   raise exception 'foreign tenant poster job exposed'; end if;
end $$;

set local role anon;
select set_config('request.jwt.claim.role','anon',true);
select set_config('request.jwt.claim.sub','',true);
do $$
declare denied boolean:=false;
begin
 begin
   perform public.request_poster_job((select id from public.poster_drafts limit 1));
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'anonymous poster render request allowed'; end if;
end $$;

reset role;
select set_config('request.jwt.claim.role','service_role',true);
do $$
declare jid uuid; job jsonb; token uuid; poster uuid; path text; attempted integer;
begin
 select id,poster_id into jid,poster from public.poster_jobs limit 1;
 job:=public.claim_poster_job(jid);
 token:=(job->>'claim_token')::uuid;
 attempted:=(job->>'attempts')::integer;
 path:=(job->>'shop_id')||'/posters/'||poster||'/'||token||'.png';
 if job->>'status'<>'RUNNING' or token is null then
   raise exception 'claim not fenced'; end if;
 if public.complete_poster_job(jid,attempted,gen_random_uuid(),path)
   or public.complete_poster_job(jid,attempted+1,token,path)
   or public.complete_poster_job(jid,attempted,token,'other-shop/forged.png') then
     raise exception 'forged claim unexpectedly completed'; end if;
 if not public.complete_poster_job(jid,attempted,token,path) then
   raise exception 'matching poster claim should complete'; end if;
 if public.complete_poster_job(jid,attempted,token,path)
   or (select status from public.poster_drafts where id=poster)<>'READY'
   or (select count(*) from public.media_assets where object_path=path)<>1 then
     raise exception 'poster completion was not one-shot'; end if;
end $$;

rollback;
\echo 'PASS: poster job owner/viewer/tenant denial, transactional outbox, fenced completion'
