-- RetailGrowthAI-only Part 1 platform control. Additive; NEVER modify WineShopPOS.
-- Do not grant a root account automatically. Provision an EXISTING verified
-- RetailGrowthAI auth.users UUID from the trusted Supabase SQL editor ONLY.
begin;

create table retail_private.platform_admins (
  user_id uuid primary key references auth.users(id) on delete cascade,
  active boolean not null default true,
  granted_at timestamptz not null default now()
);
revoke all on retail_private.platform_admins from public, anon, authenticated;
grant all on retail_private.platform_admins to service_role;

create table retail_private.platform_admin_audit (
  id bigint generated always as identity primary key,
  actor_id uuid not null references auth.users(id),
  shop_id uuid not null references public.shops(id),
  action text not null check (action = 'SET_SUBSCRIPTION'),
  previous_plan text not null,
  new_plan text not null,
  new_status text not null,
  reason text not null check (length(reason) between 10 and 300),
  happened_at timestamptz not null default now()
);
revoke all on retail_private.platform_admin_audit from public, anon, authenticated;
grant select on retail_private.platform_admin_audit to service_role;

-- Identical Supabase login. Platform authority is DB-owned and immediately
-- revocable; no reliance on app_metadata, user_metadata, email, or local state.
create function retail_private.assert_platform_admin()
returns void language plpgsql stable security definer set search_path = ''
as $$
begin
  if (select auth.role()) is distinct from 'authenticated'
     or (select auth.uid()) is null
     or not exists (
       select 1 from retail_private.platform_admins pa
       where pa.user_id = (select auth.uid()) and pa.active
     ) then
    raise exception 'PLATFORM_ADMIN_REQUIRED' using errcode='42501';
  end if;
end
$$;
revoke all on function retail_private.assert_platform_admin() from public, anon, authenticated;

create function public.retail_platform_me()
returns boolean language sql stable security definer set search_path = ''
as $$
  select coalesce((select auth.role()) = 'authenticated'
    and (select auth.uid()) is not null
    and exists (
      select 1 from retail_private.platform_admins pa
      where pa.user_id = (select auth.uid()) and pa.active
    ), false);
$$;
revoke all on function public.retail_platform_me() from public,anon;
grant execute on function public.retail_platform_me() to authenticated;

create function public.retail_platform_summary()
returns jsonb language plpgsql stable security definer set search_path = ''
as $$
declare result jsonb;
begin
  perform retail_private.assert_platform_admin();
  select jsonb_build_object(
    'retailers', (select count(*) from public.shops),
    'trial_shops', (select count(*) from public.shop_subscriptions
                   where plan_code='TRIAL' and status='TRIAL' and valid_until>now()),
    'active_paid_shops', (select count(*) from public.shop_subscriptions
                         where plan_code<>'TRIAL' and status='ACTIVE' and valid_until>now()),
    'expired_or_suspended', (select count(*) from public.shop_subscriptions
                            where status in ('EXPIRED','SUSPENDED') or valid_until<=now()),
    'campaigns', (select count(*) from public.campaigns),
    'reels_completed', (select count(*) from public.render_jobs where status='SUCCEEDED')
  ) into result;
  return result;
end
$$;
revoke all on function public.retail_platform_summary() from public,anon;
grant execute on function public.retail_platform_summary() to authenticated;

create function public.retail_platform_shops(p_limit integer default 25, p_offset integer default 0)
returns jsonb language plpgsql stable security definer set search_path = ''
as $$
declare result jsonb;
begin
  perform retail_private.assert_platform_admin();
  if p_limit is null or p_limit not between 1 and 50
     or p_offset is null or p_offset not between 0 and 5000 then
    raise exception 'INVALID_PAGE' using errcode='22023';
  end if;
  select jsonb_build_object(
    'total', (select count(*) from public.shops),
    'shops', coalesce((
      select jsonb_agg(jsonb_build_object(
        'shop_id', x.id, 'name', x.name, 'slug', x.slug,
        'plan_code', x.plan_code, 'subscription_status', x.sub_status,
        'valid_until', x.valid_until, 'campaigns', x.campaigns,
        'renders', x.renders
      ) order by x.created_at desc, x.id), '[]'::jsonb)
      from (
        select s.id, s.name, s.slug, s.created_at,
               sub.plan_code, sub.status as sub_status, sub.valid_until,
               (select count(*) from public.campaigns c where c.shop_id=s.id) as campaigns,
               (select count(*) from public.render_jobs r where r.shop_id=s.id) as renders
        from public.shops s
        left join public.shop_subscriptions sub on sub.shop_id=s.id
        order by s.created_at desc, s.id
        limit p_limit offset p_offset
      ) x
    )
  ) into result;
  return result;
end
$$;
revoke all on function public.retail_platform_shops(integer,integer) from public,anon;
grant execute on function public.retail_platform_shops(integer,integer) to authenticated;

-- Platform control is not a payment gateway. Privileged manual entitlements
-- always produce an append-only audit; no admin may change the access table
-- directly through PostgREST, even when their UI shows "Platform Admin".
create function public.retail_platform_set_subscription(
  p_shop_id uuid, p_plan_code text, p_status text,
  p_valid_until timestamptz, p_reason text
)
returns jsonb language plpgsql security definer set search_path = ''
as $$
declare before_row public.shop_subscriptions%rowtype;
declare after_row public.shop_subscriptions%rowtype;
begin
  perform retail_private.assert_platform_admin();
  if p_shop_id is null
     or p_plan_code is null or p_plan_code not in ('STARTER','GROWTH','BUSINESS')
     or p_status is null or p_status not in ('ACTIVE','SUSPENDED')
     or p_valid_until is null or p_valid_until <= now()
     or p_valid_until > now()+interval '366 days'
     or p_reason is null or length(btrim(p_reason)) not between 10 and 300 then
    raise exception 'INVALID_ADMIN_SUBSCRIPTION_CHANGE' using errcode='22023';
  end if;
  select * into before_row from public.shop_subscriptions
    where shop_id=p_shop_id for update;
  if not found then
    raise exception 'SUBSCRIPTION_NOT_FOUND' using errcode='P0002';
  end if;
  -- Period changes intentionally start a fresh quota window; the audit
  -- records who made the change. Historic reservations are never deleted.
  update public.shop_subscriptions set
    plan_code=p_plan_code, status=p_status,
    valid_from=now(), valid_until=p_valid_until,
    period_start=now(), period_end=least(p_valid_until,now()+interval '30 days')
  where shop_id=p_shop_id returning * into after_row;
  insert into retail_private.platform_admin_audit
    (actor_id,shop_id,action,previous_plan,new_plan,new_status,reason)
  values ((select auth.uid()),p_shop_id,'SET_SUBSCRIPTION',
          before_row.plan_code,p_plan_code,p_status,btrim(p_reason));
  return jsonb_build_object(
    'shop_id', after_row.shop_id, 'plan_code', after_row.plan_code,
    'status', after_row.status, 'valid_until', after_row.valid_until,
    'period_start', after_row.period_start, 'period_end', after_row.period_end
  );
end
$$;
revoke all on function public.retail_platform_set_subscription(uuid,text,text,timestamptz,text) from public,anon;
grant execute on function public.retail_platform_set_subscription(uuid,text,text,timestamptz,text) to authenticated;

commit;
