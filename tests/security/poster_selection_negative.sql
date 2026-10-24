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
declare p uuid; j uuid;
begin
 p:=public.create_poster_draft(
 '33333333-3333-4333-8333-333333333333',
 '44444444-4444-4444-8444-444444444444',
 '88888888-8888-4888-8888-888888888888',
 '55555555-5555-4555-8555-555555555555',null,
 'editorial','square','Merchant','#AA6644','#F5F0E8',null);
 if p is null then raise exception 'poster setup denied'; end if;
 j:=public.request_poster_job(p);
 if j is null then raise exception 'render request denied'; end if;
end $$;
reset role;
select set_config('request.jwt.claim.role','service_role',true);
do $$
declare j public.poster_jobs%rowtype;
        p uuid;
        claimed jsonb;
        path text;
begin
 select id,poster_id into j.id,p from public.poster_jobs limit 1;
 claimed:=public.claim_poster_job(j.id);
 path:=(claimed->>'shop_id')||'/posters/'||p||'/'||
    (claimed->>'claim_token')||'.png';
 if not public.complete_poster_job(j.id,(claimed->>'attempts')::int,
      (claimed->>'claim_token')::uuid,path) then
   raise exception 'poster completion denied'; end if;
end $$;

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
do $$
declare poster uuid;
        original jsonb;
        output uuid;
        changed jsonb;
begin
 select id,output_asset_id into poster,output from public.poster_drafts limit 1;
 select instagram into original from public.campaign_days
  where id='88888888-8888-4888-8888-888888888888';
 if not public.select_poster_banner(poster,original) then
    raise exception 'owner cannot select ready poster'; end if;
 select instagram into changed from public.campaign_days
  where id='88888888-8888-4888-8888-888888888888';
 if changed->>'banner_asset_id' is distinct from output::text then
    raise exception 'generated asset did not attach'; end if;
 if public.select_poster_banner(poster,original) then
    raise exception 'stale expected draft overwrote a saved banner'; end if;
end $$;

select set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true);
do $$
declare poster uuid; current_day jsonb;
begin
 select id into poster from public.poster_drafts limit 1;
 select instagram into current_day from public.campaign_days limit 1;
 if public.select_poster_banner(poster,current_day) then
   raise exception 'viewer changed Instagram banner'; end if;
end $$;

select set_config('request.jwt.claim.sub','99999999-9999-4999-8999-999999999999',true);
do $$
declare poster uuid; current_day jsonb;
begin
 -- Foreign user does not receive poster ID via any RLS query.
 if (select count(*) from public.poster_drafts)<>0 then
   raise exception 'foreign tenant sees posters'; end if;
 poster:='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'::uuid;
 select instagram into current_day from public.campaign_days limit 1;
 if public.select_poster_banner(poster,coalesce(current_day,'{}'::jsonb)) then
   raise exception 'foreign user attached banner'; end if;
end $$;
rollback;
\echo 'PASS: explicit owner-only CAS poster selection, stale and tenant denials'
