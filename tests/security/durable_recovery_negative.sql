-- Disposable Supabase DB ONLY. Never run against hosted DEV/PROD.
-- Called by rls_negative.sql under psql -v ON_ERROR_STOP=1. Nothing persists.
\set ON_ERROR_STOP on
begin;

insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values ('8a000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000',
'authenticated','authenticated','outbox-owner@example.invalid','!',now(),now());

set local role authenticated;
-- Simulate the signed JWT role accurately for auth.role() in guarded triggers.
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','8a000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug) values
('8a000000-0000-4000-8000-000000000002','8a000000-0000-4000-8000-000000000001',
 'Outbox tenant A','rg-outbox-tenant-a');
insert into public.campaigns(id,shop_id,created_by,brief,start_date) values
('8a000000-0000-4000-8000-000000000003','8a000000-0000-4000-8000-000000000002',
 '8a000000-0000-4000-8000-000000000001','Test service-only transactional outbox','2026-11-01');

-- Authenticated cannot read, write or execute any service-only durable recovery primitives.
reset role;
do $$
declare sig text;
begin
  if not (select relrowsecurity from pg_class where oid='public.job_outbox'::regclass)
    or not (select relrowsecurity from pg_class where oid='public.job_poison_events'::regclass)
  then raise exception 'FAIL: durable recovery tables not RLS-enabled'; end if;
  foreach sig in array array['public.job_outbox','public.job_poison_events'] loop
    if has_table_privilege('authenticated',sig,'SELECT')
       or has_table_privilege('authenticated',sig,'INSERT')
       or has_table_privilege('authenticated',sig,'UPDATE')
       or has_table_privilege('anon',sig,'SELECT')
       or has_table_privilege('anon',sig,'INSERT') then
      raise exception 'FAIL: browser role has durable table privilege on %',sig;
    end if;
  end loop;
  foreach sig in array array[
    'claim_outbox_events(integer)', 'confirm_outbox_event(uuid,uuid,boolean)',
    'claim_campaign_job(uuid)', 'claim_render_job(uuid)',
    'complete_campaign_claim(uuid,integer,uuid,jsonb)',
    'fail_campaign_claim(uuid,integer,uuid,text,boolean)',
    'complete_render_claim(uuid,integer,uuid,text)',
    'fail_render_claim(uuid,integer,uuid,text,boolean)',
    'record_poison_event(text,text,uuid)', 'reconcile_stale_jobs(integer)'
  ] loop
    if has_function_privilege('authenticated','public.'||sig,'EXECUTE')
      or has_function_privilege('anon','public.'||sig,'EXECUTE') then
      raise exception 'FAIL: service-only RPC exposed to browser: %',sig;
    end if;
    if not has_function_privilege('service_role','public.'||sig,'EXECUTE') then
      raise exception 'FAIL: service role cannot execute %',sig;
    end if;
  end loop;
  if (select count(*) from public.job_outbox where kind='planning'
       and job_id='8a000000-0000-4000-8000-000000000003') <> 1 then
    raise exception 'FAIL: campaign INSERT did not atomically write one planning outbox';
  end if;
end $$;

set local role authenticated;
-- Simulate the signed JWT role accurately for auth.role() in guarded triggers.
select set_config('request.jwt.claim.role','authenticated',true);
do $$
declare blocked boolean:=false;
begin
  begin
    perform public.claim_outbox_events(1);
  exception when insufficient_privilege then blocked:=true;
  end;
  if not blocked then raise exception 'FAIL: authenticated client executed service-only outbox RPC'; end if;
  blocked:=false;
  begin
    insert into public.job_poison_events(kind,fingerprint)
      values ('planning',repeat('a',64));
  exception when insufficient_privilege then blocked:=true;
  end;
  if not blocked then raise exception 'FAIL: authenticated client wrote poison receipt'; end if;
end $$;
reset role;

-- Outbox leases are CAS-fenced; wrong, stale or reused acknowledgements fail.
do $$
declare event jsonb; event_id uuid; token uuid;
begin
  select value into event from jsonb_array_elements(public.claim_outbox_events(10)) limit 1;
  if event is null or event->>'kind'<>'planning' then raise exception 'FAIL: cannot claim outbox'; end if;
  event_id := (event->>'id')::uuid;
  token := (event->>'lease_token')::uuid;
  if public.confirm_outbox_event(event_id,gen_random_uuid(),true) then
    raise exception 'FAIL: wrong outbox lease token accepted';
  end if;
  if not public.confirm_outbox_event(event_id,token,true) then
    raise exception 'FAIL: correct outbox lease token rejected';
  end if;
  if public.confirm_outbox_event(event_id,token,true) then
    raise exception 'FAIL: duplicate outbox ACK accepted';
  end if;
end $$;

-- A new attempt must fence all stale planner completion/failure writes.
do $$
declare first_claim jsonb; replacement jsonb;
begin
  first_claim := public.claim_campaign_job('8a000000-0000-4000-8000-000000000003');
  if (first_claim->>'planning_attempts')::int<>1 then raise exception 'FAIL: first planner attempt'; end if;
  update public.campaigns set planning_lease_until=now()-interval '1 minute'
    where id='8a000000-0000-4000-8000-000000000003';
  replacement := public.claim_campaign_job('8a000000-0000-4000-8000-000000000003');
  if (replacement->>'planning_attempts')::int<>2
     or replacement->>'planning_claim_token'=first_claim->>'planning_claim_token'
  then raise exception 'FAIL: replacement planner not re-fenced'; end if;
  if public.fail_campaign_claim('8a000000-0000-4000-8000-000000000003',
       1,(first_claim->>'planning_claim_token')::uuid,'STALE',true) then
    raise exception 'FAIL: stale planner failure clobbered current attempt';
  end if;
  if public.complete_campaign_claim('8a000000-0000-4000-8000-000000000003',
       1,(first_claim->>'planning_claim_token')::uuid,'[]'::jsonb) then
    raise exception 'FAIL: stale planner completion accepted';
  end if;
  if not public.fail_campaign_claim('8a000000-0000-4000-8000-000000000003',
       2,(replacement->>'planning_claim_token')::uuid,'TEST_TERMINAL',true) then
    raise exception 'FAIL: authorized planner failure did not persist';
  end if;
  if (select status from public.campaigns
      where id='8a000000-0000-4000-8000-000000000003')<>'FAILED' then
    raise exception 'FAIL: planner terminal status not persisted';
  end if;
end $$;

-- Seed one authorized day and render. Trigger writes exactly one render outbox.
insert into public.campaign_days(id,shop_id,campaign_id,day_index,scheduled_date,topic,linkedin,instagram)
values ('8a000000-0000-4000-8000-000000000004',
        '8a000000-0000-4000-8000-000000000002',
        '8a000000-0000-4000-8000-000000000003',
        1,'2026-11-01','Test topic','{}'::jsonb,'{}'::jsonb);
insert into public.render_jobs(id,shop_id,campaign_id,day_id,requested_by,preset,idempotency_key)
values ('8a000000-0000-4000-8000-000000000005',
        '8a000000-0000-4000-8000-000000000002',
        '8a000000-0000-4000-8000-000000000003',
        '8a000000-0000-4000-8000-000000000004',
        '8a000000-0000-4000-8000-000000000001','instagram_reel_30s','recovery-render');
do $$
declare first_claim jsonb; replacement jsonb; path text;
begin
  if (select count(*) from public.job_outbox where kind='render'
       and job_id='8a000000-0000-4000-8000-000000000005')<>1 then
    raise exception 'FAIL: render outbox trigger missing/duplicated';
  end if;
  first_claim:=public.claim_render_job('8a000000-0000-4000-8000-000000000005');
  update public.render_jobs set render_lease_until=now()-interval '1 minute'
    where id='8a000000-0000-4000-8000-000000000005';
  replacement:=public.claim_render_job('8a000000-0000-4000-8000-000000000005');
  if (replacement->>'attempts')::int<>2
     or replacement->>'render_claim_token'=first_claim->>'render_claim_token' then
    raise exception 'FAIL: replacement render not re-fenced';
  end if;
  if public.fail_render_claim('8a000000-0000-4000-8000-000000000005',
       1,(first_claim->>'render_claim_token')::uuid,'STALE',true) then
    raise exception 'FAIL: stale render failure accepted';
  end if;
  if public.complete_render_claim('8a000000-0000-4000-8000-000000000005',
       1,(first_claim->>'render_claim_token')::uuid,'bogus') then
    raise exception 'FAIL: stale render completion accepted';
  end if;
  if public.complete_render_claim('8a000000-0000-4000-8000-000000000005',
       2,(replacement->>'render_claim_token')::uuid,'forged/path.mp4') then
    raise exception 'FAIL: forged render output path accepted';
  end if;
  path:='8a000000-0000-4000-8000-000000000002/renders/'||
        '8a000000-0000-4000-8000-000000000005/'||
        (replacement->>'render_claim_token')||'.mp4';
  if not public.complete_render_claim('8a000000-0000-4000-8000-000000000005',
       2,(replacement->>'render_claim_token')::uuid,path) then
    raise exception 'FAIL: current render completion rejected';
  end if;
  if not exists(select 1 from public.render_jobs r
    join public.media_assets a on a.id=r.output_asset_id and a.shop_id=r.shop_id
    where r.id='8a000000-0000-4000-8000-000000000005'
      and r.status='SUCCEEDED' and a.object_path=path) then
    raise exception 'FAIL: render output and terminal state not atomic';
  end if;
end $$;

-- Poison receipts are durable, unique by fingerprint and strictly validated.
do $$
declare denied boolean:=false;
begin
  begin
    perform public.record_poison_event('planning','not-a-digest',null);
  exception when others then denied:=true;
  end;
  if not denied then raise exception 'FAIL: malformed poison envelope accepted'; end if;
  perform public.record_poison_event('planning',repeat('b',64),null);
  perform public.record_poison_event('planning',repeat('b',64),null);
  if (select count(*) from public.job_poison_events
      where kind='planning' and fingerprint=repeat('b',64))<>1 then
    raise exception 'FAIL: poison receipts not deduplicated';
  end if;
end $$;

-- Terminalize an exhausted stale planning record without altering completed jobs.
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values('8a000000-0000-4000-8000-000000000006',
       '8a000000-0000-4000-8000-000000000002',
       '8a000000-0000-4000-8000-000000000001',
       'Exhausted stale claim','2026-11-02');
update public.campaigns set planning_attempts=3,
  planning_lease_until=now()-interval '3 minutes',created_at=now()-interval '10 minutes'
where id='8a000000-0000-4000-8000-000000000006';
select public.reconcile_stale_jobs(10);
do $$
begin
  if not exists (select 1 from public.campaigns where
    id='8a000000-0000-4000-8000-000000000006'
    and status='FAILED' and planning_error_code='RETRY_EXHAUSTED') then
    raise exception 'FAIL: retry-exhausted stale campaign not terminalized';
  end if;
  if (select status from public.render_jobs where
    id='8a000000-0000-4000-8000-000000000005') <> 'SUCCEEDED' then
    raise exception 'FAIL: reconciler rewrote completed render';
  end if;
end $$;
rollback;
\echo 'PASS: service-only RLS/grants, transactional dispatch, lease CAS, stale attempt fencing, poison dedupe, private output and exhausted reconciliation'
