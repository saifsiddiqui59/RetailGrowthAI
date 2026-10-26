-- WARNING: use ONLY an isolated disposable Supabase local test database.
-- Required: both foundation + private-media migrations. Transaction always rolls back.
\set ON_ERROR_STOP on
begin;
insert into auth.users (id, instance_id, aud, role, email, encrypted_password, created_at, updated_at)
values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','00000000-0000-0000-0000-000000000000','authenticated','authenticated','rls-a@example.invalid','!',now(),now()),
 ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','00000000-0000-0000-0000-000000000000','authenticated','authenticated','rls-b@example.invalid','!',now(),now()),
 ('cccccccc-cccc-4ccc-8ccc-cccccccccccc','00000000-0000-0000-0000-000000000000','authenticated','authenticated','rls-c@example.invalid','!',now(),now());
set local role authenticated;
-- Simulate the signed JWT role accurately for auth.role() in guarded triggers.
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',true);
insert into public.shops(id,owner_user_id,name,slug)
values('10000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','Shop A','rg-security-shop-a');
insert into public.campaigns(id,shop_id,created_by,brief,start_date)
values('20000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001',
       'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','First shop campaign','2026-11-01');
do $$
begin
  if not exists (select 1 from public.shop_memberships
                 where shop_id='10000000-0000-4000-8000-000000000001'
                   and user_id=auth.uid() and role='OWNER') then
    raise exception 'FAIL: shop bootstrap OWNER missing';
  end if;
  if not exists (select 1 from public.business_profiles
                 where shop_id='10000000-0000-4000-8000-000000000001') then
    raise exception 'FAIL: business profile bootstrap missing';
  end if;
end $$;
-- Owner may grant a VIEWER seat to an existing user, but never an OWNER seat.
insert into public.shop_memberships(shop_id,user_id,role)
values('10000000-0000-4000-8000-000000000001',
       'cccccccc-cccc-4ccc-8ccc-cccccccccccc','VIEWER');

select set_config('request.jwt.claim.sub','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',true);
insert into public.shops(id,owner_user_id,name,slug)
values('10000000-0000-4000-8000-000000000002','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','Shop B','rg-security-shop-b');
do $$
declare rows_changed integer; denied boolean;
begin
  -- B cannot discover A's shop, profile, campaign or membership.
  if exists (select 1 from public.shops where id='10000000-0000-4000-8000-000000000001')
    or exists (select 1 from public.business_profiles where shop_id='10000000-0000-4000-8000-000000000001')
    or exists (select 1 from public.campaigns where shop_id='10000000-0000-4000-8000-000000000001')
    or exists (select 1 from public.shop_memberships where shop_id='10000000-0000-4000-8000-000000000001')
  then raise exception 'FAIL: cross-tenant SELECT leaked'; end if;

  update public.business_profiles set description='ATTACK' where shop_id='10000000-0000-4000-8000-000000000001';
  get diagnostics rows_changed = row_count;
  if rows_changed <> 0 then raise exception 'FAIL: cross-tenant profile UPDATE allowed'; end if;

  denied := false;
  begin
    insert into public.campaigns(shop_id,created_by,brief,start_date)
    values('10000000-0000-4000-8000-000000000001',
           'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','forged campaign','2026-11-01');
  exception when insufficient_privilege then denied := true;
  end;
  if not denied then raise exception 'FAIL: forged campaign shop_id accepted'; end if;

  denied := false;
  begin
    insert into public.shop_memberships(shop_id,user_id,role)
    values('10000000-0000-4000-8000-000000000001',
           'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','EDITOR');
  exception when insufficient_privilege then denied := true;
  end;
  if not denied then raise exception 'FAIL: self-invitation to another shop accepted'; end if;

  denied := false;
  begin
    insert into public.shops(owner_user_id,name,slug)
    values('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','Forged owner','rg-security-forged');
  exception when insufficient_privilege then denied := true;
  end;
  if not denied then raise exception 'FAIL: other-user shop ownership accepted'; end if;

  denied := false;
  begin
    execute 'update public.shops set owner_user_id = ' ||
      quote_literal('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb') ||
      ' where id = ' || quote_literal('10000000-0000-4000-8000-000000000002');
  exception when insufficient_privilege then denied := true;
  end;
  if not denied then raise exception 'FAIL: immutable owner column mutated'; end if;

  denied := false;
  begin
    insert into public.media_assets(shop_id,created_by,object_path,mime_type,source)
    values('10000000-0000-4000-8000-000000000001',
           'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
           '10000000-0000-4000-8000-000000000001/stolen.png','image/png','UPLOAD');
  exception when insufficient_privilege then denied := true;
  end;
  if not denied then raise exception 'FAIL: wrong-shop media INSERT allowed'; end if;
end $$;

select set_config('request.jwt.claim.sub','cccccccc-cccc-4ccc-8ccc-cccccccccccc',true);
do $$
declare changed integer; denied boolean := false;
begin
  if not exists (select 1 from public.shops where id='10000000-0000-4000-8000-000000000001')
  then raise exception 'FAIL: viewer cannot read own shop'; end if;
  update public.business_profiles set description='VIEWER ATTACK'
  where shop_id='10000000-0000-4000-8000-000000000001';
  get diagnostics changed = row_count;
  if changed <> 0 then raise exception 'FAIL: viewer changed profile'; end if;
  update public.shop_memberships set role='OWNER'
  where shop_id='10000000-0000-4000-8000-000000000001'
    and user_id=auth.uid();
  get diagnostics changed = row_count;
  if changed <> 0 then raise exception 'FAIL: viewer self-promoted'; end if;
  begin
    insert into public.campaigns(shop_id,created_by,brief,start_date)
    values('10000000-0000-4000-8000-000000000001',
           'cccccccc-cccc-4ccc-8ccc-cccccccccccc','viewer write','2026-11-01');
  exception when insufficient_privilege then denied := true;
  end;
  if not denied then raise exception 'FAIL: viewer campaign INSERT allowed'; end if;
end $$;

-- Revoking membership must immediately close all current reads, regardless of JWT age.
select set_config('request.jwt.claim.sub','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',true);
update public.shop_memberships set active=false
where shop_id='10000000-0000-4000-8000-000000000001'
  and user_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc';
select set_config('request.jwt.claim.sub','cccccccc-cccc-4ccc-8ccc-cccccccccccc',true);
do $$
begin
  if exists (select 1 from public.shops where id='10000000-0000-4000-8000-000000000001')
  then raise exception 'FAIL: inactive membership retained shop access'; end if;
  if retail_private.media_path_shop('not-a-uuid/something') is not null
  then raise exception 'FAIL: malformed media path accepted'; end if;
end $$;

-- Anonymous client with no subject can never read a tenant row.
reset role;
-- Subsequent DB-owner setup calls simulate the server's service_role JWT.
select set_config('request.jwt.claim.role','service_role',true);
set local role anon;
select set_config('request.jwt.claim.role','anon',true);
select set_config('request.jwt.claim.sub','',true);
do $$
declare denied boolean := false;
begin
  begin
    if exists (select 1 from public.shops) then raise exception 'FAIL: anon read shops'; end if;
  exception when insufficient_privilege then denied := true;
  end;
  -- Denial by either lack of table GRANT or RLS-visible zero rows is acceptable.
  if not denied and exists (select 1 from information_schema.role_table_grants
      where grantee='anon' and table_name='shops' and privilege_type='SELECT') then
    raise exception 'FAIL: anonymous table grant was unexpectedly installed';
  end if;
end $$;
reset role;
-- Subsequent DB-owner setup calls simulate the server's service_role JWT.
select set_config('request.jwt.claim.role','service_role',true);
rollback;
\echo 'PASS: cross-shop read/write, owner forgery, viewer escalation, revocation and anon-denial RLS tests'


-- The ordered Feature #2 migration is automatically applied by local Supabase;
-- exercise its tenant-RLS and service-only invariants after foundational tests.
\i tests/security/feature2_trends_negative.sql
