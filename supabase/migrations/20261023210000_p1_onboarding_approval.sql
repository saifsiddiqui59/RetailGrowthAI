-- RetailGrowthAI-only gated retailer onboarding. No WineShopPOS resources.
-- IMPORTANT: enforcement OFF initially to preserve existing tenants/release tests.
-- Enable separately in DEV AFTER UI/RPC deployment and role E2E verification.
begin;

create table retail_private.onboarding_requests (
  user_id uuid primary key references auth.users(id) on delete cascade,
  status text not null default 'PENDING'
    check (status in ('PENDING','APPROVED','REJECTED')),
  requested_at timestamptz not null default now(),
  decided_at timestamptz,
  decided_by uuid references auth.users(id),
  decision_reason text,
  constraint onboarding_review_consistency check (
    (status = 'PENDING' and decided_at is null and decided_by is null)
    or (status <> 'PENDING' and decided_at is not null and decided_by is not null)
  )
);
revoke all on retail_private.onboarding_requests from public, anon, authenticated;
grant all on retail_private.onboarding_requests to service_role;

-- Existing users had access before this opt-in approval gate. Preserve them;
-- new signups are PENDING even if Supabase Auth auto-confirms an email.
insert into retail_private.onboarding_requests
  (user_id,status,decided_at,decided_by,decision_reason)
select u.id,'APPROVED',now(),u.id,'Existing user preserved before onboarding gate'
from auth.users u
on conflict (user_id) do nothing;

create function retail_private.queue_on_signup()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  insert into retail_private.onboarding_requests (user_id)
  values (new.id) on conflict (user_id) do nothing;
  return new;
end
$$;
revoke all on function retail_private.queue_on_signup() from public, anon, authenticated;
create trigger retail_queue_on_auth_signup
after insert on auth.users
for each row execute function retail_private.queue_on_signup();

create table retail_private.onboarding_gate (
  singleton boolean primary key default true check (singleton),
  enforce_approval boolean not null default false
);
insert into retail_private.onboarding_gate (singleton,enforce_approval)
values (true,false);
revoke all on retail_private.onboarding_gate from public,anon,authenticated;
grant select on retail_private.onboarding_gate to service_role;

create function retail_private.shop_onboarding_allowed()
returns boolean language sql stable security definer set search_path = ''
as $$
  select (select auth.uid()) is not null and (
    not coalesce((select enforce_approval
                  from retail_private.onboarding_gate where singleton), true)
    or exists (select 1 from retail_private.onboarding_requests r
               where r.user_id=(select auth.uid()) and r.status='APPROVED')
    or exists (select 1 from retail_private.platform_admins p
               where p.user_id=(select auth.uid()) and p.active)
  );
$$;
revoke all on function retail_private.shop_onboarding_allowed() from public,anon;
grant execute on function retail_private.shop_onboarding_allowed() to authenticated;

-- Existing RLS still requires shop owner = current JWT user. The new check
-- is performed by the database, never by a browser boolean.
drop policy shops_create on public.shops;
create policy shops_create on public.shops for insert to authenticated
with check (owner_user_id=(select auth.uid())
  and retail_private.shop_onboarding_allowed());

create function public.retail_onboarding_status()
returns jsonb language plpgsql stable security definer set search_path = ''
as $$
declare v_status text;
declare v_enforced boolean;
begin
  if (select auth.role()) is distinct from 'authenticated' or (select auth.uid()) is null then
    raise exception 'SIGN_IN_REQUIRED' using errcode='42501';
  end if;
  select enforce_approval into v_enforced from retail_private.onboarding_gate
  where singleton;
  select status into v_status from retail_private.onboarding_requests
  where user_id=(select auth.uid());
  return jsonb_build_object(
    'status', coalesce(v_status,'PENDING'),
    'approval_required', coalesce(v_enforced,true));
end
$$;
revoke all on function public.retail_onboarding_status() from public,anon;
grant execute on function public.retail_onboarding_status() to authenticated;

create function public.retail_platform_onboarding_requests(
  p_status text default 'PENDING', p_limit int default 40)
returns jsonb language plpgsql stable security definer set search_path = ''
as $$
declare v_result jsonb;
begin
  perform retail_private.assert_platform_admin();
  if p_status not in ('PENDING','APPROVED','REJECTED')
     or p_status is null or p_limit is null or p_limit not between 1 and 50 then
    raise exception 'INVALID_APPROVAL_QUERY' using errcode='22023';
  end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'user_id', t.user_id, 'email', t.email, 'requested_at', t.requested_at,
    'status', t.status, 'decided_at', t.decided_at
  ) order by t.requested_at, t.user_id),'[]'::jsonb)
  into v_result from (
    select r.user_id,u.email,r.requested_at,r.status,r.decided_at
    from retail_private.onboarding_requests r
    join auth.users u on u.id=r.user_id
    where r.status=p_status
    order by r.requested_at,r.user_id
    limit p_limit
  ) t;
  return v_result;
end
$$;
revoke all on function public.retail_platform_onboarding_requests(text,int) from public,anon;
grant execute on function public.retail_platform_onboarding_requests(text,int) to authenticated;

create function public.retail_platform_review_onboarding(
  p_user_id uuid, p_approve boolean, p_reason text)
returns jsonb language plpgsql security definer set search_path = ''
as $$
declare v_record retail_private.onboarding_requests%rowtype;
declare v_status text;
begin
  perform retail_private.assert_platform_admin();
  if p_user_id is null or p_user_id=(select auth.uid())
     or p_approve is null or p_reason is null
     or length(btrim(p_reason)) not between 10 and 300 then
    raise exception 'INVALID_APPROVAL_DECISION' using errcode='22023';
  end if;
  select * into v_record from retail_private.onboarding_requests
    where user_id=p_user_id for update;
  if not found or v_record.status <> 'PENDING' then
    raise exception 'APPROVAL_NOT_PENDING' using errcode='P0002';
  end if;
  v_status := case when p_approve then 'APPROVED' else 'REJECTED' end;
  update retail_private.onboarding_requests
  set status=v_status,decided_at=now(),decided_by=(select auth.uid()),
      decision_reason=btrim(p_reason)
  where user_id=p_user_id;
  return jsonb_build_object('user_id',p_user_id,'status',v_status);
end
$$;
revoke all on function public.retail_platform_review_onboarding(uuid,boolean,text) from public,anon;
grant execute on function public.retail_platform_review_onboarding(uuid,boolean,text) to authenticated;

commit;
