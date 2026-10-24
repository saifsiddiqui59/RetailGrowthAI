-- Disposable local CI only: prove the service role can dispatch posters without
-- disclosing the private outbox to browser roles. Does not touch live DEV.
\set ON_ERROR_STOP on
begin;
do $$
begin
  if not has_schema_privilege('service_role','retail_private','USAGE') then
    raise exception 'poster dispatcher service_role missing private schema USAGE';
  end if;
  if not has_table_privilege('service_role','retail_private.poster_outbox','SELECT,UPDATE') then
    raise exception 'service poster outbox table privilege missing';
  end if;
  if not has_function_privilege('service_role','public.claim_poster_outbox(integer)','EXECUTE') then
    raise exception 'service poster outbox RPC EXECUTE privilege missing';
  end if;
  if has_table_privilege('authenticated','retail_private.poster_outbox','SELECT') or
     has_table_privilege('anon','retail_private.poster_outbox','SELECT') then
    raise exception 'private poster outbox exposed to browser roles';
  end if;
  if has_function_privilege('authenticated','public.claim_poster_outbox(integer)','EXECUTE') or
     has_function_privilege('anon','public.claim_poster_outbox(integer)','EXECUTE') then
    raise exception 'private claim RPC exposed to browser roles';
  end if;
end $$;
set local role service_role;
-- No data created; exercising the exact SECURITY INVOKER service-role route
-- catches the missing schema-USAGE permission found on hosted DEV.
do $$
declare claimed jsonb;
begin
  claimed := public.claim_poster_outbox(1);
  if jsonb_typeof(claimed) <> 'array' then
    raise exception 'poster outbox claim RPC returned invalid response';
  end if;
end $$;
reset role;
rollback;
