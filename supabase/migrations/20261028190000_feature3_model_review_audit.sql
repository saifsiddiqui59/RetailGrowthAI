-- Feature3 P0: immutable, server-verified model-source evidence and signed
-- human decision ledger. SOURCE ONLY: hosted DEV/PROD NOT migrated by CI.
-- No public GPU route, social publication or WineShopPOS writes.
begin;

-- Only the trusted backend service role can insert evidence, AFTER verifying
-- the exact private image bytes, per-image license, provenance and adult origin.
-- The browser cannot create an eligible review source or impersonate a verifier.
create table retail_private.feature3_model_evidence (
  owner_shop_id uuid not null,
  model_id uuid not null,
  media_asset_id uuid not null,
  image_sha256 text not null check (image_sha256 ~ '^[0-9a-f]{64}$'),
  license_id text not null check (license_id in ('CC0-1.0','CC-BY-4.0','REVIEWED-COMMERCIAL')),
  license_evidence_sha256 text not null check (license_evidence_sha256 ~ '^[0-9a-f]{64}$'),
  source_kind text not null check (source_kind in ('opensource_render','created_ai','retailer_licensed')),
  source_uri text not null check (length(source_uri) between 12 and 1500
    and source_uri ~ '^https://[^/@?#[:space:]]+(/[^#]*)?$'),
  pose text not null check (pose in ('front','three_quarter','side','full_body','portrait')),
  synthetic_adult_verified boolean not null check (synthetic_adult_verified),
  component_rights_cleared boolean not null check (component_rights_cleared),
  commercial_reuse_approved boolean not null check (commercial_reuse_approved),
  evidence_revision integer not null default 1 check (evidence_revision = 1),
  verified_by uuid not null references auth.users(id),
  verified_at timestamptz not null default now(),
  primary key (owner_shop_id, model_id),
  foreign key (owner_shop_id,model_id)
    references public.feature3_models(owner_shop_id,model_id) on delete cascade,
  foreign key (owner_shop_id,media_asset_id)
    references public.media_assets(shop_id,id)
);
alter table retail_private.feature3_model_evidence enable row level security;
revoke all on retail_private.feature3_model_evidence from public,anon,authenticated;
grant select,insert on retail_private.feature3_model_evidence to service_role;
-- Immutable: no UPDATE/DELETE grant, even for the service role.
-- An updated license requires a separately reviewed new model identity.

create table retail_private.feature3_model_review_events (
  event_id uuid primary key default gen_random_uuid(),
  owner_shop_id uuid not null,
  model_id uuid not null,
  media_asset_id uuid not null,
  reviewer_id uuid not null references auth.users(id),
  action text not null check(action in ('APPROVE','REJECT','REVOKE')),
  from_status text not null,
  to_status text not null check(to_status in ('APPROVED','REJECTED','REVOKED')),
  previous_revision integer not null check(previous_revision >= 1),
  rights_revision integer not null check(rights_revision = previous_revision + 1),
  image_sha256 text not null check(image_sha256 ~ '^[0-9a-f]{64}$'),
  evidence_revision integer not null check(evidence_revision = 1),
  checks jsonb not null check(jsonb_typeof(checks)='object'),
  notes text not null check(length(trim(notes)) between 12 and 500
    and notes !~ '[[:cntrl:]]'),
  happened_at timestamptz not null default now(),
  foreign key(owner_shop_id,model_id)
    references public.feature3_models(owner_shop_id,model_id) on delete cascade,
  foreign key(owner_shop_id,media_asset_id)
    references public.media_assets(shop_id,id),
  unique(owner_shop_id,model_id,rights_revision)
);
create index feature3_review_event_owner
on retail_private.feature3_model_review_events(owner_shop_id,model_id,happened_at desc);
alter table retail_private.feature3_model_review_events enable row level security;
revoke all on retail_private.feature3_model_review_events from public,anon,authenticated;
grant select on retail_private.feature3_model_review_events to service_role;
-- SECURITY DEFINER below is sole event writer. No direct table mutation rights.

-- Signed, CURRENT reviewer principal: auth.uid comes from verified PostgREST
-- JWT, not a caller-supplied actor UUID or self-asserted browser role.
create function retail_private.feature3_can_review(p_shop uuid,p_actor uuid)
returns boolean language sql stable security definer set search_path='' as $$
  select p_actor is not null and
   (select auth.uid())=p_actor and
   (select auth.role())='authenticated' and
   exists(select 1 from public.shop_memberships m
     where m.shop_id=p_shop and m.user_id=p_actor
       and m.active and m.role in ('OWNER','EDITOR'))
$$;
revoke all on function retail_private.feature3_can_review(uuid,uuid)
  from public,anon,authenticated;

-- Approval/rejection: one locked model + evidence + media, one audit insert and
-- one status transition. User can attest 6 checks, but cannot forge the
-- independently licensed/verifier-proven private evidence row.
create function public.feature3_review_model(
  p_shop_id uuid,p_model_id uuid,p_decision text,
  p_expected_revision integer,p_expected_image_sha256 text,
  p_expected_evidence_revision integer,p_checks jsonb,p_notes text
) returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare
  actor uuid := (select auth.uid());
  m public.feature3_models%rowtype;
  e retail_private.feature3_model_evidence%rowtype;
  a public.media_assets%rowtype;
  target text;
  event_id uuid;
  required_checks text[] := array['adult_synthetic','approved_uses',
    'image_license','likeness_and_consent','private_media_integrity','visual_quality'];
  k text;
  expected_key text;
begin
  if not retail_private.feature3_can_review(p_shop_id,actor)
     or p_decision not in ('APPROVE','REJECT')
     or p_expected_revision is null or p_expected_revision < 1
     or p_expected_revision >= 2147483647
     or p_expected_image_sha256 is null
     or p_expected_image_sha256 !~ '^[0-9a-f]{64}$'
     or p_expected_evidence_revision is distinct from 1
     or p_checks is null or jsonb_typeof(p_checks) <> 'object'
     or p_notes is null or length(trim(p_notes)) not between 12 and 500
     or p_notes ~ '[[:cntrl:]]' then
    return null;
  end if;
  if (select array_agg(key order by key) from jsonb_object_keys(p_checks) as key)
      is distinct from required_checks then
    return null;
  end if;
  foreach k in array required_checks loop
    if jsonb_typeof(p_checks->k) <> 'boolean' then return null; end if;
    if p_decision='APPROVE' and p_checks->>k <> 'true' then return null; end if;
  end loop;

  select * into m from public.feature3_models
    where owner_shop_id=p_shop_id and model_id=p_model_id for update;
  if not found or m.status <> 'PENDING_REVIEW' or m.rights_verified
     or m.rights_revision <> p_expected_revision
     or m.image_sha256 <> p_expected_image_sha256
     or m.synthetic_adult is not true then return null; end if;

  -- A shared platform model requires a separate CURRENT platform curator,
  -- not the uploader/creator granting themselves a global approval.
  if m.scope='platform' and (
    actor=m.created_by or not exists(
      select 1 from retail_private.platform_admins pa
       where pa.user_id=actor and pa.active
    )) then return null; end if;

  select * into e from retail_private.feature3_model_evidence
   where owner_shop_id=p_shop_id and model_id=p_model_id for share;
  if not found or e.media_asset_id <> m.media_asset_id
     or e.image_sha256 <> m.image_sha256
     or e.license_id <> m.license_id
     or e.license_evidence_sha256 <> m.license_evidence_sha256
     or e.source_kind <> m.source_kind
     or e.evidence_revision <> p_expected_evidence_revision
     or not (e.synthetic_adult_verified and e.component_rights_cleared
             and e.commercial_reuse_approved) then return null; end if;

  select * into a from public.media_assets
   where shop_id=p_shop_id and id=m.media_asset_id for share;
  expected_key := p_shop_id::text || '/model-library/' ||
    case when m.scope='platform' then 'platform/' else '' end ||
    p_model_id::text || '/' || m.image_sha256 || '.png';
  if not found or a.storage_bucket <> 'retailgrowth-media'
     or a.object_path <> expected_key or a.mime_type <> 'image/png'
     or a.source not in ('UPLOAD','GENERATED')
     or a.license_name not in ('owned','cc0','commercial','royalty_free')
     or length(trim(coalesce(a.attribution,''))) < 10
     or (a.license_name <> 'owned' and
         (a.license_url is null or a.license_url not like 'https://%'))
     or (m.license_id='CC-BY-4.0' and length(trim(m.attribution))=0)
     then return null; end if;

  target := case when p_decision='APPROVE' then 'APPROVED' else 'REJECTED' end;
  insert into retail_private.feature3_model_review_events(
    owner_shop_id,model_id,media_asset_id,reviewer_id,
    action,from_status,to_status,previous_revision,rights_revision,
    image_sha256,evidence_revision,checks,notes)
  values(p_shop_id,p_model_id,m.media_asset_id,actor,p_decision,
    m.status,target,m.rights_revision,m.rights_revision+1,
    m.image_sha256,e.evidence_revision,p_checks,trim(p_notes))
  returning feature3_model_review_events.event_id into event_id;

  update public.feature3_models set status=target,
    rights_verified=(target='APPROVED'),rights_revision=m.rights_revision+1,
    updated_at=now()
   where owner_shop_id=p_shop_id and model_id=p_model_id
     and rights_revision=m.rights_revision and status='PENDING_REVIEW';
  if not found then raise exception 'MODEL_REVIEW_CAS_LOST' using errcode='40001'; end if;

  return jsonb_build_object('model_id',p_model_id,'owner_shop_id',p_shop_id,
    'status',target,'rights_verified',target='APPROVED',
    'rights_revision',m.rights_revision+1,'review_event_id',event_id,
    'audit_persisted',true);
end
$$;
revoke all on function public.feature3_review_model(uuid,uuid,text,integer,text,integer,jsonb,text)
  from public,anon,authenticated;
grant execute on function public.feature3_review_model(uuid,uuid,text,integer,text,integer,jsonb,text)
  to authenticated;

-- Emergency withdrawal is allowed even if source licensing has expired;
-- only CURRENT signed shop OWNER/EDITOR, still-approved state and exact
-- revision/hash can revoke; no reapproval path exists for revoked records.
create function public.feature3_revoke_model(
 p_shop_id uuid,p_model_id uuid,p_expected_revision integer,
 p_expected_image_sha256 text,p_reason text
) returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare actor uuid := (select auth.uid());
 m public.feature3_models%rowtype;
 e retail_private.feature3_model_evidence%rowtype;
 event_id uuid;
begin
 if not retail_private.feature3_can_review(p_shop_id,actor)
    or p_expected_revision is null or p_expected_revision < 1
    or p_expected_revision >= 2147483647
    or p_expected_image_sha256 is null
    or p_expected_image_sha256 !~ '^[0-9a-f]{64}$'
    or p_reason is null or length(trim(p_reason)) not between 12 and 500
    or p_reason ~ '[[:cntrl:]]' then return null; end if;
 select * into m from public.feature3_models
   where owner_shop_id=p_shop_id and model_id=p_model_id for update;
 if not found or m.status <> 'APPROVED' or not m.rights_verified
    or m.rights_revision <> p_expected_revision
    or m.image_sha256 <> p_expected_image_sha256 then return null; end if;
 select * into e from retail_private.feature3_model_evidence
  where owner_shop_id=p_shop_id and model_id=p_model_id;
 -- No current commercial rights required to record an urgent withdrawal.
 insert into retail_private.feature3_model_review_events(
   owner_shop_id,model_id,media_asset_id,reviewer_id,action,
   from_status,to_status,previous_revision,rights_revision,
   image_sha256,evidence_revision,checks,notes)
 values(p_shop_id,p_model_id,m.media_asset_id,actor,'REVOKE',
   'APPROVED','REVOKED',m.rights_revision,m.rights_revision+1,
   m.image_sha256,coalesce(e.evidence_revision,1),'{}'::jsonb,trim(p_reason))
 returning feature3_model_review_events.event_id into event_id;
 update public.feature3_models set status='REVOKED',rights_verified=false,
  rights_revision=m.rights_revision+1,updated_at=now()
  where owner_shop_id=p_shop_id and model_id=p_model_id
    and rights_revision=m.rights_revision and status='APPROVED';
 if not found then raise exception 'MODEL_REVOKE_CAS_LOST' using errcode='40001'; end if;
 return jsonb_build_object('model_id',p_model_id,'owner_shop_id',p_shop_id,
  'status','REVOKED','rights_verified',false,
  'rights_revision',m.rights_revision+1,'review_event_id',event_id,
  'audit_persisted',true);
end
$$;
revoke all on function public.feature3_revoke_model(uuid,uuid,integer,text,text)
 from public,anon,authenticated;
grant execute on function public.feature3_revoke_model(uuid,uuid,integer,text,text)
 to authenticated;


-- Guard against ANY old service-role code path bypassing human review by
-- directly PATCHing model flags. All approval transitions require an event
-- just inserted by the signed RPC in the same transaction.
create function retail_private.feature3_guard_reviewed_model()
returns trigger language plpgsql security definer set search_path='' as $$
begin
  if tg_op = 'INSERT' then
    if new.status <> 'PENDING_REVIEW' or new.rights_verified or new.rights_revision <> 1
    then raise exception 'MODEL_MUST_START_PENDING' using errcode='42501'; end if;
    return new;
  end if;
  if (new.owner_shop_id,new.model_id,new.media_asset_id,new.created_by,
      new.scope,new.source_kind,new.image_sha256,new.license_id,
      new.license_evidence_sha256,new.synthetic_adult,new.approved_uses,
      new.attribution) is distinct from
     (old.owner_shop_id,old.model_id,old.media_asset_id,old.created_by,
      old.scope,old.source_kind,old.image_sha256,old.license_id,
      old.license_evidence_sha256,old.synthetic_adult,old.approved_uses,
      old.attribution) then
    raise exception 'MODEL_SOURCE_IMMUTABLE' using errcode='42501';
  end if;
  if (new.status,new.rights_verified,new.rights_revision)
      is distinct from (old.status,old.rights_verified,old.rights_revision) then
    if new.rights_revision <> old.rights_revision + 1 or
       not exists(select 1 from retail_private.feature3_model_review_events ev
        where ev.owner_shop_id=old.owner_shop_id and ev.model_id=old.model_id
          and ev.media_asset_id=old.media_asset_id
          and ev.previous_revision=old.rights_revision
          and ev.rights_revision=new.rights_revision
          and ev.from_status=old.status and ev.to_status=new.status
          and ev.image_sha256=old.image_sha256
          and ((ev.action='APPROVE' and new.status='APPROVED' and new.rights_verified)
            or (ev.action='REJECT' and new.status='REJECTED' and not new.rights_verified)
            or (ev.action='REVOKE' and new.status='REVOKED' and not new.rights_verified)))
    then raise exception 'MODEL_REVIEW_EVENT_REQUIRED' using errcode='42501'; end if;
  end if;
  return new;
end
$$;
revoke all on function retail_private.feature3_guard_reviewed_model()
 from public,anon,authenticated;
create trigger feature3_model_rights_guard
before insert or update on public.feature3_models
for each row execute function retail_private.feature3_guard_reviewed_model();

commit;
