-- Disposable CI-only Platform Super Admin monitoring, snapshot/persistence and RBAC.
-- Not intended for hosted Supabase; entire test runs under ROLLBACK.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
 ('b1000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','rg-ops-root-a@example.invalid','!',now(),now()),
 ('b1000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','rg-ops-root-b@example.invalid','!',now(),now()),
 ('b1000000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000',
  'authenticated','authenticated','rg-ops-owner@example.invalid','!',now(),now());

insert into retail_private.platform_admins(user_id) values
 ('b1000000-0000-4000-8000-000000000001'),
 ('b1000000-0000-4000-8000-000000000002');
-- The actual shop-creation trigger requires approved, signed-in owner identity.
update retail_private.onboarding_requests set
 status='APPROVED', decided_at=now(),
 decided_by='b1000000-0000-4000-8000-000000000001',
 decision_reason='Approved disposable 55-shop fixture'
where user_id='b1000000-0000-4000-8000-000000000003';

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','b1000000-0000-4000-8000-000000000003',true);
-- Create 55 verified retailer subscriptions, more than 25-row UI page.
do $$
declare idx int;
begin
 for idx in 1..55 loop
   insert into public.shops(id,owner_user_id,name,slug)
   values(gen_random_uuid(),'b1000000-0000-4000-8000-000000000003',
    'RGAI Ops Store '||lpad(idx::text,3,'0'),'rg-ops-store-'||idx::text);
 end loop;
end $$;
reset role;
select set_config('request.jwt.claim.role','service_role',true);
update public.shop_subscriptions s set valid_until=now()+interval '60 days'
from public.shops sh where sh.id=s.shop_id and sh.slug like 'rg-ops-store-%';
update public.shop_subscriptions s set valid_until=now()+interval '4 days'
from public.shops sh where sh.id=s.shop_id
  and sh.name in ('RGAI Ops Store 001','RGAI Ops Store 002','RGAI Ops Store 003',
                  'RGAI Ops Store 004','RGAI Ops Store 005');
update public.shop_subscriptions s set status='SUSPENDED'
from public.shops sh where sh.id=s.shop_id
  and sh.name in ('RGAI Ops Store 006','RGAI Ops Store 007');

-- Service-owned canary job creation (same trusted role as actual backend).
select set_config('request.jwt.claim.role','service_role',true);
-- Real FAILED campaign, delayed queue dispatch, poison receipt, all read from tables.
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
select 'b1000000-0000-4000-8000-000000000004',s.id,
 'b1000000-0000-4000-8000-000000000003','Daily verified style ideas',current_date
from public.shops s where s.slug='rg-ops-store-1';
update public.campaigns set status='FAILED'
where id='b1000000-0000-4000-8000-000000000004';
update public.job_outbox set created_at=now()-interval '30 minutes'
where kind='planning' and job_id='b1000000-0000-4000-8000-000000000004';
insert into public.job_poison_events(kind,fingerprint,job_id)
values('planning',repeat('a',64),'b1000000-0000-4000-8000-000000000004');

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','b1000000-0000-4000-8000-000000000003',true);
do $$
declare denied boolean;
begin
 denied:=false;
 begin perform public.retail_platform_notifications();
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'tenant owner read platform notifications'; end if;
 denied:=false;
 begin perform public.retail_platform_subscription_watch();
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'tenant owner queried all subscriptions'; end if;
 denied:=false;
 begin perform public.retail_platform_set_notification_read(1,true);
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'tenant owner wrote root read receipts'; end if;
 denied:=false;
 begin perform count(*) from retail_private.platform_notifications;
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'tenant owner directly selected private inbox'; end if;
end $$;

select set_config('request.jwt.claim.sub','b1000000-0000-4000-8000-000000000001',true);
do $$
declare a jsonb; b jsonb; c jsonb; id bigint; denied boolean:=false;
begin
 a:=public.retail_platform_notifications();
 if (a->>'total_active')::int < 10 or (a->>'unread_active')::int < 10 then
   raise exception 'root missing persisted DB-backed alerts'; end if;
 if not exists(select 1 from jsonb_array_elements(a->'items') t
   where t->>'category'='job' and t->>'title'='Campaign planning failed') then
   raise exception 'terminal planning failure unreported'; end if;
 if not exists(select 1 from jsonb_array_elements(a->'items') t
   where t->>'category'='queue' and t->>'title'='Planning/video dispatch backlog') then
   raise exception 'old DB outbox backlog unreported'; end if;
 if not exists(select 1 from jsonb_array_elements(a->'items') t
   where t->>'title'='Poison queue messages recorded') then
   raise exception 'poison queue receipt unreported'; end if;
 if a->>'azure_telemetry' <> 'NOT_CONNECTED' then
   raise exception 'fabricated Azure infrastructure health'; end if;
 select (t->>'id')::bigint into id from jsonb_array_elements(a->'items') t
   where t->>'event_key'='job:campaign:b1000000-0000-4000-8000-000000000004';
 if id is null then raise exception 'missing durable event'; end if;
 if (public.retail_platform_set_notification_read(id,true)->>'read')::boolean<>true then
   raise exception 'root read receipt not persisted'; end if;
 b:=public.retail_platform_notifications('history','job',40,0);
 if not exists(select 1 from jsonb_array_elements(b->'items') t
   where (t->>'id')::bigint=id and t->>'read_at' is not null) then
   raise exception 'refresh lost read receipt'; end if;
 if (public.retail_platform_set_notification_read(id,false)->>'read')::boolean<>false then
   raise exception 'root cannot restore unread status'; end if;
 c:=public.retail_platform_subscription_watch('all','',25,25);
 if (c->>'all_retailers')::int <> 55 or (c->>'total')::int <> 55
    or jsonb_array_length(c->'shops') <> 25 or (c->'counts'->>'expiring')::int <> 5
    or (c->'counts'->>'suspended')::int <> 2 then
   raise exception 'global subscription totals/pagination are incomplete'; end if;
 c:=public.retail_platform_subscription_watch('expiring','RGAI Ops Store',25,0);
 if (c->>'total')::int <> 5 then raise exception 'server side subscription filtering is not global'; end if;
 begin perform public.retail_platform_notifications('active','all',51,0);
 exception when invalid_parameter_value then denied:=true; end;
 if not denied then raise exception 'unbounded root notification list accepted'; end if;
end $$;

-- Read receipts are personal to each platform admin, not a global read toggle.
select set_config('request.jwt.claim.sub','b1000000-0000-4000-8000-000000000002',true);
do $$
declare id bigint; a jsonb;
begin
 a:=public.retail_platform_notifications('history','job',40,0);
 select (t->>'id')::bigint into id from jsonb_array_elements(a->'items') t
 where t->>'event_key'='job:campaign:b1000000-0000-4000-8000-000000000004';
 if not exists(select 1 from jsonb_array_elements(a->'items') t
  where (t->>'id')::bigint=id and t->>'read_at' is null) then
   raise exception 'different root inherited a read receipt'; end if;
end $$;

-- Immediate DB privilege revocation, even with an old authenticated JWT.
reset role;
update retail_private.platform_admins set active=false
where user_id='b1000000-0000-4000-8000-000000000001';
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','b1000000-0000-4000-8000-000000000001',true);
do $$
declare denied boolean:=false;
begin
 begin perform public.retail_platform_notifications();
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'revoked root accessed inbox'; end if;
end $$;
rollback;
\echo 'PASS: durable scoped Super Admin notifications, true DB failure/queue alerts, 55-shop pagination, RBAC and immediate revoke'
