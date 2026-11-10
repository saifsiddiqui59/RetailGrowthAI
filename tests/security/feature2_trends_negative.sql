-- Isolated Supabase CI only. Never run against hosted or production databases.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,created_at,updated_at)
values
('fa000000-0000-4000-8000-000000000001','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f2a@example.invalid','!',now(),now()),
('fa000000-0000-4000-8000-000000000002','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f2b@example.invalid','!',now(),now()),
('fa000000-0000-4000-8000-000000000003','00000000-0000-0000-0000-000000000000','authenticated','authenticated','f2c@example.invalid','!',now(),now());
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','fa000000-0000-4000-8000-000000000001',true);
insert into public.shops(id,owner_user_id,name,slug)
values('fb000000-0000-4000-8000-000000000001','fa000000-0000-4000-8000-000000000001','Trend A','f2-trend-a');
insert into public.shop_memberships(shop_id,user_id,role)
values('fb000000-0000-4000-8000-000000000001','fa000000-0000-4000-8000-000000000003','VIEWER');
-- Only the trusted backend can insert: direct authenticated inserts are forbidden.
reset role;
insert into public.shop_content_drafts(shop_id,created_by,trend_id,content)
values('fb000000-0000-4000-8000-000000000001',
       'fa000000-0000-4000-8000-000000000001',
       'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
       '{"campaign":{"shop_id":"fb000000-0000-4000-8000-000000000001"},"content_days":[{"trend_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}],"review":{"status":"DRAFT","can_publish":false}}');
set local role authenticated;
select set_config('request.jwt.claim.role','authenticated',true);
select set_config('request.jwt.claim.sub','fa000000-0000-4000-8000-000000000001',true);
do $$
declare denied boolean := false;
begin
  if (select count(*) from public.shop_content_drafts
      where shop_id='fb000000-0000-4000-8000-000000000001')<>1
  then raise exception 'FAIL: owner cannot read own Feature2 draft'; end if;
  begin
    execute 'select * from public.trend_snapshots limit 1';
  exception when insufficient_privilege then denied := true; end;
  if not denied then raise exception 'FAIL: shared snapshot exposed to browser roles'; end if;
  denied := false;
  begin
    insert into public.shop_content_drafts(shop_id,created_by,trend_id,content)
    values('fb000000-0000-4000-8000-000000000001',
           'fa000000-0000-4000-8000-000000000001',
           'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
           '{"campaign":{"shop_id":"fb000000-0000-4000-8000-000000000001"},"content_days":[{"trend_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}],"review":{"status":"DRAFT","can_publish":false}}');
  exception when insufficient_privilege then denied := true; end;
  if not denied then raise exception 'FAIL: owner bypassed evidence-verifying backend'; end if;
  denied := false;
  begin
    perform public.feature2_claim_collection('IN',current_date);
  exception when insufficient_privilege then denied := true; end;
  if not denied then raise exception 'FAIL: collector claim RPC publicly executable'; end if;
end $$;

select set_config('request.jwt.claim.sub','fa000000-0000-4000-8000-000000000002',true);
insert into public.shops(id,owner_user_id,name,slug)
values('fb000000-0000-4000-8000-000000000002','fa000000-0000-4000-8000-000000000002','Trend B','f2-trend-b');
do $$
declare denied boolean := false;
begin
  if exists(select 1 from public.shop_content_drafts where shop_id='fb000000-0000-4000-8000-000000000001')
  then raise exception 'FAIL: foreign Feature2 draft leaked'; end if;
  begin
    insert into public.shop_content_drafts(shop_id,created_by,trend_id,content)
    values('fb000000-0000-4000-8000-000000000001',
           'fa000000-0000-4000-8000-000000000002',
           'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
           '{"campaign":{"shop_id":"fb000000-0000-4000-8000-000000000001"},"content_days":[{"trend_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}],"review":{"status":"DRAFT","can_publish":false}}');
  exception when insufficient_privilege then denied := true; end;
  if not denied then raise exception 'FAIL: forged shop content INSERT accepted'; end if;
end $$;

select set_config('request.jwt.claim.sub','fa000000-0000-4000-8000-000000000003',true);
do $$
declare denied boolean := false;
begin
  if not exists (select 1 from public.shop_content_drafts
                 where shop_id='fb000000-0000-4000-8000-000000000001')
  then raise exception 'FAIL: viewer cannot read own shop draft'; end if;
  begin
    insert into public.shop_content_drafts(shop_id,created_by,trend_id,content)
    values('fb000000-0000-4000-8000-000000000001',
           'fa000000-0000-4000-8000-000000000003',
           'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
           '{"campaign":{"shop_id":"fb000000-0000-4000-8000-000000000001"},"content_days":[{"trend_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}],"review":{"status":"DRAFT","can_publish":false}}');
  exception when insufficient_privilege then denied := true; end;
  if not denied then raise exception 'FAIL: viewer inserted content draft'; end if;
end $$;
reset role;
rollback;
\echo 'PASS: Feature2 global snapshot private, claim service-only, draft RLS cross-shop and viewer denial'
