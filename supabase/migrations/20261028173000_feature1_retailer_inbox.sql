-- Feature #1: private retailer inbox from genuine DB terminal events only.
-- Source-only. Hosted migration and actual event delivery require separate release.
begin;
create table retail_private.retailer_inbox_events(
 id bigint generated always as identity primary key,
 shop_id uuid not null references public.shops(id) on delete cascade,
 event_key text not null unique check(length(event_key) between 12 and 160),
 category text not null check(category in ('campaign','video','poster')),
 severity text not null check(severity in ('info','attention')),
 title text not null check(length(title) between 4 and 120),
 detail text not null check(length(detail) between 4 and 240),
 created_at timestamptz not null default now()
);
create index retailer_inbox_shop_recent on retail_private.retailer_inbox_events(shop_id,created_at desc,id desc);
alter table retail_private.retailer_inbox_events enable row level security;
revoke all on retail_private.retailer_inbox_events from public,anon,authenticated;
grant select,insert on retail_private.retailer_inbox_events to service_role;
create table retail_private.retailer_inbox_reads(
 event_id bigint not null references retail_private.retailer_inbox_events(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 read_at timestamptz not null default now(),
 primary key(event_id,user_id)
);
alter table retail_private.retailer_inbox_reads enable row level security;
revoke all on retail_private.retailer_inbox_reads from public,anon,authenticated;
grant select,insert,delete on retail_private.retailer_inbox_reads to service_role;
create function retail_private.capture_retailer_job_event()
returns trigger language plpgsql security definer set search_path = '' as $$
declare v_cat text; v_title text; v_detail text; v_severity text;
begin
 if new.status is not distinct from old.status then return new; end if;
 if tg_table_name='campaigns' and new.status='FAILED' then
  v_cat:='campaign';v_title:='Campaign planning failed';
  v_detail:='Your saved campaign planning job failed. Open Campaign Studio to review.';
  v_severity:='attention';
 elsif tg_table_name='render_jobs' and new.status in ('SUCCEEDED','FAILED') then
  v_cat:='video';v_title:=case when new.status='FAILED' then 'Reel rendering failed' else 'Reel rendering completed' end;
  v_detail:=case when new.status='FAILED' then 'A video render failed. Review your private job in Campaign Studio.'
             else 'A video render completed. Open Campaign Studio for its private result.' end;
  v_severity:=case when new.status='FAILED' then 'attention' else 'info' end;
 elsif tg_table_name='poster_jobs' and new.status in ('SUCCEEDED','FAILED') then
  v_cat:='poster';v_title:=case when new.status='FAILED' then 'Poster rendering failed' else 'Poster rendering completed' end;
  v_detail:=case when new.status='FAILED' then 'A poster render failed. Review your private job in Campaign Studio.'
             else 'A poster render completed. Open Campaign Studio for its private result.' end;
  v_severity:=case when new.status='FAILED' then 'attention' else 'info' end;
 else return new; end if;
 insert into retail_private.retailer_inbox_events(shop_id,event_key,category,severity,title,detail)
 values(new.shop_id,tg_table_name||':'||new.id::text||':'||new.status,v_cat,v_severity,v_title,v_detail)
 on conflict(event_key) do nothing;
 return new;
end $$;
revoke all on function retail_private.capture_retailer_job_event() from public,anon,authenticated;
create trigger retailer_campaign_terminal_event after update of status on public.campaigns
 for each row execute function retail_private.capture_retailer_job_event();
create trigger retailer_video_terminal_event after update of status on public.render_jobs
 for each row execute function retail_private.capture_retailer_job_event();
create trigger retailer_poster_terminal_event after update of status on public.poster_jobs
 for each row execute function retail_private.capture_retailer_job_event();
-- Current auth.uid + current shop membership are authoritative; no ROOT exemption.
create function public.retail_retailer_inbox(
 p_shop_id uuid,p_view text default 'all',p_category text default 'all',
 p_limit integer default 20,p_offset integer default 0)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare v_user uuid:=(select auth.uid()); v_items jsonb; v_total bigint; v_unread bigint;
begin
 if (select auth.role()) is distinct from 'authenticated' or v_user is null
    or p_shop_id is null or not retail_private.has_role(p_shop_id,array['OWNER','EDITOR','VIEWER'])
 then raise exception 'RETAILER_INBOX_DENIED' using errcode='42501'; end if;
 if p_view is null or p_view not in ('all','unread')
    or p_category is null or p_category not in ('all','campaign','video','poster')
    or p_limit is null or p_limit not between 1 and 40
    or p_offset is null or p_offset not between 0 and 100000
 then raise exception 'INVALID_RETAILER_INBOX_QUERY' using errcode='22023'; end if;
 select count(*) into v_total from retail_private.retailer_inbox_events e
 left join retail_private.retailer_inbox_reads rr on rr.event_id=e.id and rr.user_id=v_user
 where e.shop_id=p_shop_id and (p_view='all' or rr.read_at is null)
 and (p_category='all' or e.category=p_category);
 select count(*) into v_unread from retail_private.retailer_inbox_events e
 where e.shop_id=p_shop_id and not exists(
  select 1 from retail_private.retailer_inbox_reads rr where rr.event_id=e.id and rr.user_id=v_user);
 select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id desc),'[]'::jsonb)
 into v_items from (
  select e.id,e.shop_id,e.category,e.severity,e.title,e.detail,e.created_at,rr.read_at
  from retail_private.retailer_inbox_events e
  left join retail_private.retailer_inbox_reads rr on rr.event_id=e.id and rr.user_id=v_user
  where e.shop_id=p_shop_id and (p_view='all' or rr.read_at is null)
    and (p_category='all' or e.category=p_category)
  order by e.created_at desc,e.id desc limit p_limit offset p_offset
 ) t;
 return jsonb_build_object('shop_id',p_shop_id,'matching_total',v_total,
  'unread_total',v_unread,'items',v_items,'checked_at',now());
end $$;
revoke all on function public.retail_retailer_inbox(uuid,text,text,integer,integer)
 from public,anon,authenticated;
grant execute on function public.retail_retailer_inbox(uuid,text,text,integer,integer) to authenticated;
create function public.retail_retailer_set_inbox_read(
 p_shop_id uuid,p_event_id bigint,p_read boolean)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare v_user uuid:=(select auth.uid());
begin
 if (select auth.role()) is distinct from 'authenticated' or v_user is null
    or p_shop_id is null or not retail_private.has_role(p_shop_id,array['OWNER','EDITOR','VIEWER'])
    or p_event_id is null or p_event_id<1 or p_read is null
    or not exists(select 1 from retail_private.retailer_inbox_events e
      where e.id=p_event_id and e.shop_id=p_shop_id)
 then raise exception 'RETAILER_INBOX_DENIED' using errcode='42501'; end if;
 if p_read then
  insert into retail_private.retailer_inbox_reads(event_id,user_id) values(p_event_id,v_user)
    on conflict(event_id,user_id) do nothing;
 else delete from retail_private.retailer_inbox_reads
    where event_id=p_event_id and user_id=v_user;
 end if;
 return jsonb_build_object('shop_id',p_shop_id,'id',p_event_id,'read',p_read);
end $$;
revoke all on function public.retail_retailer_set_inbox_read(uuid,bigint,boolean)
 from public,anon,authenticated;
grant execute on function public.retail_retailer_set_inbox_read(uuid,bigint,boolean) to authenticated;
commit;
