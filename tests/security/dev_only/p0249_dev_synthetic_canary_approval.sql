-- P0249 DEV-only synthetic retailer authorization hook.
-- Do NOT execute in PROD; requires separate independent security review before
-- DEV migration. No global approval gate toggle and no ROOT impersonation.
-- Uses the existing approval table for exactly two disposable GitHub-owned
-- example.invalid accounts; Auth Admin app_metadata is trusted, user_metadata is not.
begin;

-- Disabled in every database after migration. A separately verified DEV-only
-- deployment may turn on this private flag for its bounded test window.
-- PROD never gains test fixture authorization merely by applying migrations.
create table retail_private.p0249_synthetic_canary_gate (
    singleton boolean primary key default true check (singleton),
    enabled boolean not null default false
);
insert into retail_private.p0249_synthetic_canary_gate (singleton, enabled)
values (true, false);
revoke all on retail_private.p0249_synthetic_canary_gate
  from public, anon, authenticated;
grant select on retail_private.p0249_synthetic_canary_gate to service_role;

create function retail_private.p0249_authorize_disposable_shop_fixture(
    p_user_id uuid, p_run_id text, p_attempt text)
returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
    v_user auth.users%rowtype;
    v_status text;
begin
    -- The caller JWT is SERVICE_ROLE only. Do not grant browser/authenticated
    -- roles EXECUTE, and never accept arbitrary email/user-supplied metadata.
    if (select auth.role()) is distinct from 'service_role'
        or p_user_id is null
        or p_run_id is null or p_run_id !~ '^[0-9]{9,20}$'
        or p_attempt is null or p_attempt !~ '^[0-9]{1,6}$' then
        raise exception 'DEV_FIXTURE_FORBIDDEN' using errcode = '42501';
    end if;

    if not coalesce((select enabled from retail_private.p0249_synthetic_canary_gate
                     where singleton), false) then
        raise exception 'DEV_FIXTURE_DISABLED' using errcode = '42501';
    end if;
    select * into v_user from auth.users where id = p_user_id;
    if not found
        or v_user.email !~ '^rgai-canary-[0-9a-f]{12}-[ab]@example[.]invalid$'
        or v_user.created_at < clock_timestamp() - interval '15 minutes'
        or v_user.created_at > clock_timestamp() + interval '1 minute'
        or v_user.raw_app_meta_data ->> 'rgai_dev_fixture_mode' is distinct
             from 'browser-upload-synthetic'
        or v_user.raw_app_meta_data ->> 'rgai_dev_run_id' is distinct from p_run_id
        or v_user.raw_app_meta_data ->> 'rgai_dev_run_attempt' is distinct from p_attempt
    then
        raise exception 'DEV_FIXTURE_USER_NOT_ELIGIBLE' using errcode = '42501';
    end if;

    -- Must be an existing GoTrue signup-trigger PENDING record, fresh and
    -- never previously reviewed. Do not create one on behalf of another user.
    update retail_private.onboarding_requests
    set status = 'APPROVED',
        decided_at = clock_timestamp(),
        decided_by = p_user_id,
        decision_reason = 'AUTOMATED DEV synthetic fixture by service role; NOT ROOT approval'
    where user_id = p_user_id and status = 'PENDING'
      and requested_at >= clock_timestamp() - interval '15 minutes'
    returning status into v_status;
    if v_status is distinct from 'APPROVED' then
        raise exception 'DEV_FIXTURE_NOT_PENDING' using errcode = '42501';
    end if;
    -- Test-only approval is explicitly attributed to its disposable fixture
    -- identity and documented as a service-role action, never a human reviewer.
    return jsonb_build_object('status',v_status,'synthetic_fixture',true);
end;
$$;
revoke all on function retail_private.p0249_authorize_disposable_shop_fixture(uuid,text,text)
  from public, anon, authenticated;
grant usage on schema retail_private to service_role;
grant execute on function retail_private.p0249_authorize_disposable_shop_fixture(uuid,text,text)
  to service_role;

-- Data API wrapper is invoker-only. No privileged SECURITY DEFINER in public.
create function public.p0249_dev_authorize_synthetic_retailer(
    p_user_id uuid, p_run_id text, p_attempt text)
returns jsonb language sql security invoker set search_path = ''
as $$
    select retail_private.p0249_authorize_disposable_shop_fixture(
      p_user_id, p_run_id, p_attempt);
$$;
revoke all on function public.p0249_dev_authorize_synthetic_retailer(uuid,text,text)
  from public, anon, authenticated;
grant execute on function public.p0249_dev_authorize_synthetic_retailer(uuid,text,text)
  to service_role;

commit;
