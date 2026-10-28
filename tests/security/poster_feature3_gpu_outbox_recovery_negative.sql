-- Disposable source SQL checks only; no GPU or cloud Queue invoked.
\set ON_ERROR_STOP on
begin;
do $$
declare n integer;
begin
 if has_function_privilege('anon',
 'public.feature3_claim_gpu_dispatch(integer)','EXECUTE')
 or has_function_privilege('authenticated',
 'public.feature3_claim_gpu_dispatch(integer)','EXECUTE')
 or has_function_privilege('authenticated',
 'public.feature3_confirm_gpu_dispatch(uuid,uuid,boolean)','EXECUTE')
 or has_function_privilege('authenticated',
 'public.feature3_audit_gpu_recovery(integer)','EXECUTE')
 or has_table_privilege('authenticated',
 'retail_private.feature3_gpu_recovery_events','SELECT')
 or has_table_privilege('authenticated',
 'retail_private.feature3_gpu_outbox','UPDATE') then
   raise exception 'FAIL: browser can dispatch or settle paid queue';
 end if;
 if (select relrowsecurity from pg_class
   where oid='retail_private.feature3_gpu_recovery_events'::regclass)
   is distinct from true then
   raise exception 'FAIL: no private incident RLS';
 end if;
 select count(*) into n from information_schema.columns
   where table_schema='retail_private'
     and table_name='feature3_gpu_outbox'
     and column_name in ('dispatch_token','claimed_until','sent_at');
 if n<>3 then raise exception 'FAIL: outbox fencing metadata absent'; end if;
 if (select pg_get_functiondef(
  'public.feature3_audit_gpu_recovery(integer)'::regprocedure
 )) !~* 'on conflict[[:space:]]*[(]job_id,[[:space:]]*kind[)][[:space:]]*do nothing' then
   raise exception 'FAIL: recovery incidents not deduplicated';
 end if;
end $$;
-- Empty queues return an empty batch, not a claim or charge. No spend enabled.
set local role service_role;
select set_config('request.jwt.claim.role','service_role',true);
do $$
declare r jsonb;
begin
 r:=public.feature3_claim_gpu_dispatch(1);
 if r is null or jsonb_typeof(r)<>'array' or jsonb_array_length(r)<>0 then
  raise exception 'FAIL: empty GPU dispatch not no-op';
 end if;
 if public.feature3_confirm_gpu_dispatch(
 'e3100000-0000-4000-8000-000000000001',
 'e3100000-0000-4000-8000-000000000002',
 true) then
   raise exception 'FAIL: nonexistent dispatch ACK accepted';
 end if;
 if public.feature3_audit_gpu_recovery(1) <> 0 then
   raise exception 'FAIL: synthetic unclaimed recovery incident created';
 end if;
end $$;
reset role;
rollback;
\echo 'PASS: Feature3 GPU outbox dispatch service-only, no fake ACK and non-billing incident RLS'
