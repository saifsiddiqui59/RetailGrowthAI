-- Source-only transactionally captured RetailGrowthAI onboarding notifications.
-- Service worker/send is opt-in and sender credentials are NEVER in this migration.
begin;
create table retail_private.notification_outbox (
  id uuid primary key default gen_random_uuid(),
  kind text not null check (kind in ('RETAILER_SIGNUP','RETAILER_APPROVED','RETAILER_REJECTED')),
  user_id uuid not null references auth.users(id) on delete cascade,
  event_key text not null unique check (length(event_key) between 12 and 150),
  status text not null default 'PENDING' check(status in ('PENDING','CLAIMED','SENT','DEAD')),
  attempts integer not null default 0 check (attempts between 0 and 8),
  lease_token uuid,
  lease_until timestamptz,
  retry_after timestamptz not null default now(),
  last_error_code text,
  created_at timestamptz not null default now(),
  sent_at timestamptz
);
create index notification_outbox_pending
  on retail_private.notification_outbox(retry_after,created_at)
  where status in ('PENDING','CLAIMED');
revoke all on retail_private.notification_outbox from public,anon,authenticated;
grant select,insert,update on retail_private.notification_outbox to service_role;

-- Audit trigger is in the same transaction as onboarding row creation/decision.
-- No addresses or personal details are copied into the outbox.
create function retail_private.capture_onboarding_notification()
returns trigger language plpgsql security definer set search_path = '' as $$
declare event_kind text;
        unique_key text;
begin
 if tg_op='INSERT' and new.status='PENDING' then
   event_kind:='RETAILER_SIGNUP';
   unique_key:='signup:'||new.user_id::text;
 elsif tg_op='UPDATE' and new.status in ('APPROVED','REJECTED')
       and old.status is distinct from new.status then
   event_kind:=case when new.status='APPROVED' then 'RETAILER_APPROVED'
                    else 'RETAILER_REJECTED' end;
   unique_key:='review:'||new.user_id::text||':'||new.status||':'||
      coalesce(new.decided_at::text,'none');
 else return new; end if;
 insert into retail_private.notification_outbox(kind,user_id,event_key)
 values(event_kind,new.user_id,unique_key)
 on conflict(event_key) do nothing;
 return new;
end $$;
revoke all on function retail_private.capture_onboarding_notification() from public,anon,authenticated;
create trigger notifications_after_signup_request
 after insert or update on retail_private.onboarding_requests
 for each row execute function retail_private.capture_onboarding_notification();

-- Backend-only queue leasing. The sending service retrieves recipients at send time.
-- A failed/expired lease is replayed; a successful SMTP delivery is at-least-once.
create function public.claim_notifications(p_limit int default 10)
returns jsonb language plpgsql volatile security invoker set search_path = '' as $$
declare results jsonb;
begin
 if p_limit is null or p_limit not between 1 and 25 then
    raise exception 'invalid notification batch'; end if;
 with ready as (
   select id from retail_private.notification_outbox
   where ((status='PENDING' and retry_after<=now())
       or (status='CLAIMED' and lease_until<=now()))
     and attempts<8
   order by created_at,id limit p_limit for update skip locked
 ), selected as (
   update retail_private.notification_outbox n
      set status='CLAIMED',attempts=n.attempts+1,
      lease_token=gen_random_uuid(),lease_until=now()+interval '2 minutes'
   from ready r where r.id=n.id
   returning n.id,n.kind,n.user_id,n.event_key,n.lease_token,n.attempts
 )
 select coalesce(jsonb_agg(to_jsonb(selected)),'[]'::jsonb)
   into results from selected;
 return results;
end $$;
revoke all on function public.claim_notifications(int) from public,anon,authenticated;
grant execute on function public.claim_notifications(int) to service_role;

-- The only service-only identity lookup: emails are returned over backend TLS
-- after a secret-authenticated request, never to a browser or ordinary JWT.
create function public.notification_recipients(p_event_id uuid,p_token uuid)
returns jsonb language plpgsql stable security invoker set search_path = '' as $$
declare n retail_private.notification_outbox%rowtype;
        result jsonb;
begin
 select * into n from retail_private.notification_outbox
  where id=p_event_id and status='CLAIMED'
    and lease_token=p_token and lease_until>now();
 if not found then return '[]'::jsonb; end if;
 if n.kind='RETAILER_SIGNUP' then
   select coalesce(jsonb_agg(distinct u.email),'[]'::jsonb) into result
     from retail_private.platform_admins a
     join auth.users u on u.id=a.user_id
     where a.active and u.email is not null and u.email_confirmed_at is not null;
 else
   select coalesce(jsonb_agg(u.email),'[]'::jsonb) into result
     from auth.users u where u.id=n.user_id and u.email is not null
       and u.email_confirmed_at is not null;
 end if;
 return result;
end $$;
revoke all on function public.notification_recipients(uuid,uuid) from public,anon,authenticated;
grant execute on function public.notification_recipients(uuid,uuid) to service_role;

create function public.confirm_notification(p_event_id uuid,p_token uuid,p_success boolean,
 p_error text default null)
returns boolean language plpgsql volatile security invoker set search_path = '' as $$
declare updated_id uuid;
begin
 if p_success is null or (p_error is not null and (length(p_error)>64
      or p_error !~ '^[A-Z_]+$')) then raise exception 'invalid notification result' using errcode='22023'; end if;
 update retail_private.notification_outbox
  set status=case when p_success then 'SENT'
                  when attempts>=8 then 'DEAD' else 'PENDING' end,
      sent_at=case when p_success then now() else sent_at end,
      last_error_code=case when p_success then null else coalesce(p_error,'SEND_FAILED') end,
      lease_token=null,lease_until=null,
      retry_after=now()+make_interval(secs=>least(3600,30 * power(2,least(attempts,7)))::integer)
 where id=p_event_id and status='CLAIMED'
   and lease_token=p_token and lease_until>now()
 returning id into updated_id;
 return updated_id is not null;
end $$;
revoke all on function public.confirm_notification(uuid,uuid,boolean,text)
 from public,anon,authenticated;
grant execute on function public.confirm_notification(uuid,uuid,boolean,text) to service_role;
commit;
