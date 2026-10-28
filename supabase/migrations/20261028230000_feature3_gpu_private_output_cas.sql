-- Feature #3 generated PNG output: strict one-shot private Storage/DB registration.
-- SOURCE ONLY. DO NOT APPLY HOSTED DEV WITHOUT SEPARATE REVIEW/APPROVAL.
-- Existing FLUX worker, unpaid default-off budget, one-shot job and ledger are unchanged.
begin;

-- Original tenant Storage policy allowed an OWNER/EDITOR to fabricate, overwrite
-- or delete objects in the reserved generated namespace. Restrictive policies
-- keep normal tenant upload/model paths unchanged but protect this namespace.
create policy feature3_generated_private_insert_only_service
on storage.objects as restrictive for insert to authenticated
with check (not (
  bucket_id='retailgrowth-media'
  and name ~ '^[0-9a-f-]{36}/feature3/gpu/'
));
create policy feature3_generated_private_update_only_service
on storage.objects as restrictive for update to authenticated
using (not (bucket_id='retailgrowth-media'
  and name ~ '^[0-9a-f-]{36}/feature3/gpu/'))
with check (not (bucket_id='retailgrowth-media'
  and name ~ '^[0-9a-f-]{36}/feature3/gpu/'));
create policy feature3_generated_private_delete_only_service
on storage.objects as restrictive for delete to authenticated
using (not (bucket_id='retailgrowth-media'
  and name ~ '^[0-9a-f-]{36}/feature3/gpu/'));

-- Service-only, immutable generated image provenance. media_assets has no
-- SHA/status columns, so never pretend it independently attests actual bytes.
create table retail_private.feature3_gpu_output_evidence (
  job_id uuid primary key references public.feature3_gpu_jobs(id),
  shop_id uuid not null references public.shops(id),
  media_asset_id uuid not null unique,
  claim_token uuid not null,
  attempt integer not null check(attempt=1),
  image_sha256 text not null check(image_sha256 ~ '^[a-f0-9]{64}$'),
  object_path text not null unique,
  object_bytes bigint not null check(object_bytes between 100 and 26214400),
  source_asset_ids uuid[] not null check(cardinality(source_asset_ids) between 1 and 12),
  review_status text not null default 'UNREVIEWED'
    check(review_status='UNREVIEWED'),
  created_at timestamptz not null default now(),
  foreign key(shop_id,media_asset_id) references public.media_assets(shop_id,id),
  foreign key(shop_id,job_id) references public.feature3_gpu_jobs(shop_id,id),
  check (object_path=shop_id::text||'/feature3/gpu/'||job_id::text||'/'||image_sha256||'.png')
);
alter table retail_private.feature3_gpu_output_evidence enable row level security;
revoke all on retail_private.feature3_gpu_output_evidence from public,anon,authenticated;
grant select on retail_private.feature3_gpu_output_evidence to service_role;
-- Only SECURITY DEFINER RPC owner inserts; service users cannot rewrite evidence.

create function public.feature3_commit_gpu_private_output(
 p_shop_id uuid, p_job_id uuid, p_attempt integer, p_claim_token uuid,
 p_object_path text, p_image_sha256 text, p_object_bytes bigint,
 p_source_asset_ids uuid[]
) returns jsonb language plpgsql security definer set search_path='' as $$
declare
 j public.feature3_gpu_jobs%rowtype;
 d public.feature3_poster_designs%rowtype;
 obj storage.objects%rowtype;
 actor_active boolean;
 missing_count integer;
 source_count integer;
 media_id uuid;
 reserved public.shop_ai_spend_reservations%rowtype;
 begin_guard boolean;
begin
 if (select auth.role()) is distinct from 'service_role' then
   raise exception 'Service-only generated image receipt' using errcode='42501';
 end if;
 if p_shop_id is null or p_job_id is null or p_claim_token is null
    or p_attempt is distinct from 1
    or p_image_sha256 is null or p_image_sha256 !~ '^[a-f0-9]{64}$'
    or p_object_bytes is null or p_object_bytes not between 100 and 26214400
    or p_object_path is null or p_object_path <>
       p_shop_id::text||'/feature3/gpu/'||p_job_id::text||'/'||p_image_sha256||'.png'
    or p_source_asset_ids is null or cardinality(p_source_asset_ids) not between 1 and 12
    or array_position(p_source_asset_ids,null) is not null
    or (select count(distinct id) from unnest(p_source_asset_ids) as t(id))
        <> cardinality(p_source_asset_ids)
 then return null; end if;

 -- The *existing* SQL queue claim is one-shot and requires a SENT outbox.
 select * into j from public.feature3_gpu_jobs
 where id=p_job_id and shop_id=p_shop_id for update;
 if not found or j.status <> 'RUNNING' or j.attempts <> 1
   or j.claim_token is distinct from p_claim_token or j.lease_until is null
   or now() >= j.lease_until or j.output_asset_id is not null
   or exists(select 1 from retail_private.feature3_gpu_output_evidence
       where job_id=p_job_id) then return null; end if;

 -- Still reserved and *current* author entitled. Revocation stops publishing
 -- the output even if worker previously measured a paid inference.
 select * into reserved from public.shop_ai_spend_reservations
 where id=j.reservation_id and shop_id=j.shop_id for update;
 if not found or reserved.state <> 'RESERVED'
    or reserved.operation <> 'image_generation' then return null; end if;
 select exists(select 1 from public.shop_memberships m
   where m.shop_id=j.shop_id and m.user_id=j.requested_by and m.active
     and m.role in ('OWNER','EDITOR')) into actor_active;
 if actor_active is not true then return null; end if;
 if not exists(select 1 from public.shop_subscriptions s
    where s.shop_id=j.shop_id and s.status in ('TRIAL','ACTIVE')
      and now()>=s.valid_from and now()<s.valid_until
      and now()>=s.period_start and now()<s.period_end) then return null; end if;
 select * into d from public.feature3_poster_designs
  where id=j.design_id and shop_id=j.shop_id for share;
 if not found or d.status<>'DRAFT'
    or d.revision<>j.design_revision
    or d.server_document_sha256<>j.design_server_sha256 then return null; end if;

 -- The trusted worker has already inspected actual source pixels and current
 -- per-image commercial rights. DB still checks original same-shop registered
 -- media, nonempty metadata and approved model state where applicable.
 select count(*) into source_count from public.media_assets a
 where a.shop_id=j.shop_id and a.id=any(p_source_asset_ids)
   and a.storage_bucket='retailgrowth-media'
   and a.mime_type in ('image/png','image/jpeg','image/webp')
   and a.source in ('UPLOAD','GENERATED')
   and a.license_name in ('owned','cc0','royalty_free','commercial')
   and length(trim(coalesce(a.attribution,'')))>=10
   and (a.license_name='owned' or a.license_url like 'https://%');
 if source_count<>cardinality(p_source_asset_ids) then return null; end if;
 if exists(select 1 from public.feature3_models m
  where m.owner_shop_id=j.shop_id and m.media_asset_id=any(p_source_asset_ids)
    and (m.status<>'APPROVED' or m.rights_verified is not true)) then return null; end if;

 -- Metadata cannot cryptographically verify bytes stored in Supabase:
 -- upstream trusted staged binary reader must independently SHA256 them.
 select * into obj from storage.objects
  where bucket_id='retailgrowth-media' and name=p_object_path for share;
 if not found or obj.metadata is null
    or obj.metadata->>'mimetype' <> 'image/png'
    or coalesce(obj.metadata->>'size','') !~ '^[0-9]{1,10}$'
    or (obj.metadata->>'size')::bigint <> p_object_bytes then return null; end if;

 -- Atomic uniqueness and same-tenant FKs block duplicate/foreign registrations.
 insert into public.media_assets
   (shop_id,created_by,storage_bucket,object_path,mime_type,source,
    license_name,attribution)
 values(j.shop_id,j.requested_by,'retailgrowth-media',p_object_path,
   'image/png','GENERATED',null,'Unreviewed generated image - not licensed')
 returning id into media_id;
 insert into retail_private.feature3_gpu_output_evidence
   (job_id,shop_id,media_asset_id,claim_token,attempt,image_sha256,object_path,
    object_bytes,source_asset_ids)
 values(j.id,j.shop_id,media_id,p_claim_token,1,p_image_sha256,p_object_path,
    p_object_bytes,p_source_asset_ids);
 return jsonb_build_object('media_asset_id',media_id,'shop_id',j.shop_id,
   'job_id',j.id,'claim_token',p_claim_token,'attempt',1,
   'image_sha256',p_image_sha256,'object_path',p_object_path,
   'review_status','UNREVIEWED','source','GENERATED','private',true);
end $$;
revoke all on function public.feature3_commit_gpu_private_output(
  uuid,uuid,integer,uuid,text,text,bigint,uuid[]) from public,anon,authenticated;
grant execute on function public.feature3_commit_gpu_private_output(
  uuid,uuid,integer,uuid,text,text,bigint,uuid[]) to service_role;


-- The prior feature3_finish_gpu_job RPC can finish an arbitrary registered
-- generated media row. A success must now match this exact immutable
-- output-evidence receipt, source claim token and original job identity.
create function retail_private.feature3_output_settlement_fence()
returns trigger language plpgsql security definer set search_path='' as $f3_output_guard$
begin
 if new.status='SUCCEEDED' and (
    old.status <> 'RUNNING' or old.claim_token is null
    or new.output_asset_id is null
    or not exists (
      select 1 from retail_private.feature3_gpu_output_evidence e
      where e.job_id=new.id and e.shop_id=new.shop_id
        and e.media_asset_id=new.output_asset_id
        and e.claim_token=old.claim_token and e.attempt=old.attempts
        and e.review_status='UNREVIEWED'
    )) then
    raise exception 'Unverified private GPU output settlement'
      using errcode='42501';
 end if;
 return new;
end $f3_output_guard$;
create trigger feature3_output_settlement_guard
before update on public.feature3_gpu_jobs
for each row execute function retail_private.feature3_output_settlement_fence();
revoke all on function retail_private.feature3_output_settlement_fence()
from public,anon,authenticated;

commit;
