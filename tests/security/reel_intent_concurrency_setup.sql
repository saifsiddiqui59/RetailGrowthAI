-- Disposable GitHub Actions Supabase PostgreSQL ONLY.
-- Committed fixtures are required for real two-connection serialization.
-- Do NOT run on a linked/hosted database. The Python runner hard-pins localhost.
\set ON_ERROR_STOP on
-- Canonical migration is applied by disposable `supabase db start` first.
-- Abort if the versioned RPC is missing; never load a second proposal copy.
select 'public.request_reel_render_job(uuid,uuid)'::regprocedure;

insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values ('a1111111-1111-4111-8111-111111111111',
        '00000000-0000-0000-0000-000000000000',
        'authenticated','authenticated',
        'reel-rpc-concurrent@example.invalid','!',now(),now());

begin;
set local role authenticated;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"a1111111-1111-4111-8111-111111111111","is_anonymous":false}',true);
insert into public.shops(id,owner_user_id,name,slug)
values ('a3333333-3333-4333-8333-333333333333',
        'a1111111-1111-4111-8111-111111111111',
        'Disposable concurrency test shop','rg-reel-rpc-concurrency-ci');
commit;

-- Match existing disposable fixture semantics for backend-only campaign writes.
select set_config('request.jwt.claims','{"role":"service_role","sub":"a1111111-1111-4111-8111-111111111111"}',false);

insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values ('a4444444-4444-4444-8444-444444444444',
        'a3333333-3333-4333-8333-333333333333',
        'a1111111-1111-4111-8111-111111111111',
        'Two simultaneous identical render requests on isolated database',
        '2026-11-01');

-- The campaign planner normally transitions this row before a render request.
update public.campaigns set status='DRAFT'
where id='a4444444-4444-4444-8444-444444444444';

insert into public.media_assets(id,shop_id,created_by,object_path,mime_type,
                               source,license_name,attribution)
values ('a5555555-5555-4555-8555-555555555555',
        'a3333333-3333-4333-8333-333333333333',
        'a1111111-1111-4111-8111-111111111111',
        'a3333333-3333-4333-8333-333333333333/uploads/a5555555-5555-4555-8555-555555555555.png',
        'image/png','UPLOAD','owned','Disposable test-owned creative image');

insert into public.campaign_days(id,campaign_id,shop_id,day_index,scheduled_date,
                                 topic,linkedin,instagram)
values ('a8888888-8888-4888-8888-888888888888',
        'a4444444-4444-4444-8444-444444444444',
        'a3333333-3333-4333-8333-333333333333',
        1,'2026-11-01','Concurrent Diwali campaign',
        '{"post_text":"Diwali promotion","hashtags":["#Diwali"]}'::jsonb,
        '{"caption":"Diwali","banner_asset_id":null,"reel":{"duration_seconds":30,"aspect_ratio":"9:16","storyboard":[{"start_seconds":0,"duration_seconds":30,"asset_id":"a5555555-5555-4555-8555-555555555555","overlay_text":"Festival 🎉 हिंदी"}],"music_asset_id":null,"cta":"Shop today"}}'::jsonb);

-- Fail early if a schema or trigger emitted a job before we start the race.
do $$
begin
  if (select count(*) from public.render_jobs
      where campaign_id='a4444444-4444-4444-8444-444444444444')<>0 then
    raise exception 'concurrency fixture unexpectedly has a render job';
  end if;
end $$;
