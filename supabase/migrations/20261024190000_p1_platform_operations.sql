-- RetailGrowthAI-only Platform Super Admin operations. Source-only; do not apply to PROD.
-- Persist provider-visible signals and per-admin read receipts; NO email or Azure claims.
begin;

create table retail_private.platform_notifications (
  id bigint generated always as identity primary key,
  event_key text not null unique check (length(event_key) between 5 and 180),
  category text not null check (category in ('onboarding','subscription','job','queue')),
  severity text not null check (severity in ('critical','attention','info')),
  title text not null check (length(title) between 3 and 160),
  detail text not null check (length(detail) between 3 and 350),
  shop_id uuid references public.shops(id) on delete set null,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  active boolean not null default true,
  scan_id uuid not null
);
create index platform_notifications_browse on retail_private.platform_notifications
  (active,first_seen_at desc,id desc);
alter table retail_private.platform_notifications enable row level security;
revoke all on retail_private.platform_notifications from public,anon,authenticated;
grant select on retail_private.platform_notifications to service_role;

create table retail_private.platform_notification_reads (
  notification_id bigint not null references retail_private.platform_notifications(id) on delete cascade,
  admin_id uuid not null references auth.users(id) on delete cascade,
  read_at timestamptz not null default now(),
  primary key (notification_id,admin_id)
);
create index platform_notification_reads_admin on retail_private.platform_notification_reads(admin_id);
alter table retail_private.platform_notification_reads enable row level security;
revoke all on retail_private.platform_notification_reads from public,anon,authenticated;
grant select on retail_private.platform_notification_reads to service_role;

-- Not remotely callable: both functions are in non-exposed retail_private and revoked.
create function retail_private.upsert_platform_signal(
  p_scan uuid,p_key text,p_category text,p_severity text,
  p_title text,p_detail text,p_shop uuid default null
) returns void language plpgsql security definer set search_path = ''
as $$
begin
  insert into retail_private.platform_notifications
    (scan_id,event_key,category,severity,title,detail,shop_id)
  values(p_scan,p_key,p_category,p_severity,p_title,p_detail,p_shop)
  on conflict(event_key) do update set
    scan_id=excluded.scan_id,category=excluded.category,
    severity=excluded.severity,title=excluded.title,detail=excluded.detail,
    shop_id=excluded.shop_id,last_seen_at=now(),active=true;
  -- A repeated signal retains each admin's prior read/unread decision.
end $$;
revoke all on function retail_private.upsert_platform_signal(uuid,text,text,text,text,text,uuid)
  from public,anon,authenticated;

create function retail_private.refresh_platform_signals()
returns void language plpgsql security definer set search_path = ''
as $$
declare v_scan uuid := gen_random_uuid();
declare v record;
declare v_count bigint;
begin
  perform retail_private.assert_platform_admin();
  -- Transactional sweep: if any query fails, all changes roll back (no false green).
  for v in select r.user_id,r.requested_at
    from retail_private.onboarding_requests r where r.status='PENDING' loop
    perform retail_private.upsert_platform_signal(v_scan,'onboarding:'||v.user_id::text,
      'onboarding','attention','Retailer approval pending',
      'Open Platform Control to review the pending registration.');
  end loop;
  for v in
    select s.shop_id,s.status,s.valid_until,sh.name
    from public.shop_subscriptions s join public.shops sh on sh.id=s.shop_id
    where s.status in ('SUSPENDED','EXPIRED') or s.valid_until<=now()
       or (s.valid_until<=now()+interval '7 days' and s.valid_until>now())
  loop
    perform retail_private.upsert_platform_signal(v_scan,
      'subscription:'||v.shop_id::text,'subscription',
      case when v.status in ('SUSPENDED','EXPIRED') or v.valid_until<=now()
        then 'critical' else 'attention' end,
      case when v.status='SUSPENDED' then 'Subscription suspended'
        when v.status='EXPIRED' or v.valid_until<=now() then 'Subscription expired'
        else 'Subscription expires within 7 days' end,
      'Retailer: '||left(v.name,140)||'. Review the audited subscription controls.',
      v.shop_id);
  end loop;
  for v in select id from public.campaigns where status='FAILED' loop
    perform retail_private.upsert_platform_signal(v_scan,'job:campaign:'||v.id::text,
      'job','critical','Campaign planning failed',
      'A database-backed campaign job ended FAILED. Inspect its private execution records.');
  end loop;
  for v in select id from public.render_jobs where status='FAILED' loop
    perform retail_private.upsert_platform_signal(v_scan,'job:render:'||v.id::text,
      'job','critical','Video rendering failed',
      'A database-backed FFmpeg render job ended FAILED. Inspect its private execution records.');
  end loop;
  for v in select id from public.poster_jobs where status='FAILED' loop
    perform retail_private.upsert_platform_signal(v_scan,'job:poster:'||v.id::text,
      'job','critical','Poster rendering failed',
      'A database-backed poster job ended FAILED. Inspect its private execution records.');
  end loop;

  select count(*) into v_count from public.job_poison_events
   where recorded_at >= now()-interval '24 hours';
  if v_count>0 then
    perform retail_private.upsert_platform_signal(v_scan,
      'queue:poison:'||to_char(now() at time zone 'UTC','YYYYMMDD'),
      'queue','critical','Poison queue messages recorded',
      v_count::text||' persisted planning/render poison receipts in the past 24 hours.');
  end if;
  select count(*) into v_count from public.job_outbox
   where state<>'SENT' and created_at<now()-interval '15 minutes';
  if v_count>0 then
    perform retail_private.upsert_platform_signal(v_scan,
      'queue:outbox:planning-render','queue','attention','Planning/video dispatch backlog',
      v_count::text||' unsent planning/video outbox records older than 15 minutes.');
  end if;
  select count(*) into v_count from retail_private.poster_outbox
   where state<>'SENT' and created_at<now()-interval '15 minutes';
  if v_count>0 then
    perform retail_private.upsert_platform_signal(v_scan,
      'queue:outbox:poster','queue','attention','Poster dispatch backlog',
      v_count::text||' unsent poster outbox records older than 15 minutes.');
  end if;
  select count(*) into v_count from public.render_jobs
    where status='RUNNING' and render_lease_until<now();
  if v_count>0 then
    perform retail_private.upsert_platform_signal(v_scan,
      'queue:render:stale','queue','critical','Stale video worker leases',
      v_count::text||' RUNNING video jobs have expired DB leases.');
  end if;
  select count(*) into v_count from public.poster_jobs
    where status='RUNNING' and lease_until<now();
  if v_count>0 then
    perform retail_private.upsert_platform_signal(v_scan,
      'queue:poster:stale','queue','critical','Stale poster worker leases',
      v_count::text||' RUNNING poster jobs have expired DB leases.');
  end if;
  update retail_private.platform_notifications set active=false
    where active and scan_id<>v_scan;
end $$;
revoke all on function retail_private.refresh_platform_signals() from public,anon,authenticated;

-- Every call verifies a CURRENT DB-based root grant and refreshes real DB signals.
-- A missing table or failed query returns an error instead of fabricated zero alerts.
create function public.retail_platform_notifications(
  p_view text default 'active',p_category text default 'all',
  p_limit integer default 40,p_offset integer default 0
) returns jsonb language plpgsql security definer set search_path = ''
as $$
declare v_actor uuid; v_total bigint; v_unread bigint; v_rows jsonb;
begin
  perform retail_private.assert_platform_admin();
  if p_view is null or p_view not in ('active','unread','history')
     or p_category is null or p_category not in ('all','onboarding','subscription','job','queue')
     or p_limit is null or p_limit not between 1 and 50
     or p_offset is null or p_offset not between 0 and 100000 then
    raise exception 'INVALID_ALERT_QUERY' using errcode='22023';
  end if;
  v_actor := auth.uid();
  perform retail_private.refresh_platform_signals();
  select count(*), count(*) filter (where r.notification_id is null)
    into v_total,v_unread from retail_private.platform_notifications n
    left join retail_private.platform_notification_reads r
      on r.notification_id=n.id and r.admin_id=v_actor
    where n.active;
  select coalesce(jsonb_agg(to_jsonb(t) order by t.first_seen_at desc,t.id desc),'[]'::jsonb)
    into v_rows from (
      select n.id,n.event_key,n.category,n.severity,n.title,n.detail,
        n.shop_id,n.first_seen_at,n.last_seen_at,n.active,
        r.read_at
      from retail_private.platform_notifications n
      left join retail_private.platform_notification_reads r
        on r.notification_id=n.id and r.admin_id=v_actor
      where (p_view='history' or n.active)
        and (p_view<>'unread' or r.read_at is null)
        and (p_category='all' or n.category=p_category)
      order by n.first_seen_at desc,n.id desc
      limit p_limit offset p_offset
    ) t;
  return jsonb_build_object('total_active',v_total,'unread_active',v_unread,
    'items',v_rows,'database_checked_at',now(),
    'azure_telemetry','NOT_CONNECTED');
end $$;
revoke all on function public.retail_platform_notifications(text,text,integer,integer)
  from public,anon,authenticated;
grant execute on function public.retail_platform_notifications(text,text,integer,integer)
  to authenticated;

create function public.retail_platform_set_notification_read(
  p_notification_id bigint,p_read boolean
) returns jsonb language plpgsql security definer set search_path = ''
as $$
declare v_actor uuid;
begin
  perform retail_private.assert_platform_admin();
  if p_notification_id is null or p_notification_id<1 or p_read is null
    or not exists(select 1 from retail_private.platform_notifications n
                  where n.id=p_notification_id) then
    raise exception 'INVALID_NOTIFICATION' using errcode='22023';
  end if;
  v_actor:=auth.uid();
  if p_read then
    insert into retail_private.platform_notification_reads(notification_id,admin_id)
      values(p_notification_id,v_actor)
      on conflict(notification_id,admin_id) do nothing;
  else
    delete from retail_private.platform_notification_reads
      where notification_id=p_notification_id and admin_id=v_actor;
  end if;
  return jsonb_build_object('id',p_notification_id,'read',p_read);
end $$;
revoke all on function public.retail_platform_set_notification_read(bigint,boolean)
  from public,anon,authenticated;
grant execute on function public.retail_platform_set_notification_read(bigint,boolean)
  to authenticated;

-- Full-platform subscription search, counting every retailer before pagination.
create function public.retail_platform_subscription_watch(
  p_status text default 'all',p_search text default '',
  p_limit integer default 25,p_offset integer default 0
) returns jsonb language plpgsql stable security definer set search_path = ''
as $$
declare v_result jsonb;
begin
  perform retail_private.assert_platform_admin();
  if p_status is null or p_status not in ('all','expiring','expired','suspended','unknown','healthy')
     or p_search is null or length(p_search)>80
     or p_limit is null or p_limit not between 1 and 50
     or p_offset is null or p_offset not between 0 and 100000 then
    raise exception 'INVALID_SUBSCRIPTION_WATCH' using errcode='22023';
  end if;
  with base as materialized (
    select sh.id as shop_id,sh.name,sh.slug,sh.created_at,sub.plan_code,
      sub.status as subscription_status,sub.valid_until,
      case when sub.status='SUSPENDED' then 'suspended'
        when sub.status='EXPIRED' or sub.valid_until<=now() then 'expired'
        when sub.valid_until is not null and sub.valid_until<=now()+interval '7 days' then 'expiring'
        when sub.status is null or sub.valid_until is null then 'unknown'
        else 'healthy' end as health
    from public.shops sh left join public.shop_subscriptions sub on sub.shop_id=sh.id
  ), selected as materialized (
    select * from base
    where (p_status='all' or health=p_status)
      and (btrim(p_search)='' or position(lower(btrim(p_search))
        in lower(coalesce(name,'')||' '||coalesce(slug,'')||' '||coalesce(plan_code,'')))>0)
  )
  select jsonb_build_object(
    'total',(select count(*) from selected),
    'all_retailers',(select count(*) from base),
    'counts',(select jsonb_build_object(
      'expiring',count(*) filter(where health='expiring'),
      'expired',count(*) filter(where health='expired'),
      'suspended',count(*) filter(where health='suspended'),
      'unknown',count(*) filter(where health='unknown'),
      'healthy',count(*) filter(where health='healthy')
    ) from base),
    'shops',coalesce((
      select jsonb_agg(to_jsonb(x) order by x.created_at desc,x.shop_id)
      from (select shop_id,name,slug,plan_code,subscription_status,valid_until,health,created_at
        from selected order by created_at desc,shop_id limit p_limit offset p_offset) x
    ),'[]'::jsonb)
  ) into v_result;
  return v_result;
end $$;
revoke all on function public.retail_platform_subscription_watch(text,text,integer,integer)
  from public,anon,authenticated;
grant execute on function public.retail_platform_subscription_watch(text,text,integer,integer)
  to authenticated;
commit;
