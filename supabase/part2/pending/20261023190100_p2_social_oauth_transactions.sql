-- RETAILGROWTHAI PART 2, PENDING ONLY. DO NOT APPLY TO HOSTED SUPABASE.
-- Requires pending social foundation and all existing 11 Part 1 migrations.
-- Expose strictly service-role RPCs; browsers must never read encrypted OAuth data.
begin;

create function public.p2_issue_oauth_state(
  p_digest_hex text, p_shop uuid, p_actor uuid, p_provider text,
  p_verifier_hex text, p_redirect text
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_digest_hex !~ '^[0-9a-f]{64}$'
      or (p_verifier_hex !~ '^[0-9a-f]+
      or p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_redirect !~ '^https://[^/[:space:]]+/'
      or length(p_redirect)>600 then
    raise exception 'invalid OAuth state' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  insert into retail_private.social_oauth_states(
    state_digest,shop_id,requested_by,provider,verifier_ciphertext,
    exact_redirect_uri,expires_at)
  values (decode(p_digest_hex,'hex'),p_shop,p_actor,p_provider,
          decode(p_verifier_hex,'hex'),p_redirect,now()+interval '10 minutes');
  return true;
end
$$;

-- Important: update ... returning sees the newly set consumed_at. Return
-- consumed_at=NULL explicitly because the backend verifies the PRE-consume row.
-- This is a CAS: concurrent callback executions cannot both claim the state.
create function public.p2_consume_oauth_state(
  p_digest_hex text, p_shop uuid, p_actor uuid, p_provider text
) returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
  rec retail_private.social_oauth_states%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_digest_hex !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid OAuth digest' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    return null;
  end if;
  update retail_private.social_oauth_states s
    set consumed_at=now()
    where s.state_digest=decode(p_digest_hex,'hex')
      and s.shop_id=p_shop and s.requested_by=p_actor
      and s.provider=p_provider and s.consumed_at is null
      and s.expires_at>now()
    returning * into rec;
  if not found then return null; end if;
  return jsonb_build_object(
    'state_digest',encode(rec.state_digest,'hex'),
    'shop_id',rec.shop_id,'user_id',rec.requested_by,'provider',rec.provider,
    'expires_at',rec.expires_at,'consumed_at',null,
    'exact_redirect_uri',rec.exact_redirect_uri,
    'verifier_ciphertext',encode(rec.verifier_ciphertext,'hex')
  );
end
$$;

-- Atomic account metadata and encrypted credential persistence. Never return
-- ciphertext in response; uniqueness failures rollback both inserts.
create function public.p2_connect_social_account(
  p_id uuid,p_shop uuid,p_actor uuid,p_provider text,p_provider_account text,
  p_name text,p_scopes text[],p_access_hex text,p_refresh_hex text,
  p_key_version integer,p_expires_at timestamptz
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  if p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_provider_account !~ '^[A-Za-z0-9:_-]{1,200}$'
      or length(trim(coalesce(p_name,''))) not between 1 and 200
      or p_scopes is null or cardinality(p_scopes)=0
      or (p_access_hex !~ '^[0-9a-f]+
      or (p_refresh_hex is not null
          and (p_refresh_hex !~ '^[0-9a-f]+)
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_verifier_hex) not between 80 and 16384 or length(p_verifier_hex)%2<>0)
      or p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_redirect !~ '^https://[^/[:space:]]+/'
      or length(p_redirect)>600 then
    raise exception 'invalid OAuth state' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  insert into retail_private.social_oauth_states(
    state_digest,shop_id,requested_by,provider,verifier_ciphertext,
    exact_redirect_uri,expires_at)
  values (decode(p_digest_hex,'hex'),p_shop,p_actor,p_provider,
          decode(p_verifier_hex,'hex'),p_redirect,now()+interval '10 minutes');
  return true;
end
$$;

-- Important: update ... returning sees the newly set consumed_at. Return
-- consumed_at=NULL explicitly because the backend verifies the PRE-consume row.
-- This is a CAS: concurrent callback executions cannot both claim the state.
create function public.p2_consume_oauth_state(
  p_digest_hex text, p_shop uuid, p_actor uuid, p_provider text
) returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
  rec retail_private.social_oauth_states%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_digest_hex !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid OAuth digest' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    return null;
  end if;
  update retail_private.social_oauth_states s
    set consumed_at=now()
    where s.state_digest=decode(p_digest_hex,'hex')
      and s.shop_id=p_shop and s.requested_by=p_actor
      and s.provider=p_provider and s.consumed_at is null
      and s.expires_at>now()
    returning * into rec;
  if not found then return null; end if;
  return jsonb_build_object(
    'state_digest',encode(rec.state_digest,'hex'),
    'shop_id',rec.shop_id,'user_id',rec.requested_by,'provider',rec.provider,
    'expires_at',rec.expires_at,'consumed_at',null,
    'exact_redirect_uri',rec.exact_redirect_uri,
    'verifier_ciphertext',encode(rec.verifier_ciphertext,'hex')
  );
end
$$;

-- Atomic account metadata and encrypted credential persistence. Never return
-- ciphertext in response; uniqueness failures rollback both inserts.
create function public.p2_connect_social_account(
  p_id uuid,p_shop uuid,p_actor uuid,p_provider text,p_provider_account text,
  p_name text,p_scopes text[],p_access_hex text,p_refresh_hex text,
  p_key_version integer,p_expires_at timestamptz
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  if p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_provider_account !~ '^[A-Za-z0-9:_-]{1,200}$'
      or length(trim(coalesce(p_name,''))) not between 1 and 200
      or p_scopes is null or cardinality(p_scopes)=0
      or p_access_hex !~ '^(?:[0-9a-f]{2}){40,8192}$'
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_access_hex) not between 80 and 16384 or length(p_access_hex)%2<>0)
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_verifier_hex) not between 80 and 16384 or length(p_verifier_hex)%2<>0)
      or p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_redirect !~ '^https://[^/[:space:]]+/'
      or length(p_redirect)>600 then
    raise exception 'invalid OAuth state' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  insert into retail_private.social_oauth_states(
    state_digest,shop_id,requested_by,provider,verifier_ciphertext,
    exact_redirect_uri,expires_at)
  values (decode(p_digest_hex,'hex'),p_shop,p_actor,p_provider,
          decode(p_verifier_hex,'hex'),p_redirect,now()+interval '10 minutes');
  return true;
end
$$;

-- Important: update ... returning sees the newly set consumed_at. Return
-- consumed_at=NULL explicitly because the backend verifies the PRE-consume row.
-- This is a CAS: concurrent callback executions cannot both claim the state.
create function public.p2_consume_oauth_state(
  p_digest_hex text, p_shop uuid, p_actor uuid, p_provider text
) returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
  rec retail_private.social_oauth_states%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_digest_hex !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid OAuth digest' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    return null;
  end if;
  update retail_private.social_oauth_states s
    set consumed_at=now()
    where s.state_digest=decode(p_digest_hex,'hex')
      and s.shop_id=p_shop and s.requested_by=p_actor
      and s.provider=p_provider and s.consumed_at is null
      and s.expires_at>now()
    returning * into rec;
  if not found then return null; end if;
  return jsonb_build_object(
    'state_digest',encode(rec.state_digest,'hex'),
    'shop_id',rec.shop_id,'user_id',rec.requested_by,'provider',rec.provider,
    'expires_at',rec.expires_at,'consumed_at',null,
    'exact_redirect_uri',rec.exact_redirect_uri,
    'verifier_ciphertext',encode(rec.verifier_ciphertext,'hex')
  );
end
$$;

-- Atomic account metadata and encrypted credential persistence. Never return
-- ciphertext in response; uniqueness failures rollback both inserts.
create function public.p2_connect_social_account(
  p_id uuid,p_shop uuid,p_actor uuid,p_provider text,p_provider_account text,
  p_name text,p_scopes text[],p_access_hex text,p_refresh_hex text,
  p_key_version integer,p_expires_at timestamptz
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  if p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_provider_account !~ '^[A-Za-z0-9:_-]{1,200}$'
      or length(trim(coalesce(p_name,''))) not between 1 and 200
      or p_scopes is null or cardinality(p_scopes)=0
      or (p_access_hex !~ '^[0-9a-f]+
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_access_hex) not between 80 and 16384 or length(p_access_hex)%2<>0)
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_refresh_hex) not between 80 and 16384 or length(p_refresh_hex)%2<>0))
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_verifier_hex) not between 80 and 16384 or length(p_verifier_hex)%2<>0)
      or p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_redirect !~ '^https://[^/[:space:]]+/'
      or length(p_redirect)>600 then
    raise exception 'invalid OAuth state' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  insert into retail_private.social_oauth_states(
    state_digest,shop_id,requested_by,provider,verifier_ciphertext,
    exact_redirect_uri,expires_at)
  values (decode(p_digest_hex,'hex'),p_shop,p_actor,p_provider,
          decode(p_verifier_hex,'hex'),p_redirect,now()+interval '10 minutes');
  return true;
end
$$;

-- Important: update ... returning sees the newly set consumed_at. Return
-- consumed_at=NULL explicitly because the backend verifies the PRE-consume row.
-- This is a CAS: concurrent callback executions cannot both claim the state.
create function public.p2_consume_oauth_state(
  p_digest_hex text, p_shop uuid, p_actor uuid, p_provider text
) returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
  rec retail_private.social_oauth_states%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_digest_hex !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid OAuth digest' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    return null;
  end if;
  update retail_private.social_oauth_states s
    set consumed_at=now()
    where s.state_digest=decode(p_digest_hex,'hex')
      and s.shop_id=p_shop and s.requested_by=p_actor
      and s.provider=p_provider and s.consumed_at is null
      and s.expires_at>now()
    returning * into rec;
  if not found then return null; end if;
  return jsonb_build_object(
    'state_digest',encode(rec.state_digest,'hex'),
    'shop_id',rec.shop_id,'user_id',rec.requested_by,'provider',rec.provider,
    'expires_at',rec.expires_at,'consumed_at',null,
    'exact_redirect_uri',rec.exact_redirect_uri,
    'verifier_ciphertext',encode(rec.verifier_ciphertext,'hex')
  );
end
$$;

-- Atomic account metadata and encrypted credential persistence. Never return
-- ciphertext in response; uniqueness failures rollback both inserts.
create function public.p2_connect_social_account(
  p_id uuid,p_shop uuid,p_actor uuid,p_provider text,p_provider_account text,
  p_name text,p_scopes text[],p_access_hex text,p_refresh_hex text,
  p_key_version integer,p_expires_at timestamptz
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  if p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_provider_account !~ '^[A-Za-z0-9:_-]{1,200}$'
      or length(trim(coalesce(p_name,''))) not between 1 and 200
      or p_scopes is null or cardinality(p_scopes)=0
      or p_access_hex !~ '^(?:[0-9a-f]{2}){40,8192}$'
      or (p_refresh_hex is not null
          and (p_refresh_hex !~ '^[0-9a-f]+)
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_access_hex) not between 80 and 16384 or length(p_access_hex)%2<>0)
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_verifier_hex) not between 80 and 16384 or length(p_verifier_hex)%2<>0)
      or p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_redirect !~ '^https://[^/[:space:]]+/'
      or length(p_redirect)>600 then
    raise exception 'invalid OAuth state' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  insert into retail_private.social_oauth_states(
    state_digest,shop_id,requested_by,provider,verifier_ciphertext,
    exact_redirect_uri,expires_at)
  values (decode(p_digest_hex,'hex'),p_shop,p_actor,p_provider,
          decode(p_verifier_hex,'hex'),p_redirect,now()+interval '10 minutes');
  return true;
end
$$;

-- Important: update ... returning sees the newly set consumed_at. Return
-- consumed_at=NULL explicitly because the backend verifies the PRE-consume row.
-- This is a CAS: concurrent callback executions cannot both claim the state.
create function public.p2_consume_oauth_state(
  p_digest_hex text, p_shop uuid, p_actor uuid, p_provider text
) returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
  rec retail_private.social_oauth_states%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_digest_hex !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid OAuth digest' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    return null;
  end if;
  update retail_private.social_oauth_states s
    set consumed_at=now()
    where s.state_digest=decode(p_digest_hex,'hex')
      and s.shop_id=p_shop and s.requested_by=p_actor
      and s.provider=p_provider and s.consumed_at is null
      and s.expires_at>now()
    returning * into rec;
  if not found then return null; end if;
  return jsonb_build_object(
    'state_digest',encode(rec.state_digest,'hex'),
    'shop_id',rec.shop_id,'user_id',rec.requested_by,'provider',rec.provider,
    'expires_at',rec.expires_at,'consumed_at',null,
    'exact_redirect_uri',rec.exact_redirect_uri,
    'verifier_ciphertext',encode(rec.verifier_ciphertext,'hex')
  );
end
$$;

-- Atomic account metadata and encrypted credential persistence. Never return
-- ciphertext in response; uniqueness failures rollback both inserts.
create function public.p2_connect_social_account(
  p_id uuid,p_shop uuid,p_actor uuid,p_provider text,p_provider_account text,
  p_name text,p_scopes text[],p_access_hex text,p_refresh_hex text,
  p_key_version integer,p_expires_at timestamptz
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  if p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_provider_account !~ '^[A-Za-z0-9:_-]{1,200}$'
      or length(trim(coalesce(p_name,''))) not between 1 and 200
      or p_scopes is null or cardinality(p_scopes)=0
      or (p_access_hex !~ '^[0-9a-f]+
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_access_hex) not between 80 and 16384 or length(p_access_hex)%2<>0)
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_refresh_hex) not between 80 and 16384 or length(p_refresh_hex)%2<>0))
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_access_hex) not between 80 and 16384 or length(p_access_hex)%2<>0)
      or (p_refresh_hex is not null
          and (p_refresh_hex !~ '^[0-9a-f]+)
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_verifier_hex) not between 80 and 16384 or length(p_verifier_hex)%2<>0)
      or p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_redirect !~ '^https://[^/[:space:]]+/'
      or length(p_redirect)>600 then
    raise exception 'invalid OAuth state' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  insert into retail_private.social_oauth_states(
    state_digest,shop_id,requested_by,provider,verifier_ciphertext,
    exact_redirect_uri,expires_at)
  values (decode(p_digest_hex,'hex'),p_shop,p_actor,p_provider,
          decode(p_verifier_hex,'hex'),p_redirect,now()+interval '10 minutes');
  return true;
end
$$;

-- Important: update ... returning sees the newly set consumed_at. Return
-- consumed_at=NULL explicitly because the backend verifies the PRE-consume row.
-- This is a CAS: concurrent callback executions cannot both claim the state.
create function public.p2_consume_oauth_state(
  p_digest_hex text, p_shop uuid, p_actor uuid, p_provider text
) returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
  rec retail_private.social_oauth_states%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_digest_hex !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid OAuth digest' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    return null;
  end if;
  update retail_private.social_oauth_states s
    set consumed_at=now()
    where s.state_digest=decode(p_digest_hex,'hex')
      and s.shop_id=p_shop and s.requested_by=p_actor
      and s.provider=p_provider and s.consumed_at is null
      and s.expires_at>now()
    returning * into rec;
  if not found then return null; end if;
  return jsonb_build_object(
    'state_digest',encode(rec.state_digest,'hex'),
    'shop_id',rec.shop_id,'user_id',rec.requested_by,'provider',rec.provider,
    'expires_at',rec.expires_at,'consumed_at',null,
    'exact_redirect_uri',rec.exact_redirect_uri,
    'verifier_ciphertext',encode(rec.verifier_ciphertext,'hex')
  );
end
$$;

-- Atomic account metadata and encrypted credential persistence. Never return
-- ciphertext in response; uniqueness failures rollback both inserts.
create function public.p2_connect_social_account(
  p_id uuid,p_shop uuid,p_actor uuid,p_provider text,p_provider_account text,
  p_name text,p_scopes text[],p_access_hex text,p_refresh_hex text,
  p_key_version integer,p_expires_at timestamptz
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  if p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_provider_account !~ '^[A-Za-z0-9:_-]{1,200}$'
      or length(trim(coalesce(p_name,''))) not between 1 and 200
      or p_scopes is null or cardinality(p_scopes)=0
      or (p_access_hex !~ '^[0-9a-f]+
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_access_hex) not between 80 and 16384 or length(p_access_hex)%2<>0)
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_refresh_hex) not between 80 and 16384 or length(p_refresh_hex)%2<>0))
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_verifier_hex) not between 80 and 16384 or length(p_verifier_hex)%2<>0)
      or p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_redirect !~ '^https://[^/[:space:]]+/'
      or length(p_redirect)>600 then
    raise exception 'invalid OAuth state' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  insert into retail_private.social_oauth_states(
    state_digest,shop_id,requested_by,provider,verifier_ciphertext,
    exact_redirect_uri,expires_at)
  values (decode(p_digest_hex,'hex'),p_shop,p_actor,p_provider,
          decode(p_verifier_hex,'hex'),p_redirect,now()+interval '10 minutes');
  return true;
end
$$;

-- Important: update ... returning sees the newly set consumed_at. Return
-- consumed_at=NULL explicitly because the backend verifies the PRE-consume row.
-- This is a CAS: concurrent callback executions cannot both claim the state.
create function public.p2_consume_oauth_state(
  p_digest_hex text, p_shop uuid, p_actor uuid, p_provider text
) returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
  rec retail_private.social_oauth_states%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if p_digest_hex !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid OAuth digest' using errcode='22023';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    return null;
  end if;
  update retail_private.social_oauth_states s
    set consumed_at=now()
    where s.state_digest=decode(p_digest_hex,'hex')
      and s.shop_id=p_shop and s.requested_by=p_actor
      and s.provider=p_provider and s.consumed_at is null
      and s.expires_at>now()
    returning * into rec;
  if not found then return null; end if;
  return jsonb_build_object(
    'state_digest',encode(rec.state_digest,'hex'),
    'shop_id',rec.shop_id,'user_id',rec.requested_by,'provider',rec.provider,
    'expires_at',rec.expires_at,'consumed_at',null,
    'exact_redirect_uri',rec.exact_redirect_uri,
    'verifier_ciphertext',encode(rec.verifier_ciphertext,'hex')
  );
end
$$;

-- Atomic account metadata and encrypted credential persistence. Never return
-- ciphertext in response; uniqueness failures rollback both inserts.
create function public.p2_connect_social_account(
  p_id uuid,p_shop uuid,p_actor uuid,p_provider text,p_provider_account text,
  p_name text,p_scopes text[],p_access_hex text,p_refresh_hex text,
  p_key_version integer,p_expires_at timestamptz
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  if p_provider not in ('instagram','facebook','linkedin','youtube')
      or p_provider_account !~ '^[A-Za-z0-9:_-]{1,200}$'
      or length(trim(coalesce(p_name,''))) not between 1 and 200
      or p_scopes is null or cardinality(p_scopes)=0
      or (p_access_hex !~ '^[0-9a-f]+
      or (p_refresh_hex is not null
          and (p_refresh_hex !~ '^[0-9a-f]+)
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_access_hex) not between 80 and 16384 or length(p_access_hex)%2<>0)
      or (p_refresh_hex is not null
          and p_refresh_hex !~ '^(?:[0-9a-f]{2}){40,8192}$')
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_refresh_hex) not between 80 and 16384 or length(p_refresh_hex)%2<>0))
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_access_hex) not between 80 and 16384 or length(p_access_hex)%2<>0)
      or (p_refresh_hex is not null
          and (p_refresh_hex !~ '^[0-9a-f]+)
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
 or length(p_refresh_hex) not between 80 and 16384 or length(p_refresh_hex)%2<>0))
      or p_key_version < 1 then
    raise exception 'invalid verified provider account' using errcode='22023';
  end if;
  insert into public.social_accounts(
    id,shop_id,provider,provider_account_id,display_name,connected_by,
    granted_scopes,connection_status)
  values(p_id,p_shop,p_provider,p_provider_account,p_name,p_actor,p_scopes,'CONNECTED');
  insert into retail_private.social_account_credentials(
    social_account_id,encryption_key_version,access_token_ciphertext,
    refresh_token_ciphertext,expires_at)
  values(p_id,p_key_version,decode(p_access_hex,'hex'),
    case when p_refresh_hex is null then null else decode(p_refresh_hex,'hex') end,
    p_expires_at);
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_CONNECTED');
  return true;
end
$$;

-- Immediate local disconnect revokes credentials and unsent jobs inside one
-- transaction. A possibly sent SENDING job is RECONCILE, never silently retried.
create function public.p2_disconnect_social_account(
  p_shop uuid,p_id uuid,p_actor uuid
) returns boolean language plpgsql security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only operation' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.shop_memberships m
    where m.shop_id=p_shop and m.user_id=p_actor and m.active and m.role='OWNER'
  ) then
    raise exception 'owner authorization required' using errcode='42501';
  end if;
  update public.social_accounts
    set connection_status='DISCONNECTED',disconnected_at=now()
    where id=p_id and shop_id=p_shop and connection_status<>'DISCONNECTED';
  if not found then return false; end if;
  update public.social_publish_jobs set status='CANCELED',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status in ('DRAFT','APPROVED','QUEUED','RETRYABLE');
  update public.social_publish_jobs set status='RECONCILE',updated_at=now()
    where shop_id=p_shop and social_account_id=p_id
      and status='SENDING';
  delete from retail_private.social_account_credentials
    where social_account_id=p_id;
  insert into public.social_publish_audit(shop_id,actor_user_id,event_code)
    values(p_shop,p_actor,'SOCIAL_DISCONNECTED');
  return true;
end
$$;

revoke all on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  from public,anon,authenticated;
revoke all on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  from public,anon,authenticated;
revoke all on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  from public,anon,authenticated;
revoke all on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_issue_oauth_state(text,uuid,uuid,text,text,text)
  to service_role;
grant execute on function public.p2_consume_oauth_state(text,uuid,uuid,text)
  to service_role;
grant execute on function public.p2_connect_social_account(
  uuid,uuid,uuid,text,text,text,text[],text,text,integer,timestamptz)
  to service_role;
grant execute on function public.p2_disconnect_social_account(uuid,uuid,uuid)
  to service_role;
commit;
