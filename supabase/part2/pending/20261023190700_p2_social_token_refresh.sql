-- P2 separately staged credential refresh transaction. NOT HOSTED.
-- Requires social foundation, attempts and 190500 claim-context migrations.
begin;

create function public.p2_social_refresh_context(p_job uuid,p_claim uuid)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  a public.social_accounts%rowtype;
  c retail_private.social_account_credentials%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only token refresh' using errcode='42501';
  end if;
  select * into j from public.social_publish_jobs
    where id=p_job and status in ('APPROVED','QUEUED','RETRYABLE')
    for update;
  if not found or j.approved_by is null or
      not exists(
        select 1 from retail_private.social_publish_attempts t
        where t.job_id=p_job and t.claim_token=p_claim
          and t.finished_at is null and t.result_code is null
          and t.started_at>=now()-interval '2 minutes'
      ) or not exists(
        select 1 from public.shop_memberships m
        where m.shop_id=j.shop_id and m.user_id=j.approved_by
          and m.active and m.role in ('OWNER','EDITOR')
      ) or not exists(
        select 1 from retail_private.social_publish_quota_ledger l
        join public.shop_subscriptions s
        on s.shop_id=l.shop_id and s.period_start=l.period_start
        where l.publish_job_id=p_job and l.shop_id=j.shop_id
          and s.status in ('TRIAL','ACTIVE')
          and now()>=s.valid_from and now()<s.valid_until
          and now()>=s.period_start and now()<s.period_end
      ) then return null; end if;
  select * into a from public.social_accounts
    where id=j.social_account_id and shop_id=j.shop_id
      and provider=j.provider and connection_status='CONNECTED'
      and provider in ('youtube','linkedin');
  if not found then return null; end if;
  select * into c from retail_private.social_account_credentials
    where social_account_id=a.id
      and refresh_token_ciphertext is not null
      and encryption_key_version>0;
  if not found then return null; end if;
  return jsonb_build_object(
    'shop_id',j.shop_id,'account_id',a.id,'provider',a.provider,
    'granted_scopes',a.granted_scopes,
    'access_ciphertext_hex',encode(c.access_token_ciphertext,'hex'),
    'refresh_ciphertext_hex',encode(c.refresh_token_ciphertext,'hex'),
    'key_version',c.encryption_key_version,
    'expires_at',c.expires_at);
end
$$;

create function public.p2_rotate_social_access(
  p_job uuid,p_claim uuid,p_expected_access_hex text,
  p_new_access_hex text,p_new_refresh_hex text,
  p_expires_at timestamptz,p_key_version integer
) returns boolean language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  a public.social_accounts%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'server-only token refresh' using errcode='42501';
  end if;
  if p_expected_access_hex is null
     or p_new_access_hex is null
     or p_expected_access_hex !~ '^[0-9a-f]+$'
     or p_new_access_hex !~ '^[0-9a-f]+$'
     or length(p_expected_access_hex) not between 80 and 16384
     or length(p_new_access_hex) not between 80 and 16384
     or length(p_expected_access_hex)%2<>0
     or length(p_new_access_hex)%2<>0
     or (p_new_refresh_hex is not null and (
          p_new_refresh_hex !~ '^[0-9a-f]+$'
          or length(p_new_refresh_hex) not between 80 and 16384
          or length(p_new_refresh_hex)%2<>0))
     or p_key_version is null or p_key_version<1
     or p_expires_at is null
     or p_expires_at<=now()+interval '2 minutes'
     or p_expires_at>now()+interval '90 days'
     then raise exception 'unapproved refresh envelope' using errcode='22023';
  end if;
  select * into j from public.social_publish_jobs
    where id=p_job and status in ('APPROVED','QUEUED','RETRYABLE')
    for update;
  if not found or j.approved_by is null or not exists(
      select 1 from retail_private.social_publish_attempts t
        where t.job_id=p_job and t.claim_token=p_claim
          and t.finished_at is null and t.result_code is null
          and t.started_at>=now()-interval '2 minutes'
     ) or not exists(
      select 1 from public.shop_memberships m
        where m.shop_id=j.shop_id and m.user_id=j.approved_by
          and m.active and m.role in ('OWNER','EDITOR')
     ) then return false; end if;
  select * into a from public.social_accounts
    where id=j.social_account_id and shop_id=j.shop_id
      and provider=j.provider and connection_status='CONNECTED'
      and provider in ('youtube','linkedin');
  if not found then return false; end if;
  update retail_private.social_account_credentials
    set access_token_ciphertext=decode(p_new_access_hex,'hex'),
        refresh_token_ciphertext=coalesce(
          decode(p_new_refresh_hex,'hex'),refresh_token_ciphertext),
        expires_at=p_expires_at,updated_at=now()
    where social_account_id=a.id
      and encryption_key_version=p_key_version
      and access_token_ciphertext=decode(p_expected_access_hex,'hex')
      and refresh_token_ciphertext is not null;
  return found;
end
$$;

revoke all on function public.p2_social_refresh_context(uuid,uuid)
  from public,anon,authenticated;
revoke all on function public.p2_rotate_social_access(
  uuid,uuid,text,text,text,timestamptz,integer)
  from public,anon,authenticated;
grant execute on function public.p2_social_refresh_context(uuid,uuid)
  to service_role;
grant execute on function public.p2_rotate_social_access(
  uuid,uuid,text,text,text,timestamptz,integer)
  to service_role;
commit;
