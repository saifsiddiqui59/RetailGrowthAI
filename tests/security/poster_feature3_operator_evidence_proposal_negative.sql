-- Feature3 private generated PNG operator evidence RPC: disposable SQL proof ONLY.
-- Proposal is not a canonical migration; no DEV/PROD deployment or GPU usage.
\set ON_ERROR_STOP on
\ir ../../supabase/proposals/feature3_operator_evidence_read_20261029.sql

begin;
do $test$
declare fn text := 'public.feature3_read_gpu_private_evidence(uuid,uuid,uuid)';
begin
  if to_regprocedure(fn) is null then
    raise exception 'FAIL: operator evidence RPC absent in isolated PostgreSQL';
  end if;
  if has_function_privilege('anon',fn,'EXECUTE') or
     has_function_privilege('authenticated',fn,'EXECUTE') or
     not has_function_privilege('service_role',fn,'EXECUTE') then
    raise exception 'FAIL: public/browser execution of immutable output evidence';
  end if;
  if pg_get_functiondef(to_regprocedure(fn)) !~* 'security definer' then
    raise exception 'FAIL: operator evidence privileged boundary unreviewed';
  end if;
end $test$;

set local role service_role;
select set_config('request.jwt.claim.role','service_role',true);
do $test$
declare
  sid uuid := 'f3400000-0000-4000-8000-000000000001';
  jid uuid := 'f3400000-0000-4000-8000-000000000002';
  mid uuid := 'f3400000-0000-4000-8000-000000000003';
begin
  -- These are nonexistent synthetic IDs. No SQL status, private PNG key or
  -- fabricated Storage row can be inferred from an absent job.
  if public.feature3_read_gpu_private_evidence(sid,jid,mid) is not null or
     public.feature3_read_gpu_private_evidence(null,jid,mid) is not null or
     public.feature3_read_gpu_private_evidence(sid,null,mid) is not null or
     public.feature3_read_gpu_private_evidence(sid,jid,null) is not null then
    raise exception 'FAIL: missing/foreign private generated PNG accepted';
  end if;
end $test$;

-- A forged JWT authorization context is rejected, even under a privileged
-- Postgres session. Only actual service_role provider credentials may call.
select set_config('request.jwt.claim.role','authenticated',true);
do $test$
begin
  begin
    perform public.feature3_read_gpu_private_evidence(
      'f3400000-0000-4000-8000-000000000001',
      'f3400000-0000-4000-8000-000000000002',
      'f3400000-0000-4000-8000-000000000003');
    raise exception 'FAIL: nonservice JWT claim forged private output evidence';
  exception when sqlstate '42501' then
    null;
  end;
end $test$;
reset role;
rollback;

-- Remove proposed routine from local disposable environment after checks.
drop function public.feature3_read_gpu_private_evidence(uuid,uuid,uuid);
\echo 'PASS: Feature3 operator private-evidence RPC service-only, missing output and forged JWT denied'
