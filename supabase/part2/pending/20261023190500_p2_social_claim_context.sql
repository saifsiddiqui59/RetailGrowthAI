-- RetailGrowthAI P2 service-only publish claim context, SOURCE ONLY.
-- Ordered after 190000..190400; no hosted Supabase writes without approval.
-- Private access tokens are exposed as AES-GCM ciphertext only to service_role.
begin;

create function public.p2_social_claim_context(p_job uuid,p_claim uuid)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare
  j public.social_publish_jobs%rowtype;
  a public.social_accounts%rowtype;
  m public.shop_memberships%rowtype;
  s public.shop_subscriptions%rowtype;
  c retail_private.social_account_credentials%rowtype;
begin
  if (select auth.role()) is distinct from 'service_role' then
    raise exception 'service role required' using errcode='42501';
  end if;

  select * into j from public.social_publish_jobs
    where id=p_job and status in ('APPROVED','QUEUED','RETRYABLE')
      and approved_by is not null and approved_at is not null
      and approved_content_sha256 is not null
    for update;
  if not found then return null; end if;
  if not exists (
    select 1 from retail_private.social_publish_attempts t
      where t.job_id=p_job and t.claim_token=p_claim
        and t.finished_at is null and t.result_code is null
        and t.started_at >= now()-interval '2 minutes'
  ) then return null; end if;
  if j.provider not in ('facebook','linkedin') or j.media_asset_id is not null then
    -- Video is denied until authoritative commercial rights + FFprobe review.
    return null;
  end if;
  if not exists (
    select 1 from public.campaign_days d
    where d.id=j.campaign_day_id and d.shop_id=j.shop_id
      and d.review_status='APPROVED'
  ) then return null; end if;

  select * into a from public.social_accounts
    where id=j.social_account_id and shop_id=j.shop_id
      and provider=j.provider and connection_status='CONNECTED';
  if not found then return null; end if;
  select * into m from public.shop_memberships
    where shop_id=j.shop_id and user_id=j.approved_by and active
      and role in ('OWNER','EDITOR');
  if not found then return null; end if;
  select * into s from public.shop_subscriptions
    where shop_id=j.shop_id and status in ('TRIAL','ACTIVE')
      and now() >= valid_from and now()<valid_until
      and now() >= period_start and now()<period_end;
  if not found then return null; end if;
  if not exists (
    select 1 from retail_private.social_publish_quota_ledger q
      where q.publish_job_id=j.id and q.shop_id=j.shop_id
        and q.period_start=s.period_start
  ) then return null; end if;

  select * into c from retail_private.social_account_credentials
    where social_account_id=a.id
      and encryption_key_version > 0
      and (expires_at is null or expires_at > now()+interval '90 seconds');
  if not found then return null; end if;
  -- A refresh path must be separately verified and configured before using a
  -- credential which is about to expire. Returning null fails closed.
  if not (
    (j.provider='linkedin' and 'w_member_social'=any(a.granted_scopes))
    or (j.provider='facebook' and 'pages_manage_posts'=any(a.granted_scopes))
  ) then return null; end if;

  return jsonb_build_object(
    'shop_id',j.shop_id,
    'job',jsonb_build_object(
      'id',j.id,'shop_id',j.shop_id,'social_account_id',j.social_account_id,
      'campaign_day_id',j.campaign_day_id,'provider',j.provider,
      'status',j.status,'approved_by',j.approved_by,'approved_at',j.approved_at,
      'approved_content_sha256',encode(j.approved_content_sha256,'hex'),
      'caption',j.caption,'media_asset_id',j.media_asset_id,
      'scheduled_at',j.scheduled_at,'timezone',j.timezone,'revision',j.revision,
      'quota_reserved',true),
    'account',jsonb_build_object(
      'id',a.id,'shop_id',a.shop_id,'provider',a.provider,
      'provider_account_id',a.provider_account_id,
      'connection_status',a.connection_status,'granted_scopes',a.granted_scopes),
    'membership',jsonb_build_object(
      'shop_id',m.shop_id,'user_id',m.user_id,'active',m.active,'role',m.role),
    'entitlement',jsonb_build_object(
      'shop_id',s.shop_id,'status',s.status,'valid_until',s.valid_until),
    'credential',jsonb_build_object(
      'access_ciphertext_hex',encode(c.access_token_ciphertext,'hex'),
      'key_version',c.encryption_key_version,'expires_at',c.expires_at)
  );
end
$$;

revoke all on function public.p2_social_claim_context(uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.p2_social_claim_context(uuid,uuid)
  to service_role;
commit;
