-- Disposable onboarding notification queue tests; never apply to live Supabase.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,email_confirmed_at,encrypted_password,created_at,updated_at)
values ('a1111111-1111-4111-8111-111111111111',
 '00000000-0000-0000-0000-000000000000','authenticated','authenticated',
 'rg-email-ci@example.invalid',now(),'!',now(),now());

-- Signup creates PENDING onboarding and exactly one outbox event in same transaction.
do $$
begin
 if (select count(*) from retail_private.notification_outbox
       where kind='RETAILER_SIGNUP' and user_id='a1111111-1111-4111-8111-111111111111')<>1 then
  raise exception 'signup email event missing or duplicated'; end if;
end $$;

update retail_private.onboarding_requests set status='APPROVED',
  decided_at=now(),decided_by='a1111111-1111-4111-8111-111111111111',
  decision_reason='Confirmed retailer test approval'
where user_id='a1111111-1111-4111-8111-111111111111';
update retail_private.onboarding_requests set decision_reason='Duplicate replay not new state'
where user_id='a1111111-1111-4111-8111-111111111111';
do $$
begin
 if (select count(*) from retail_private.notification_outbox
       where user_id='a1111111-1111-4111-8111-111111111111')<>2 then
  raise exception 'review event duplication or missing event'; end if;
end $$;

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','a1111111-1111-4111-8111-111111111111',true);
do $$
declare denied boolean:=false;
begin
 begin
  perform public.claim_notifications(1);
 exception when insufficient_privilege then denied:=true; end;
 if not denied then raise exception 'customer claimed notification'; end if;
 begin
  perform public.notification_recipients(gen_random_uuid(),gen_random_uuid());
  raise exception 'customer queried recipients';
 exception when insufficient_privilege then null; end;
end $$;

reset role;
select set_config('request.jwt.claim.role','service_role',true);
do $$
declare batch jsonb; evt jsonb; token uuid; id uuid;
begin
 batch:=public.claim_notifications(2);
 if jsonb_array_length(batch)<>2 then raise exception 'notification claim failed'; end if;
 evt:=batch->0;
 token:=(evt->>'lease_token')::uuid;
 id:=(evt->>'id')::uuid;
 if public.confirm_notification(id,gen_random_uuid(),true,null) then
   raise exception 'stale token accepted'; end if;
 begin
   perform public.confirm_notification(id,token,true,'unsafe-message');
   raise exception 'invalid email error marker accepted';
 exception when invalid_parameter_value then null; end;
 if not public.confirm_notification(id,token,true,null)
    or public.confirm_notification(id,token,true,null) then
   raise exception 'notification delivery not one-shot'; end if;
end $$;
rollback;
\echo 'PASS: private notification queue atomic signup/review, denial, leases and confirmation'
