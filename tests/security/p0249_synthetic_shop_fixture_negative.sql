-- Disposable LOCAL Supabase CI only. No hosted account, key, or mutation.
-- Verify the test-only SERVICE_ROLE path without altering global onboarding.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,
                       raw_app_meta_data,created_at,updated_at)
values
('f2000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','rgai-canary-0a1b2c3d4e5f-a@example.invalid','!',
 '{"rgai_dev_fixture_mode":"browser-upload-synthetic","rgai_dev_run_id":"45046677003","rgai_dev_run_attempt":"1"}'::jsonb,now(),now()),
('f2000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','rgai-canary-0a1b2c3d4e5f-b@example.invalid','!',
 '{"rgai_dev_fixture_mode":"browser-upload-synthetic","rgai_dev_run_id":"45046677003","rgai_dev_run_attempt":"1"}'::jsonb,now(),now()),
('f2000000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000',
 'authenticated','authenticated','ordinary-retailer@example.invalid','!',
 '{"rgai_dev_fixture_mode":"browser-upload-synthetic","rgai_dev_run_id":"45046677003","rgai_dev_run_attempt":"1"}'::jsonb,now(),now());

update retail_private.onboarding_gate set enforce_approval=true where singleton;
do $$
begin
  if (select enabled from retail_private.p0249_synthetic_canary_gate where singleton)
  then raise exception 'FAIL: synthetic fixture gate enabled automatically'; end if;
  if exists(select 1 from retail_private.onboarding_requests
            where user_id in ('f2000000-0000-4000-8000-000000000001',
                              'f2000000-0000-4000-8000-000000000002',
                              'f2000000-0000-4000-8000-000000000003')
              and status<>'PENDING')
  then raise exception 'FAIL: synthetic users auto-approved at signup'; end if;
end $$;

-- No public or signed-in user may call the service-only canary routine.
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f2000000-0000-4000-8000-000000000001',true);
do $$
declare denied boolean:=false;
begin
  begin
    perform public.p0249_dev_authorize_synthetic_retailer(
      'f2000000-0000-4000-8000-000000000001', '45046677003', '1');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: authenticated user invoked fixture approval'; end if;
end $$;
set local role anon;
select set_config('request.jwt.claim.role','anon',true);
select set_config('request.jwt.claim.sub','',true);
do $$
declare denied boolean:=false;
begin
  begin
    perform public.p0249_dev_authorize_synthetic_retailer(
      'f2000000-0000-4000-8000-000000000001', '45046677003', '1');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: anonymous user invoked fixture approval'; end if;
end $$;

-- Even trusted service_role is DENIED until a separate DEV-only enablement.
set local role service_role;
select set_config('request.jwt.claim.role','service_role',true);
do $$
declare denied boolean:=false;
begin
  begin
    perform public.p0249_dev_authorize_synthetic_retailer(
      'f2000000-0000-4000-8000-000000000001', '45046677003', '1');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: disabled fixture gate allowed approval'; end if;
end $$;

reset role;
update retail_private.p0249_synthetic_canary_gate set enabled=true where singleton;
set local role service_role;
select set_config('request.jwt.claim.role','service_role',true);
do $$
declare denied boolean:=false;
declare result jsonb;
begin
  -- Metadata-bound run cannot be forged.
  begin perform public.p0249_dev_authorize_synthetic_retailer(
    'f2000000-0000-4000-8000-000000000001', '45046677004', '1');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: wrong GitHub run authorized'; end if;
  denied:=false;
  begin perform public.p0249_dev_authorize_synthetic_retailer(
    'f2000000-0000-4000-8000-000000000003', '45046677003', '1');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: ordinary retailer eligible as fixture'; end if;
  result:=public.p0249_dev_authorize_synthetic_retailer(
    'f2000000-0000-4000-8000-000000000001', '45046677003', '1');
  if result<>'{"status":"APPROVED","synthetic_fixture":true}'::jsonb
  then raise exception 'FAIL: fixture approved wrong result'; end if;
  result:=public.p0249_dev_authorize_synthetic_retailer(
    'f2000000-0000-4000-8000-000000000002', '45046677003', '1');
  if result->>'status'<>'APPROVED'
  then raise exception 'FAIL: second fixture not approved'; end if;
  denied:=false;
  begin perform public.p0249_dev_authorize_synthetic_retailer(
    'f2000000-0000-4000-8000-000000000001', '45046677003', '1');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: previously-approved fixture replay accepted'; end if;
end $$;

-- User-JWT onboarding and normal RLS still enforce own-shop ownership.
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','f2000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f2000000-0000-4000-8000-000000000011',
       'f2000000-0000-4000-8000-000000000001','Synthetic shop A','synthetic-shop-a');
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values('f2000000-0000-4000-8000-000000000021',
       'f2000000-0000-4000-8000-000000000011',
       'f2000000-0000-4000-8000-000000000001',
       'Synthetic clothing launch A','2026-11-23');
select set_config('request.jwt.claim.sub','f2000000-0000-4000-8000-000000000002',true);
insert into public.shops(id,owner_user_id,name,slug)
values('f2000000-0000-4000-8000-000000000012',
       'f2000000-0000-4000-8000-000000000002','Synthetic shop B','synthetic-shop-b');
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values('f2000000-0000-4000-8000-000000000022',
       'f2000000-0000-4000-8000-000000000012',
       'f2000000-0000-4000-8000-000000000002',
       'Synthetic clothing launch B','2026-11-23');
do $$
declare denied boolean:=false;
begin
  if exists(select 1 from public.shops
            where id='f2000000-0000-4000-8000-000000000011')
   or exists(select 1 from public.campaigns
             where id='f2000000-0000-4000-8000-000000000021')
  then raise exception 'FAIL: synthetic fixture bypassed tenant isolation'; end if;
  begin
    insert into public.campaigns(shop_id,created_by,brief,start_date)
    values('f2000000-0000-4000-8000-000000000011',
           'f2000000-0000-4000-8000-000000000002',
           'Foreign shop attempted write','2026-11-23');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: synthetic fixture wrote foreign campaign'; end if;
end $$;
select set_config('request.jwt.claim.sub','f2000000-0000-4000-8000-000000000003',true);
do $$
declare denied boolean:=false;
begin
  begin
    insert into public.shops(id,owner_user_id,name,slug)
    values('f2000000-0000-4000-8000-000000000013',
           'f2000000-0000-4000-8000-000000000003',
           'Ordinary unapproved','synthetic-unapproved-c');
  exception when insufficient_privilege then denied:=true;
  end;
  if not denied then raise exception 'FAIL: ordinary pending user created shop'; end if;
end $$;

-- Confirm exact synthetic fixture cleanup handles the decision-row self-FK.
reset role;
delete from public.shops where id in
  ('f2000000-0000-4000-8000-000000000011',
   'f2000000-0000-4000-8000-000000000012');
delete from auth.users where id in
  ('f2000000-0000-4000-8000-000000000001',
   'f2000000-0000-4000-8000-000000000002');
do $$
begin
  if exists(select 1 from retail_private.onboarding_requests
    where user_id in ('f2000000-0000-4000-8000-000000000001',
                      'f2000000-0000-4000-8000-000000000002'))
  then raise exception 'FAIL: synthetic onboarding receipts survived cleanup'; end if;
end $$;
rollback;
\echo 'PASS local-only synthetic DEV shop approval, 2-shop campaign RLS, ordinary user denial, exact cleanup'
