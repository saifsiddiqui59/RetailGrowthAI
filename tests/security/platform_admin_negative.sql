-- Disposable local Supabase CI ONLY. Verify platform login identity, no
-- self-escalation, exact cross-tenant read RPCs, audited writes and revocation.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('f1000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','platform-admin@example.invalid','!',now(),now()),
('f1000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','tenant-owner@example.invalid','!',now(),now()),
('f1000000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','tenant-viewer@example.invalid','!',now(),now());

set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000002',true);
insert into public.shops(id,owner_user_id,name,slug) values
('f1000000-0000-4000-8000-000000000011','f1000000-0000-4000-8000-000000000002','Platform fixture','rg-platform-test-one');
insert into public.shop_memberships(shop_id,user_id,role) values
('f1000000-0000-4000-8000-000000000011','f1000000-0000-4000-8000-000000000003','VIEWER');

-- Even OWNER has no global provider privileges or direct role table access.
do $$
declare denied boolean;
begin
  if public.retail_platform_me() is not false then
    raise exception 'FAIL: ordinary shop owner became platform admin';
  end if;
  denied:=false;
  begin
    perform public.retail_platform_summary();
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: owner accessed platform summary'; end if;
  denied:=false;
  begin
    perform public.retail_platform_shops(25,0);
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: owner accessed cross-shop list'; end if;
  denied:=false;
  begin
    perform public.retail_platform_set_subscription(
      'f1000000-0000-4000-8000-000000000011','BUSINESS','ACTIVE',
      now()+interval '60 days','owner attempted promotion');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: owner self-issued paid subscription'; end if;
  denied:=false;
  begin
    insert into retail_private.platform_admins(user_id) values
    ('f1000000-0000-4000-8000-000000000002');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: owner self-granted platform root'; end if;
end $$;

select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000003',true);
do $$
declare denied boolean:=false;
begin
  if public.retail_platform_me() then
    raise exception 'FAIL: viewer became platform admin';
  end if;
  begin perform public.retail_platform_summary();
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: viewer accessed provider RPC'; end if;
end $$;

-- Only privileged trusted provisioning for the *existing* root login UUID.
reset role;
insert into retail_private.platform_admins(user_id,active) values
('f1000000-0000-4000-8000-000000000001',true);
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000001',true);
do $$
declare summary jsonb;
declare listing jsonb;
declare changed jsonb;
declare denied boolean:=false;
begin
  if public.retail_platform_me() is not true then
    raise exception 'FAIL: approved root login was not recognized';
  end if;
  summary:=public.retail_platform_summary();
  if (summary->>'retailers')::integer < 1 then
    raise exception 'FAIL: root cannot read provider-level overview';
  end if;
  listing:=public.retail_platform_shops(25,0);
  if (listing->>'total')::integer < 1 or jsonb_array_length(listing->'shops') < 1 then
    raise exception 'FAIL: root cannot list retailers';
  end if;
  -- Root is NOT a shop owner. Ordinary tenant RLS remains restrictive.
  if exists(select 1 from public.shops where id='f1000000-0000-4000-8000-000000000011') then
    raise exception 'FAIL: ordinary cross-tenant SELECT bypassed RLS';
  end if;
  begin
    perform public.retail_platform_shops(51,0);
  exception when invalid_parameter_value then denied:=true;
  end;
  if not denied then raise exception 'FAIL: unbounded provider directory'; end if;
  changed:=public.retail_platform_set_subscription(
    'f1000000-0000-4000-8000-000000000011','GROWTH','ACTIVE',
    now()+interval '45 days','Manual DEV root plan assignment');
  if changed->>'plan_code'<>'GROWTH' or changed->>'status'<>'ACTIVE' then
    raise exception 'FAIL: authorized admin plan change was not applied';
  end if;
  denied:=false;
  begin
    perform public.retail_platform_set_subscription(
      'f1000000-0000-4000-8000-000000000011','TRIAL','ACTIVE',
      now()+interval '45 days','Unsafe reset to trial');
  exception when invalid_parameter_value then denied:=true;
  end;
  if not denied then raise exception 'FAIL: root forged new trial'; end if;
end $$;

-- Audit is private and append-only from the perspective of browser sessions.
reset role;
do $$
begin
  if (select count(*) from retail_private.platform_admin_audit
      where actor_id='f1000000-0000-4000-8000-000000000001'
        and shop_id='f1000000-0000-4000-8000-000000000011'
        and previous_plan='TRIAL' and new_plan='GROWTH'
        and action='SET_SUBSCRIPTION')<>1 then
    raise exception 'FAIL: missing successful privileged mutation audit';
  end if;
end $$;
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000001',true);
do $$
declare denied boolean:=false;
begin
  begin perform count(*) from retail_private.platform_admin_audit;
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: browser leaked private audit'; end if;
end $$;
reset role;
update retail_private.platform_admins set active=false
where user_id='f1000000-0000-4000-8000-000000000001';
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000001',true);
do $$
declare denied boolean:=false;
begin
  if public.retail_platform_me() then raise exception 'FAIL: revoked root still active'; end if;
  begin perform public.retail_platform_summary();
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: revoked admin continued read'; end if;
end $$;
reset role;
set local role anon;
select set_config('request.jwt.claim.role','anon',true);
select set_config('request.jwt.claim.sub','',true);
do $$
declare denied boolean:=false;
begin
  begin perform public.retail_platform_me();
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: anonymous identity probe exposed'; end if;
end $$;

-- A new retailer becomes pending; cannot self-approve or create a business
-- when the explicit owner-approved gate is switched on in DEV.
reset role;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values('f1000000-0000-4000-8000-000000000004',
       '00000000-0000-0000-0000-000000000000',
       'authenticated','authenticated','new-tenant@example.invalid','!',now(),now());
update retail_private.onboarding_gate set enforce_approval=true where singleton;
do $$
begin
  if (select status from retail_private.onboarding_requests
      where user_id='f1000000-0000-4000-8000-000000000004') <> 'PENDING' then
    raise exception 'FAIL: signup not enqueued as pending';
  end if;
end $$;
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000004',true);
do $$
declare denied boolean:=false;
declare result jsonb;
begin
  result:=public.retail_onboarding_status();
  if result->>'status' <> 'PENDING' or (result->>'approval_required')::boolean is not true then
    raise exception 'FAIL: pending registration status inaccurate';
  end if;
  begin
    insert into public.shops(id,owner_user_id,name,slug)
    values('f1000000-0000-4000-8000-000000000021',
           'f1000000-0000-4000-8000-000000000004',
           'Unapproved business','unapproved-test-shop');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: pending signup created a business'; end if;
  denied:=false;
  begin
    perform public.retail_platform_onboarding_requests();
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: new user saw approval inbox'; end if;
  denied:=false;
  begin
    perform public.retail_platform_review_onboarding(
      'f1000000-0000-4000-8000-000000000004',true,'Self approval not permitted');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: pending user approved themselves'; end if;
end $$;
reset role;
update retail_private.platform_admins set active=true
where user_id='f1000000-0000-4000-8000-000000000001';
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000001',true);
do $$
declare rows jsonb;
declare decision jsonb;
begin
  rows:=public.retail_platform_onboarding_requests('PENDING',40);
  if not exists(
    select 1 from jsonb_array_elements(rows) r
    where r->>'email'='new-tenant@example.invalid'
  ) then raise exception 'FAIL: root missing signup approval request'; end if;
  decision:=public.retail_platform_review_onboarding(
      'f1000000-0000-4000-8000-000000000004',true,'Verified new retailer manually');
  if decision->>'status'<>'APPROVED' then
    raise exception 'FAIL: signed-off approval did not persist'; end if;
end $$;
select set_config('request.jwt.claim.sub','f1000000-0000-4000-8000-000000000004',true);
do $$
declare result jsonb;
begin
  result:=public.retail_onboarding_status();
  if result->>'status'<>'APPROVED' then
    raise exception 'FAIL: customer not approved after root decision';
  end if;
end $$;
insert into public.shops(id,owner_user_id,name,slug)
values('f1000000-0000-4000-8000-000000000021',
       'f1000000-0000-4000-8000-000000000004',
       'Approved retailer','approved-test-shop');
reset role;
do $$
begin
  if not exists(select 1 from public.shop_subscriptions
    where shop_id='f1000000-0000-4000-8000-000000000021'
      and status='TRIAL') then
    raise exception 'FAIL: approved new shop did not start 7-day trial';
  end if;
end $$;

rollback;
\echo 'PASS platform root login grant, owner/editor/viewer denial, RLS isolation, audited plan change and immediate revocation'
