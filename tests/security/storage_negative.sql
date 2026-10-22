-- Dedicated RetailGrowthAI disposable-test transaction. No files are actually uploaded.
-- Direct storage.objects rows are synthetic, always rolled back at end.
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('11111111-1111-4111-8111-111111111111','00000000-0000-0000-0000-000000000000','authenticated','authenticated','media-a@example.invalid','!',now(),now()),
('22222222-2222-4222-8222-222222222222','00000000-0000-0000-0000-000000000000','authenticated','authenticated','media-b@example.invalid','!',now(),now()),
('33333333-3333-4333-8333-333333333333','00000000-0000-0000-0000-000000000000','authenticated','authenticated','media-viewer@example.invalid','!',now(),now());
set local role authenticated;
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
insert into public.shops (id,owner_user_id,name,slug) values
('44444444-4444-4444-8444-444444444444','11111111-1111-4111-8111-111111111111','Media shop A','rg-media-tenant-a');
insert into public.shop_memberships(shop_id,user_id,role) values
('44444444-4444-4444-8444-444444444444','33333333-3333-4333-8333-333333333333','VIEWER');

insert into storage.objects(bucket_id,name)
values('retailgrowth-media','44444444-4444-4444-8444-444444444444/a.png');

select set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true);
insert into public.shops (id,owner_user_id,name,slug) values
('55555555-5555-4555-8555-555555555555','22222222-2222-4222-8222-222222222222','Media shop B','rg-media-tenant-b');
insert into storage.objects(bucket_id,name)
values('retailgrowth-media','55555555-5555-4555-8555-555555555555/b.png');
do $$
declare denied boolean := false; rows_changed integer;
begin
  if exists (select 1 from storage.objects
   where bucket_id='retailgrowth-media'
     and name='44444444-4444-4444-8444-444444444444/a.png')
  then raise exception 'FAIL: cross-tenant private media read'; end if;
  begin
    insert into storage.objects(bucket_id,name)
    values('retailgrowth-media','44444444-4444-4444-8444-444444444444/forged.png');
  exception when insufficient_privilege then denied := true;
  end;
  if not denied then raise exception 'FAIL: wrong tenant media upload'; end if;

  update storage.objects set name='44444444-4444-4444-8444-444444444444/renamed.png'
  where bucket_id='retailgrowth-media'
    and name='55555555-5555-4555-8555-555555555555/b.png';
  get diagnostics rows_changed = row_count;
  -- Either zero rows (no update permissions) or an RLS error is a denial;
  -- explicit exceptions are checked below in an update-specific block.
  if rows_changed > 0 then raise exception 'FAIL: media moved to wrong tenant'; end if;
end $$;

select set_config('request.jwt.claim.sub','33333333-3333-4333-8333-333333333333',true);
do $$
declare denied boolean := false;
begin
  if not exists (select 1 from storage.objects
    where bucket_id='retailgrowth-media'
      and name='44444444-4444-4444-8444-444444444444/a.png')
  then raise exception 'FAIL: viewer cannot read authorized media'; end if;
  begin
    insert into storage.objects(bucket_id,name)
    values('retailgrowth-media','44444444-4444-4444-8444-444444444444/viewer.png');
  exception when insufficient_privilege then denied := true;
  end;
  if not denied then raise exception 'FAIL: viewer could upload media'; end if;
end $$;
reset role;
rollback;
