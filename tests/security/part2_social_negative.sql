-- Disposable local database ONLY. Source pending migrations are not hosted.
-- Supabase CLI applies the 11 Part 1 versions; run both P2 staged SQL files here.
\set ON_ERROR_STOP on
\ir ../../supabase/part2/pending/20261023190000_p2_social_foundation.sql
\ir ../../supabase/part2/pending/20261023190100_p2_social_oauth_transactions.sql
\ir ../../supabase/part2/pending/20261023190200_p2_social_quota_reservation.sql
\ir ../../supabase/part2/pending/20261023190300_p2_social_dispatch_claims.sql
\ir ../../supabase/part2/pending/20261023190400_p2_social_authoring.sql

begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('dddddddd-dddd-4ddd-8ddd-dddddddddddd','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','p2-a@example.invalid','!',now(),now()),
('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','p2-b@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','dddddddd-dddd-4ddd-8ddd-dddddddddddd',true);
insert into public.shops(id,owner_user_id,name,slug)
values('30000000-0000-4000-8000-000000000001',
 'dddddddd-dddd-4ddd-8ddd-dddddddddddd','P2 shop A','p2-mocked-shop-a');
select set_config('request.jwt.claim.sub','eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',true);
insert into public.shops(id,owner_user_id,name,slug)
values('30000000-0000-4000-8000-000000000002',
 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee','P2 shop B','p2-mocked-shop-b');

do $$
begin
  if has_function_privilege('authenticated',
       'public.p2_consume_oauth_state(text,uuid,uuid,text)','EXECUTE') or
     has_function_privilege('authenticated',
       'public.p2_disconnect_social_account(uuid,uuid,uuid)','EXECUTE') or
     has_function_privilege('anon',
       'public.p2_connect_social_account(uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)','EXECUTE') then
    raise exception 'FAIL: public OAuth credential RPC is browser-executable';
  end if;
end $$;

reset role;
select set_config('request.jwt.claim.role','service_role',true);
do $$
declare
  dig text := repeat('ab',32);
  cipher text := repeat('cd',80);
  first_claim jsonb;
  linked uuid := '40000000-0000-4000-8000-000000000001';
  denied boolean;
begin
  -- A's owner can create one 10m state, B's owner cannot steal or consume it.
  if not public.p2_issue_oauth_state(dig,
       '30000000-0000-4000-8000-000000000001',
       'dddddddd-dddd-4ddd-8ddd-dddddddddddd','linkedin',cipher,
       'https://retail.example/api/social/oauth/callback/linkedin') then
    raise exception 'FAIL: OAuth state not issued';
  end if;
  if public.p2_consume_oauth_state(dig,
       '30000000-0000-4000-8000-000000000002',
       'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee','linkedin') is not null then
    raise exception 'FAIL: wrong shop consumed state';
  end if;
  first_claim:=public.p2_consume_oauth_state(dig,
       '30000000-0000-4000-8000-000000000001',
       'dddddddd-dddd-4ddd-8ddd-dddddddddddd','linkedin');
  if first_claim is null
      or first_claim->>'state_digest' <> dig
      or first_claim->>'consumed_at' is not null
      or first_claim->>'verifier_ciphertext' <> cipher then
    raise exception 'FAIL: first atomic state consume';
  end if;
  if public.p2_consume_oauth_state(dig,
       '30000000-0000-4000-8000-000000000001',
       'dddddddd-dddd-4ddd-8ddd-dddddddddddd','linkedin') is not null then
    raise exception 'FAIL: OAuth replay allowed';
  end if;
  denied:=false;
  begin
    perform public.p2_connect_social_account(linked,
     '30000000-0000-4000-8000-000000000002',
     'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
     'linkedin','urn:li:person:123','User A',
     array['w_member_social'],cipher,null,1,null);
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: cross-tenant account connect'; end if;

  if not public.p2_connect_social_account(linked,
     '30000000-0000-4000-8000-000000000001',
     'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
     'linkedin','urn:li:person:123','User A',
     array['w_member_social'],cipher,null,1,null) then
    raise exception 'FAIL: account not connected';
  end if;
  if (select count(*) from retail_private.social_account_credentials
     where social_account_id=linked)<>1 then
     raise exception 'FAIL: encrypted credentials missing';
  end if;
  if public.p2_disconnect_social_account(
     '30000000-0000-4000-8000-000000000002',linked,
     'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee') then
    raise exception 'FAIL: foreign account disconnected';
  end if;
  if not public.p2_disconnect_social_account(
     '30000000-0000-4000-8000-000000000001',linked,
     'dddddddd-dddd-4ddd-8ddd-dddddddddddd') then
    raise exception 'FAIL: disconnect failed';
  end if;
  if exists (select 1 from retail_private.social_account_credentials
             where social_account_id=linked)
     or (select connection_status from public.social_accounts where id=linked)<>'DISCONNECTED' then
    raise exception 'FAIL: local token revocation/connection status';
  end if;
end $$;
rollback;
\echo 'PASS: Part 2 one-use OAuth state, server-only RPC, tenant/account disconnect and private ciphertext'

-- New staged plan ceilings must start EMPTY until explicitly owner-approved.
begin;
do $$
begin
  if exists(select 1 from retail_private.social_publish_plan_limits) then
    raise exception 'FAIL: source-only publish quota must not auto-approve a paid or trial plan';
  end if;
  if has_function_privilege('authenticated',
        'public.p2_reserve_social_publish_quota(uuid,uuid)','EXECUTE')
     or has_function_privilege('anon',
        'public.p2_reserve_social_publish_quota(uuid,uuid)','EXECUTE')
     or has_table_privilege('authenticated',
        'retail_private.social_publish_plan_limits','SELECT')
     or has_table_privilege('authenticated',
        'retail_private.social_publish_quota_ledger','INSERT') then
    raise exception 'FAIL: social quota RPC/ledger exposed to browser actor';
  end if;
end $$;
select set_config('request.jwt.claim.role','service_role',true);
do $$
begin
  if public.p2_reserve_social_publish_quota(
      '30000000-0000-4000-8000-000000000001',
      '40000000-0000-4000-8000-000000000099') then
    raise exception 'FAIL: nonexistent approved job consumed a quota unit';
  end if;
end $$;
rollback;
\echo 'PASS: social quota starts unapproved, RPC service-only, no forged job reservations'

-- Fencing API is server-only; duplicate/nonexistent UUID messages never claim.
begin;
do $$
begin
  if has_function_privilege('authenticated','public.p2_claim_social_publish(uuid)','EXECUTE')
     or has_function_privilege('authenticated','public.p2_mark_social_inflight(uuid,uuid)','EXECUTE')
     or has_function_privilege('anon','public.p2_due_social_job_ids(integer)','EXECUTE')
     or has_function_privilege('anon','public.p2_finish_social_publish(uuid,uuid,text,text,text)','EXECUTE') then
    raise exception 'FAIL: public social worker RPC privilege';
  end if;
end $$;
select set_config('request.jwt.claim.role','service_role',true);
do $$
declare
  missing uuid:='40000000-0000-4000-8000-000000000099';
begin
  if public.p2_claim_social_publish(missing) is not null then
    raise exception 'FAIL: nonexistent publish job claimed';
  end if;
  if public.p2_mark_social_inflight(missing,gen_random_uuid()) then
    raise exception 'FAIL: missing attempt marked as external send';
  end if;
  if public.p2_finish_social_publish(missing,gen_random_uuid(),
        'FAILED','NOT_SENT',null) then
    raise exception 'FAIL: missing claim finalized';
  end if;
  if exists(select 1 from public.p2_due_social_job_ids(20)) then
    raise exception 'FAIL: unapproved social jobs dispatched';
  end if;
end $$;
rollback;
\echo 'PASS: P2 due scanner, private attempt fencing and receipt RPC denied by default'

-- Author/approval/revoke transactions are backend-only with zero implicit caps.
begin;
do $$
begin
  if has_function_privilege('authenticated',
        'public.p2_create_social_draft(uuid,uuid,uuid,uuid,uuid,text,text,uuid,timestamptz,text,text)',
        'EXECUTE')
    or has_function_privilege('authenticated',
        'public.p2_approve_social_job(uuid,uuid,uuid,integer,text,text,timestamptz,text,uuid)',
        'EXECUTE')
    or has_function_privilege('anon',
        'public.p2_cancel_social_job(uuid,uuid,uuid,integer)','EXECUTE') then
    raise exception 'FAIL: publishing write RPC callable by browser';
  end if;
end $$;
select set_config('request.jwt.claim.role','service_role',true);
do $$
declare nonexistent uuid:='50000000-0000-4000-8000-000000000001';
begin
  if public.p2_cancel_social_job(
     '30000000-0000-4000-8000-000000000001',
     nonexistent,'dddddddd-dddd-4ddd-8ddd-dddddddddddd',1) then
    raise exception 'FAIL: wrong-tenant or nonexistent cancel';
  end if;
  if public.p2_approve_social_job(
     '30000000-0000-4000-8000-000000000001',
     nonexistent,'dddddddd-dddd-4ddd-8ddd-dddddddddddd',1,
     repeat('ab',32),'fake',now()+interval '2 hours','Asia/Kolkata',null) then
    raise exception 'FAIL: fabricated job approval';
  end if;
end $$;
rollback;
\echo 'PASS: service-only social authoring and immutable approval CAS'

-- Real disposable transaction journey: idempotency, one-unit quota, exact
-- approval, revoked cancellation, and failed second reservation rollbacks.
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values('ffffffff-ffff-4fff-8fff-ffffffffffff','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','p2-authoring@example.invalid','!',now(),now());
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','ffffffff-ffff-4fff-8fff-ffffffffffff',true);
insert into public.shops(id,owner_user_id,name,slug)
values('31000000-0000-4000-8000-000000000001',
  'ffffffff-ffff-4fff-8fff-ffffffffffff','P2 publishing fixture','p2-publishing-fixture');
reset role;
select set_config('request.jwt.claim.role','service_role',true);
insert into public.campaigns(
  id,shop_id,created_by,brief,duration_days,start_date,timezone,
  language,platforms,status)
values('41000000-0000-4000-8000-000000000001',
  '31000000-0000-4000-8000-000000000001',
  'ffffffff-ffff-4fff-8fff-ffffffffffff',
  'Approved fixture content',1,current_date,'Asia/Kolkata',
  'en-IN',array['linkedin'],'DRAFT');
insert into public.campaign_days(
  id,shop_id,campaign_id,day_index,scheduled_date,topic,review_status)
values('51000000-0000-4000-8000-000000000001',
  '31000000-0000-4000-8000-000000000001',
  '41000000-0000-4000-8000-000000000001',1,current_date,
  'Review-tested content','APPROVED');
insert into public.social_accounts(
  id,shop_id,provider,provider_account_id,display_name,connected_by,
  granted_scopes,connection_status)
values('71000000-0000-4000-8000-000000000001',
  '31000000-0000-4000-8000-000000000001',
  'linkedin','urn:li:person:fixture','P2 LinkedIn',
  'ffffffff-ffff-4fff-8fff-ffffffffffff',array['w_member_social'],'CONNECTED');
insert into retail_private.social_publish_plan_limits(plan_code,max_posts_per_period)
values('TRIAL',1);

do $$
declare
  shop uuid:='31000000-0000-4000-8000-000000000001';
  actor uuid:='ffffffff-ffff-4fff-8fff-ffffffffffff';
  day uuid:='51000000-0000-4000-8000-000000000001';
  account uuid:='71000000-0000-4000-8000-000000000001';
  job1 uuid:='61000000-0000-4000-8000-000000000001';
  job2 uuid:='61000000-0000-4000-8000-000000000002';
  when_utc timestamptz:=now()+interval '2 hours';
  created jsonb;
  denied boolean:=false;
begin
  created:=public.p2_create_social_draft(
    job1,shop,actor,day,account,'linkedin',
    'Reviewed promotion',null,when_utc,'Asia/Kolkata','review-fixture-001');
  if created->>'status'<>'DRAFT' or created->>'id'<>job1::text then
    raise exception 'FAIL: first social draft invalid';
  end if;
  created:=public.p2_create_social_draft(
    gen_random_uuid(),shop,actor,day,account,'linkedin',
    'Reviewed promotion',null,when_utc,'Asia/Kolkata','review-fixture-001');
  if created->>'id'<>job1::text then
    raise exception 'FAIL: idempotency replay duplicated job';
  end if;
  if public.p2_approve_social_job(
    shop,job1,actor,1,repeat('ab',32),'changed content',
    when_utc,'Asia/Kolkata',null) then
    raise exception 'FAIL: stale caption approved';
  end if;
  if not public.p2_approve_social_job(
    shop,job1,actor,1,repeat('ab',32),'Reviewed promotion',
    when_utc,'Asia/Kolkata',null) then
    raise exception 'FAIL: reviewed publication not approved';
  end if;
  if not public.p2_reserve_social_publish_quota(shop,job1)
      or (select count(*) from retail_private.social_publish_quota_ledger
          where publish_job_id=job1)<>1 then
    raise exception 'FAIL: repeated reservation charged twice';
  end if;
  perform public.p2_create_social_draft(
    job2,shop,actor,day,account,'linkedin',
    'Another reviewed promotion',null,when_utc,'Asia/Kolkata','review-fixture-002');
  begin
    perform public.p2_approve_social_job(
      shop,job2,actor,1,repeat('bc',32),'Another reviewed promotion',
      when_utc,'Asia/Kolkata',null);
  exception when sqlstate 'RG002' then denied:=true;
  end;
  if not denied or
     (select status from public.social_publish_jobs where id=job2)<>'DRAFT' then
    raise exception 'FAIL: exceeding quota committed approval';
  end if;
  if not public.p2_cancel_social_job(shop,job1,actor,1)
     or public.p2_cancel_social_job(shop,job1,actor,1)
     or public.p2_claim_social_publish(job1) is not null then
    raise exception 'FAIL: canceled or repeat claim was accepted';
  end if;
end $$;
rollback;
\echo 'PASS: P2 approved content, replay-safe draft, atomic per-period quota and cancel'
