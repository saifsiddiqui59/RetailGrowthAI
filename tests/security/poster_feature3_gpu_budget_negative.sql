-- Disposable PostgreSQL only. Assertions must not write hosted DEV.
\set ON_ERROR_STOP on
begin;
do $$
declare
  rls_job boolean;
  rls_outbox boolean;
  enabled_default text;
  allowed_count int;
begin
  select relrowsecurity into rls_job from pg_class
    where oid='public.feature3_gpu_jobs'::regclass;
  select relrowsecurity into rls_outbox from pg_class
    where oid='retail_private.feature3_gpu_outbox'::regclass;
  if rls_job is distinct from true or rls_outbox is distinct from true then
    raise exception 'FAIL: Feature3 GPU job/outbox RLS not enabled';
  end if;
  if has_table_privilege('anon','public.feature3_gpu_jobs','SELECT') or
     has_table_privilege('anon','public.feature3_gpu_jobs','INSERT') or
     has_table_privilege('authenticated','public.feature3_gpu_jobs','INSERT') or
     has_table_privilege('authenticated','public.shop_ai_budget_controls','UPDATE') or
     has_table_privilege('authenticated','public.shop_ai_spend_reservations','INSERT') or
     has_table_privilege('authenticated','retail_private.feature3_gpu_outbox','SELECT') then
    raise exception 'FAIL: browser user can authorize or dispatch paid GPU';
  end if;
  if has_function_privilege('anon',
       'public.feature3_reserve_gpu_job(uuid,uuid,uuid,integer,text,uuid,numeric)','EXECUTE') or
     has_function_privilege('authenticated',
       'public.feature3_reserve_gpu_job(uuid,uuid,uuid,integer,text,uuid,numeric)','EXECUTE') or
     has_function_privilege('authenticated',
       'public.feature3_claim_gpu_job(uuid,uuid)','EXECUTE') or
     has_function_privilege('authenticated',
       'public.feature3_finish_gpu_job(uuid,uuid,numeric,uuid)','EXECUTE') then
    raise exception 'FAIL: client can directly spend, claim or settle GPU';
  end if;
  select pg_get_expr(d.adbin,d.adrelid) into enabled_default
    from pg_attribute a join pg_attrdef d
      on d.adrelid=a.attrelid and d.adnum=a.attnum
   where a.attrelid='public.shop_ai_budget_controls'::regclass
     and a.attname='feature3_gpu_enabled';
  if enabled_default is distinct from 'false' then
    raise exception 'FAIL: GPU spending not disabled by default';
  end if;
  select count(*) into allowed_count from pg_constraint
    where conrelid='public.shop_ai_spend_reservations'::regclass
      and contype='c' and pg_get_constraintdef(oid) like '%image_generation%';
  if allowed_count <> 1 then
    raise exception 'FAIL: GPU job not using shared AI cost ledger';
  end if;
end $$;
rollback;
\echo 'PASS: Feature3 GPU default OFF; shared cost ledger and service-only fenced job/outbox API'
