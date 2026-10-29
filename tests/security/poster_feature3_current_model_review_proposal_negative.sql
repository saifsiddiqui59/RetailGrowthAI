-- Feature3 current model-review RPC PROPOSAL ONLY: isolated disposable PostgreSQL.
-- GitHub CI imports proposal against temporary DB, checks role/identity denial
-- and drops the function. No hosted migration, licence grant or GPU use.
\set ON_ERROR_STOP on
\ir ../../supabase/proposals/feature3_current_model_review_20261029.sql

begin;
do $test$
declare fn text := 'public.feature3_read_current_model_review(uuid,uuid,text)';
begin
 if to_regprocedure(fn) is null then
   raise exception 'FAIL: proposed Feature3 review RPC was not installed in disposable DB';
 end if;
 if has_function_privilege('anon',fn,'EXECUTE') or
    has_function_privilege('authenticated',fn,'EXECUTE') or
    has_function_privilege('public',fn,'EXECUTE') then
   raise exception 'FAIL: browser/public can execute privileged current model review';
 end if;
 if not has_function_privilege('service_role',fn,'EXECUTE') then
   raise exception 'FAIL: backend-only model review service cannot call RPC';
 end if;
 if pg_get_functiondef(to_regprocedure(fn)) !~* 'security definer' then
   raise exception 'FAIL: private evidence read must be explicit and reviewed';
 end if;
end
$test$;

set local role service_role;
select set_config('request.jwt.claim.role','service_role',true);
do $test$
declare
  missing_shop uuid := 'f3000000-0000-4000-8000-000000000001';
  missing_media uuid := 'f3000000-0000-4000-8000-000000000002';
begin
  -- No current reviewed customer model exists: an arbitrary selected image
  -- hash, foreign-looking shop or null input cannot produce an approval.
  if public.feature3_read_current_model_review(
      missing_shop,missing_media,repeat('a',64)) is not null or
     public.feature3_read_current_model_review(
      missing_shop,missing_media,'INVALID-SHA') is not null or
     public.feature3_read_current_model_review(
      null,missing_media,repeat('a',64)) is not null or
     public.feature3_read_current_model_review(
      missing_shop,null,repeat('a',64)) is not null then
    raise exception 'FAIL: missing/unreviewed/invalid original approved by proposed RPC';
  end if;
end
$test$;

-- SECURITY DEFINER may not treat an authenticated-role JWT claim as
-- backend authority merely because a Postgres session was initialized.
select set_config('request.jwt.claim.role','authenticated',true);
do $test$
begin
  begin
    perform public.feature3_read_current_model_review(
      'f3000000-0000-4000-8000-000000000001',
      'f3000000-0000-4000-8000-000000000002',repeat('a',64));
    raise exception 'FAIL: forged authenticated caller bypassed service role';
  exception when sqlstate '42501' then
    null;
  end;
end
$test$;
reset role;
rollback;

-- A proposed function in disposable PostgreSQL must never be retained as
-- a canonical migration or used to claim live licensed commercial model.
drop function public.feature3_read_current_model_review(uuid,uuid,text);
\echo 'PASS: Feature3 proposed model review SQL executes only for service role and denies unreviewed source'
