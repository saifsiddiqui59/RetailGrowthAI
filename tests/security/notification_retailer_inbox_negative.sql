-- Only disposable local Supabase CI. Never hosted; no committed identities.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('f1000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000','authenticated','authenticated','inbox-owner-a@example.invalid','!',now(),now()),
('f1000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000','authenticated','authenticated','inbox-owner-b@example.invalid','!',now(),now()),
('f1000000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000','authenticated','authenticated','inbox-viewer@example.invalid','!',now(),now());
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f2000000-0000-4000-8000-000000000001',
'f1000000-0000-4000-8000-000000000001','Inbox Shop A','rgai-inbox-a');
insert into public.shop_memberships(shop_id,user_id,role)
values('f2000000-0000-4000-8000-000000000001',
'f1000000-0000-4000-8000-000000000003','VIEWER');
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values('f3000000-0000-4000-8000-000000000001',
'f2000000-0000-4000-8000-000000000001',
'f1000000-0000-4000-8000-000000000001','Private campaign fixture','2026-11-01');
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000002',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f2000000-0000-4000-8000-000000000002',
'f1000000-0000-4000-8000-000000000002','Inbox Shop B','rgai-inbox-b');
reset role;
select set_config('request.jwt.claim.role','service_role',true);
-- Trusted worker terminal transition is actual durable event source.
update public.campaigns set status='FAILED'
where id='f3000000-0000-4000-8000-000000000001';
do $$
begin
 if (select count(*) from retail_private.retailer_inbox_events
     where shop_id='f2000000-0000-4000-8000-000000000001')<>1
 then raise exception 'FAILED transition did not persist exactly one retailer event'; end if;
 update public.campaigns set status='FAILED'
 where id='f3000000-0000-4000-8000-000000000001';
 if (select count(*) from retail_private.retailer_inbox_events)<>1
 then raise exception 'idempotent terminal replay duplicated notification'; end if;
end $$;
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000002',true);
do $$
declare denied boolean:=false;
begin
 begin perform public.retail_retailer_inbox('f2000000-0000-4000-8000-000000000001');
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'foreign owner read inbox'; end if;
 denied:=false;
 begin perform public.retail_retailer_set_inbox_read('f2000000-0000-4000-8000-000000000001',1,true);
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'foreign owner wrote read status'; end if;
 denied:=false;
 begin perform count(*) from retail_private.retailer_inbox_events;
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'direct private inbox table access'; end if;
end $$;
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000001',true);
do $$
declare a jsonb; b jsonb; c jsonb; event_id bigint; denied boolean:=false;
begin
 a:=public.retail_retailer_inbox('f2000000-0000-4000-8000-000000000001');
 if a->>'shop_id'<>'f2000000-0000-4000-8000-000000000001'
 or (a->>'matching_total')::int<>1 or (a->>'unread_total')::int<>1
 or jsonb_array_length(a->'items')<>1
 or a#>>'{items,0,title}'<>'Campaign planning failed'
 then raise exception 'own shop private event/count mismatch'; end if;
 event_id:=(a#>>'{items,0,id}')::bigint;
 perform public.retail_retailer_set_inbox_read('f2000000-0000-4000-8000-000000000001',event_id,true);
 b:=public.retail_retailer_inbox('f2000000-0000-4000-8000-000000000001','unread');
 if (b->>'unread_total')::int<>0 or jsonb_array_length(b->'items')<>0
 then raise exception 'read status not persisted'; end if;
 perform public.retail_retailer_set_inbox_read('f2000000-0000-4000-8000-000000000001',event_id,false);
 c:=public.retail_retailer_inbox('f2000000-0000-4000-8000-000000000001');
 if (c->>'unread_total')::int<>1 then raise exception 'mark unread not persisted'; end if;
 begin perform public.retail_retailer_inbox('f2000000-0000-4000-8000-000000000001','all','all',41,0);
 exception when invalid_parameter_value then denied:=true; end;
 if not denied then raise exception 'unbounded inbox page accepted'; end if;
end $$;
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000003',true);
do $$
declare v jsonb; event_id bigint;
begin
 v:=public.retail_retailer_inbox('f2000000-0000-4000-8000-000000000001');
 if (v->>'unread_total')::int<>1 then raise exception 'per-user read receipt leaked'; end if;
 event_id:=(v#>>'{items,0,id}')::bigint;
 perform public.retail_retailer_set_inbox_read('f2000000-0000-4000-8000-000000000001',event_id,true);
 if (public.retail_retailer_inbox('f2000000-0000-4000-8000-000000000001')->>'unread_total')::int<>0
 then raise exception 'viewer cannot maintain own receipt'; end if;
end $$;
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000001',true);
update public.shop_memberships set active=false
where shop_id='f2000000-0000-4000-8000-000000000001'
 and user_id='f1000000-0000-4000-8000-000000000003';
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000003',true);
do $$
declare denied boolean:=false;
begin
 begin perform public.retail_retailer_inbox('f2000000-0000-4000-8000-000000000001');
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'revoked member kept inbox access'; end if;
end $$;
rollback;
