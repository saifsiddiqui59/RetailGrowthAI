-- Disposable local database ONLY. Source pending migrations are not hosted.
-- Supabase CLI applies the 11 Part 1 versions; run both P2 staged SQL files here.
\set ON_ERROR_STOP on
\ir ../../supabase/part2/pending/20261023190000_p2_social_foundation.sql
\ir ../../supabase/part2/pending/20261023190100_p2_social_oauth_transactions.sql
\ir ../../supabase/part2/pending/20261023190200_p2_social_quota_reservation.sql
\ir ../../supabase/part2/pending/20261023190300_p2_social_dispatch_claims.sql
\ir ../../supabase/part2/pending/20261023190400_p2_social_authoring.sql
\ir ../../supabase/part2/pending/20261023190500_p2_social_claim_context.sql
\ir ../../supabase/part2/pending/20261023190600_p2_social_poison_reconciliation.sql
\ir ../../supabase/part2/pending/20261023190700_p2_social_token_refresh.sql
\ir ../../supabase/part2/pending/20261023190800_p2_social_media_reviews.sql
\ir ../../supabase/part2/pending/20261023190900_p2_social_draft_revision.sql
\ir ../../supabase/part2/pending/20261023191000_p2_social_cancel_quota_refund.sql
\ir ../../supabase/part2/pending/20261023191100_p2_social_video_job_reviews.sql

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
        'public.p2_social_claim_context(uuid,uuid)','EXECUTE')
    or has_function_privilege('anon',
        'public.p2_social_claim_context(uuid,uuid)','EXECUTE')
    or has_function_privilege('authenticated',
        'public.p2_revise_social_draft(uuid,uuid,uuid,integer,text,timestamptz,text)',
        'EXECUTE')
     or has_function_privilege('anon',
        'public.p2_revise_social_draft(uuid,uuid,uuid,integer,text,timestamptz,text)',
        'EXECUTE')
     or has_function_privilege('authenticated',
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
  job3 uuid:='61000000-0000-4000-8000-000000000003';
  when_utc timestamptz:=now()+interval '2 hours';
  created jsonb;
  revised jsonb;
  current_claim jsonb;
  server_context jsonb;
  refresh_context jsonb;
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
  -- Unapproved edits must bump revision. Neither forged actors nor stale
  -- approval requests can overwrite newly reviewed text/time.
  perform public.p2_create_social_draft(
    job3,shop,actor,day,account,'linkedin',
    'Unreviewed original',null,when_utc,'Asia/Kolkata','draft-revise-001');
  if public.p2_revise_social_draft(shop,job3,
      'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',1,
      'foreign actor',when_utc,'Asia/Kolkata') is not null then
    raise exception 'FAIL: foreign actor changed draft';
  end if;
  revised:=public.p2_revise_social_draft(shop,job3,actor,1,
      'Revised safe copy',when_utc+interval '1 hour','Asia/Kolkata');
  if revised->>'id'<>job3::text or revised->>'revision'<>'2'
      or (select caption from public.social_publish_jobs where id=job3)
         <> 'Revised safe copy' then
    raise exception 'FAIL: draft revision not persisted';
  end if;
  if public.p2_revise_social_draft(shop,job3,actor,1,
       'stale revision',when_utc,'Asia/Kolkata') is not null
     or public.p2_approve_social_job(shop,job3,actor,1,repeat('aa',32),
       'Unreviewed original',when_utc,'Asia/Kolkata',null) then
    raise exception 'FAIL: stale authoring revision/approval was accepted';
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
  -- The private context requires a matching active claim and credentials.
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    expires_at)
  values(account,1,decode(repeat('cd',80),'hex'),now()+interval '1 day');
  -- Move the fixture to due state to exercise the claim; a real worker would
  -- still independently reject the now-stale content digest before sending.
  update public.social_publish_jobs
    set scheduled_at=now()-interval '2 minutes' where id=job1;
  current_claim:=public.p2_claim_social_publish(job1);
  if current_claim is null then
    raise exception 'FAIL: eligible fixture did not create an atomic claim';
  end if;
  if public.p2_social_claim_context(job1,gen_random_uuid()) is not null then
    raise exception 'FAIL: unknown claim can access private credentials';
  end if;
  server_context:=public.p2_social_claim_context(
    job1,(current_claim->>'claim_token')::uuid);
  if server_context is null
    or server_context->>'shop_id'<>shop::text
    or server_context->'account'->>'provider'<>'linkedin'
    or server_context->'credential'->>'key_version'<>'1'
    or length(server_context->'credential'->>'access_ciphertext_hex')<>160
    or server_context->'job'->>'status'<>'APPROVED' then
    raise exception 'FAIL: server claim context missing or untrusted';
  end if;
  -- Never store a plaintext provider token in the public social job.
  if server_context::text like '%PLAINTEXT_PROVIDER_TOKEN%' then
    raise exception 'FAIL: private context leaked plaintext token';
  end if;
  -- Only the exact active service-role claim may rotate server ciphertext.
  update retail_private.social_account_credentials
    set refresh_token_ciphertext=decode(repeat('ef',80),'hex'),
        expires_at=now()+interval '60 seconds'
    where social_account_id=account;
  if public.p2_social_refresh_context(job1,gen_random_uuid()) is not null then
    raise exception 'FAIL: unowned claim could refresh account';
  end if;
  refresh_context:=public.p2_social_refresh_context(
    job1,(current_claim->>'claim_token')::uuid);
  if refresh_context is null
     or refresh_context->>'provider'<>'linkedin'
     or length(refresh_context->>'refresh_ciphertext_hex')<>160 then
    raise exception 'FAIL: private ciphertext refresh context missing';
  end if;
  if not public.p2_rotate_social_access(
    job1,(current_claim->>'claim_token')::uuid,
    repeat('cd',80),repeat('ab',80),null,now()+interval '1 hour',1) then
    raise exception 'FAIL: valid private credential rotation rejected';
  end if;
  if public.p2_rotate_social_access(
    job1,(current_claim->>'claim_token')::uuid,
    repeat('cd',80),repeat('ac',80),null,now()+interval '1 hour',1) then
    raise exception 'FAIL: stale ciphertext CAS replay succeeded';
  end if;
  -- Active claim (even without SENDING) blocks cancellation and refunds.
  if public.p2_cancel_social_job(shop,job1,actor,1) then
    raise exception 'FAIL: active-claim job canceled';
  end if;
  if (select count(*) from retail_private.social_publish_quota_ledger
      where publish_job_id=job1)<>1 then
    raise exception 'FAIL: active claim released quota';
  end if;
  if not public.p2_finish_social_publish(
      job1,(current_claim->>'claim_token')::uuid,'RETRYABLE','NOT_SENT',null) then
    raise exception 'FAIL: definitely-unsent fixture claim did not finish';
  end if;
  -- Execute mutating RPCs in independent statements; PostgreSQL does not
  -- guarantee short-circuit evaluation/order within one OR expression.
  if not public.p2_cancel_social_job(shop,job1,actor,1) then
    raise exception 'FAIL: first never-sent cancellation was denied';
  end if;
  if public.p2_cancel_social_job(shop,job1,actor,1)
     or public.p2_claim_social_publish(job1) is not null then
    raise exception 'FAIL: canceled job replay accepted';
  end if;
  if exists(select 1 from retail_private.social_publish_quota_ledger
      where publish_job_id=job1) then
    raise exception 'FAIL: canceled unsent post consumed quota';
  end if;
  if not public.p2_approve_social_job(
      shop,job2,actor,1,repeat('bc',32),'Another reviewed promotion',
      when_utc,'Asia/Kolkata',null) then
    raise exception 'FAIL: released quota was not available';
  end if;
  if (select count(*) from retail_private.social_publish_quota_ledger
      where publish_job_id=job2)<>1 then
    raise exception 'FAIL: released unit was double reserved';
  end if;
  if not public.p2_cancel_social_job(shop,job2,actor,1) then
    raise exception 'FAIL: second never-sent cancellation denied';
  end if;
  if public.p2_cancel_social_job(shop,job2,actor,1) then
    raise exception 'FAIL: repeated cancellation accepted';
  end if;
  if exists(select 1 from retail_private.social_publish_quota_ledger
            where publish_job_id=job2) then
    raise exception 'FAIL: canceled second job still reserves quota';
  end if;
  if not public.p2_record_social_poison(job1) or
      (select status from public.social_publish_jobs where id=job1)<>'CANCELED' then
    raise exception 'FAIL: poison redelivery changed already canceled job';
  end if;
  -- Disposable simulation of a poisoned provider send: never make it
  -- RETRYABLE or invoke another outbound call after SENDING.
  update public.social_publish_jobs set status='SENDING' where id=job1;
  insert into retail_private.social_publish_attempts(job_id,attempt_no,claim_token)
    values(job1,2,gen_random_uuid());
  if not public.p2_record_social_poison(job1) then
    raise exception 'FAIL: poisoned sending job receipt rejected';
  end if;
  if (select status from public.social_publish_jobs where id=job1)<>'RECONCILE' then
    raise exception 'FAIL: poisoned sending job not marked RECONCILE';
  end if;
  if exists(select 1 from retail_private.social_publish_attempts
                where job_id=job1 and finished_at is null) then
    raise exception 'FAIL: poisoned sending claim remained active';
  end if;
  if not public.p2_record_social_poison(job1) then
    raise exception 'FAIL: duplicate poison receipt was not idempotent';
  end if;
  -- License registry is empty by default and must be backed by explicit
  -- reviewer, object SHA, rights evidence and verified FFprobe.
  insert into public.media_assets(
    id,shop_id,created_by,object_path,mime_type,source)
  values('81000000-0000-4000-8000-000000000001',shop,actor,
    shop::text||'/renders/p2-evidence-fixture.mp4','video/mp4','GENERATED');
  if public.p2_social_media_is_reviewed(
    shop,'81000000-0000-4000-8000-000000000001') then
    raise exception 'FAIL: unreviewed media was accepted';
  end if;
  -- A video without verified AAC audio (silent or another codec) is not
  -- an eligible Reel/Shorts source, even when the video stream is H.264.
  begin
    perform public.p2_record_social_media_review(
      shop,'81000000-0000-4000-8000-000000000001',actor,
      repeat('ab',32),repeat('cd',32),'OWNER_ATTESTED',
      '{"container":"mp4","video_codec":"h264","pixel_format":"yuv420p","width":1080,"height":1920,"duration_seconds":30}'::jsonb,
      now()+interval '1 day');
    raise exception 'FAIL: missing AAC audio passed review';
  exception when sqlstate '22023' then null;
  end;
  begin
    perform public.p2_record_social_media_review(
      shop,'81000000-0000-4000-8000-000000000001',actor,
      repeat('ab',32),repeat('cd',32),'OWNER_ATTESTED',
      '{"container":"mp4","video_codec":"h264","audio_codec":"mp3","pixel_format":"yuv420p","width":1080,"height":1920,"duration_seconds":30}'::jsonb,
      now()+interval '1 day');
    raise exception 'FAIL: non-AAC audio passed review';
  exception when sqlstate '22023' then null;
  end;
  if not public.p2_record_social_media_review(
    shop,'81000000-0000-4000-8000-000000000001',actor,
    repeat('ab',32),repeat('cd',32),'OWNER_ATTESTED',
    '{"container":"mp4","video_codec":"h264","audio_codec":"aac","pixel_format":"yuv420p","width":1080,"height":1920,"duration_seconds":30}'::jsonb,
    now()+interval '1 day') then
    raise exception 'FAIL: explicit media review rejected';
  end if;
  if not public.p2_social_media_is_reviewed(
    shop,'81000000-0000-4000-8000-000000000001') then
    raise exception 'FAIL: verified media evidence unavailable';
  end if;
  -- A real Part1 SUCCEEDED render is the only eligible social video source.
  update public.media_assets set license_name='owned',
    attribution='fixture service-rendered from reviewed rights'
    where id='81000000-0000-4000-8000-000000000001';
  insert into public.render_jobs(id,shop_id,campaign_id,day_id,requested_by,
      preset,status,idempotency_key,output_asset_id)
  values('91000000-0000-4000-8000-000000000001',shop,
    '41000000-0000-4000-8000-000000000001',day,actor,
    'instagram_reel_30s','SUCCEEDED','reviewed-output-01',
    '81000000-0000-4000-8000-000000000001');
  insert into public.social_accounts(id,shop_id,provider,provider_account_id,
    display_name,connected_by,granted_scopes,connection_status)
  values('72000000-0000-4000-8000-000000000001',shop,'instagram',
    'instagram-fixture-01','Tenant IG professional',actor,
    array['instagram_content_publish'],'CONNECTED');
  perform public.p2_create_social_draft(
    '62000000-0000-4000-8000-000000000001',shop,actor,day,
    '72000000-0000-4000-8000-000000000001','instagram',
    'Reviewed video post','81000000-0000-4000-8000-000000000001',
    when_utc,'Asia/Kolkata','reel-review-fixture-001');
  if public.p2_social_video_source(shop,
      '62000000-0000-4000-8000-000000000001',
      'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee') is not null or
     public.p2_social_video_source(
      '30000000-0000-4000-8000-000000000002',
      '62000000-0000-4000-8000-000000000001',actor) is not null then
    raise exception 'FAIL: untrusted actor/shop saw media path';
  end if;
  if public.p2_social_video_source(shop,
      '62000000-0000-4000-8000-000000000001',actor)->>'media_asset_id'
      <> '81000000-0000-4000-8000-000000000001' then
    raise exception 'FAIL: exact render output candidate missing';
  end if;
  if public.p2_bind_social_video_review(shop,
      '62000000-0000-4000-8000-000000000001',actor,2,repeat('ab',32))
      or public.p2_bind_social_video_review(shop,
      '62000000-0000-4000-8000-000000000001',actor,1,repeat('ef',32)) then
    raise exception 'FAIL: mismatched draft revision/media hash was bound';
  end if;
  if not public.p2_bind_social_video_review(shop,
      '62000000-0000-4000-8000-000000000001',actor,1,repeat('ab',32))
      or not public.p2_social_video_review_bound(shop,
      '62000000-0000-4000-8000-000000000001',repeat('ab',32)) then
    raise exception 'FAIL: reviewed generated media not bound to draft';
  end if;
  -- A bound video review is NOT permission to publish: old video approval
  -- hard-deny is deliberately preserved until trusted rehash and workers exist.
  if public.p2_approve_social_job(shop,
    '62000000-0000-4000-8000-000000000001',actor,1,repeat('aa',32),
    'Reviewed video post',when_utc,'Asia/Kolkata',
    '81000000-0000-4000-8000-000000000001') then
    raise exception 'FAIL: video publish activated prematurely';
  end if;
  update public.social_publish_jobs set revision=2
    where id='62000000-0000-4000-8000-000000000001';
  if public.p2_social_video_review_bound(shop,
      '62000000-0000-4000-8000-000000000001',repeat('ab',32)) then
    raise exception 'FAIL: prior review survived a draft revision';
  end if;
  update public.social_publish_jobs set revision=1
    where id='62000000-0000-4000-8000-000000000001';
  -- The private review lookup must also fail closed after an invalid
  -- service-side metadata update, not just during the initial registration.
  update retail_private.social_media_reviews
    set ffprobe=jsonb_set(ffprobe,'{audio_codec}','"mp3"')
    where shop_id=shop and media_asset_id='81000000-0000-4000-8000-000000000001';
  if public.p2_social_media_is_reviewed(
    shop,'81000000-0000-4000-8000-000000000001') then
    raise exception 'FAIL: altered non-AAC review remained eligible';
  end if;
  update retail_private.social_media_reviews
    set ffprobe=jsonb_set(ffprobe,'{audio_codec}','"aac"')
    where shop_id=shop and media_asset_id='81000000-0000-4000-8000-000000000001';
  update retail_private.social_media_reviews
    set rights_expires_at=now()-interval '1 minute'
    where shop_id=shop and media_asset_id='81000000-0000-4000-8000-000000000001';
  if public.p2_social_media_is_reviewed(
    shop,'81000000-0000-4000-8000-000000000001') then
    raise exception 'FAIL: expired commercial rights still eligible';
  end if;
end $$;
rollback;
\echo 'PASS: P2 approved content, replay-safe draft, atomic per-period quota and cancel'

-- No authenticated actor may acknowledge or alter poison queue statuses.
begin;
do $$
begin
  if has_function_privilege('authenticated',
    'public.p2_record_social_poison(uuid)','EXECUTE')
    or has_function_privilege('anon',
    'public.p2_record_social_poison(uuid)','EXECUTE') then
    raise exception 'FAIL: social poison receipt exposed to browser role';
  end if;
end $$;
select set_config('request.jwt.claim.role','service_role',true);
do $$
begin
  if public.p2_record_social_poison(
      '40000000-0000-4000-8000-000000000099') then
    raise exception 'FAIL: unknown job poison incorrectly acknowledged';
  end if;
end $$;
rollback;
\echo 'PASS: poison receipts require an authoritative private job and server-only actor'

-- Job-specific reviewed video metadata is also never publicly executable.
begin;
do $
begin
  if has_function_privilege('authenticated',
      'public.p2_social_video_source(uuid,uuid,uuid)','EXECUTE')
     or has_function_privilege('anon',
      'public.p2_bind_social_video_review(uuid,uuid,uuid,integer,text)','EXECUTE')
     or has_function_privilege('authenticated',
      'public.p2_social_video_review_bound(uuid,uuid,text)','EXECUTE')
     or has_table_privilege('authenticated',
      'retail_private.social_video_job_reviews','SELECT') then
    raise exception 'FAIL: private video job review reached client';
  end if;
end $;
rollback;
\echo 'PASS: video evidence tenant/revision binding remains service-only'

-- Rights/ffprobe evidence and eligibility functions are not public API.
begin;
do $$
begin
  if has_function_privilege('authenticated',
    'public.p2_record_social_media_review(uuid,uuid,uuid,text,text,text,jsonb,timestamptz)',
    'EXECUTE') or has_function_privilege('anon',
    'public.p2_social_media_is_reviewed(uuid,uuid)','EXECUTE')
    or has_table_privilege('authenticated',
    'retail_private.social_media_reviews','SELECT') then
    raise exception 'FAIL: user-role media rights registry access';
  end if;
end $$;
rollback;
\echo 'PASS: private media rights, FFprobe, expiration and RLS gates'

-- Refresh RPCs never grant any ciphertext access to untrusted client roles.
begin;
do $$
begin
  if has_function_privilege('authenticated',
    'public.p2_social_refresh_context(uuid,uuid)','EXECUTE')
    or has_function_privilege('anon',
    'public.p2_rotate_social_access(uuid,uuid,text,text,text,timestamptz,integer)',
    'EXECUTE') then
    raise exception 'FAIL: unauthenticated OAuth refresh permission';
  end if;
end $$;
rollback;
\echo 'PASS: claim-only token refresh and no browser credential access'
