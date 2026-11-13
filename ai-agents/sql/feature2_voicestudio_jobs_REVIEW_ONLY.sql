-- Feature2 / VoiceStudio ORIGINAL-KEY private speech review RPCs.
-- SECURITY/INTEGRATION REVIEW ONLY: NOT APPLIED TO DEV OR PROD.
-- Supersedes the old Kokoro-specific unmerged Feature2 private voice SQL
-- proposal in PR #848. Do not apply both schemas independently.
-- Inspected actual RetailGrowthAI DEV schema on 2026-11-11:
-- campaigns status {PLANNING,DRAFT,READY,FAILED}, membership roles
-- {OWNER,EDITOR,VIEWER}, private retailgrowth-media bucket. All RPCs are
-- SECURITY INVOKER, explicitly granted ONLY to service_role; backend MUST
-- derive p_actor_id from a verified JWT and never from client JSON.
-- Model/voice rights cannot be certified by simply executing this script.
-- No live migration, direct authenticated mutation, public signed media, or
-- inference/provider code is activated here.
BEGIN;

-- Operator-only, revision-specific commercial model clearance: no seeded review rows.
CREATE TABLE public.feature2_voicestudio_model_reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upstream_source_commit text NOT NULL CHECK (upstream_source_commit ~ '^[0-9a-f]{40}$'),
  model_id text NOT NULL CHECK (model_id ~ '^[A-Za-z0-9_./-]{2,200}$'),
  model_revision text NOT NULL CHECK (length(model_revision) BETWEEN 8 AND 200),
  weights_license text NOT NULL CHECK (length(weights_license) BETWEEN 2 AND 120),
  rights_evidence_sha256 text NOT NULL CHECK (rights_evidence_sha256 ~ '^[0-9a-f]{64}$'),
  weights_commercial_allowed boolean NOT NULL DEFAULT false,
  tokenizer_commercial_allowed boolean NOT NULL DEFAULT false,
  dependencies_commercial_allowed boolean NOT NULL DEFAULT false,
  agpl_compliance_reviewed boolean NOT NULL DEFAULT false,
  reviewed_by uuid NOT NULL, reviewed_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  CONSTRAINT feature2_voice_complete_model_clearance CHECK (
    weights_commercial_allowed AND tokenizer_commercial_allowed
    AND dependencies_commercial_allowed AND agpl_compliance_reviewed
  )
);
ALTER TABLE public.feature2_voicestudio_model_reviews ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.feature2_voicestudio_model_reviews FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON public.feature2_voicestudio_model_reviews TO service_role;
-- The database owner must separately insert reviewed, licensed evidence.

CREATE TABLE public.feature2_voicestudio_plans (
  shop_id uuid NOT NULL REFERENCES public.shops(id),
  campaign_id uuid NOT NULL REFERENCES public.campaigns(id),
  plan_sha256 text NOT NULL CHECK (plan_sha256 ~ '^[0-9a-f]{64}$'),
  voiceover_script text NOT NULL
    CHECK (length(btrim(voiceover_script)) BETWEEN 1 AND 3000),
  voice text NOT NULL CHECK (voice ~ '^[A-Za-z0-9_.-]{1,64}$'),
  duration_seconds integer NOT NULL CHECK (duration_seconds IN (15,30,60)),
  review_state text NOT NULL DEFAULT 'DRAFT'
    CHECK (review_state IN ('DRAFT','APPROVED_FOR_NARRATION')),
  reviewed_actor_id uuid,
  reviewed_at timestamptz,
  source_review_receipt_id uuid,
  -- An independent operator/legal workflow must populate this field and
  -- verify the exact model revision, tokenizers/components and speaker rights.
  commercial_model_review_id uuid REFERENCES public.feature2_voicestudio_model_reviews(id),
  commercial_rights_confirmed boolean NOT NULL DEFAULT false,
  revoked_at timestamptz,
  revision bigint NOT NULL DEFAULT 0 CHECK (revision >= 0),
  PRIMARY KEY (shop_id,campaign_id),
  CONSTRAINT feature2_voice_real_review CHECK (
    review_state <> 'APPROVED_FOR_NARRATION'
    OR (reviewed_actor_id IS NOT NULL AND reviewed_at IS NOT NULL
        AND source_review_receipt_id IS NOT NULL
        AND commercial_model_review_id IS NOT NULL
        AND commercial_rights_confirmed IS TRUE
        AND revoked_at IS NULL)
  )
);

CREATE TABLE public.feature2_voicestudio_jobs (
  shop_id uuid NOT NULL REFERENCES public.shops(id),
  campaign_id uuid NOT NULL REFERENCES public.campaigns(id),
  request_id uuid NOT NULL,
  actor_id uuid NOT NULL,
  plan_sha256 text NOT NULL CHECK (plan_sha256 ~ '^[0-9a-f]{64}$'),
  audio_asset_id uuid NOT NULL DEFAULT gen_random_uuid(),
  state text NOT NULL DEFAULT 'CLAIMED_ONCE'
    CHECK (state IN ('CLAIMED_ONCE','REGISTERED_PRIVATE_NEEDS_REVIEW','REVOKED')),
  original_object_key text,
  render_object_key text,
  original_sha256 text CHECK (original_sha256 IS NULL OR original_sha256 ~ '^[0-9a-f]{64}$'),
  render_sha256 text CHECK (render_sha256 IS NULL OR render_sha256 ~ '^[0-9a-f]{64}$'),
  original_bytes integer,
  render_bytes integer,
  claimed_at timestamptz NOT NULL DEFAULT now(),
  claim_expires_at timestamptz NOT NULL DEFAULT (now() + interval '25 minutes'),
  registered_at timestamptz,
  revoked_at timestamptz,
  PRIMARY KEY (shop_id,campaign_id,request_id),
  UNIQUE (audio_asset_id),
  CONSTRAINT feature2_voice_private_media_review CHECK (
    state <> 'REGISTERED_PRIVATE_NEEDS_REVIEW'
    OR (original_object_key =
          shop_id::text||'/voicestudio/'||campaign_id::text||'/'||
          request_id::text||'/original.wav'
        AND render_object_key =
          shop_id::text||'/voicestudio/'||campaign_id::text||'/'||
          request_id::text||'/render.wav'
        AND original_sha256 ~ '^[0-9a-f]{64}$'
        AND render_sha256 ~ '^[0-9a-f]{64}$'
        AND original_bytes BETWEEN 44 AND 8388608
        AND render_bytes BETWEEN 44 AND 8388608
        AND registered_at IS NOT NULL
        AND revoked_at IS NULL)
  )
);
CREATE INDEX feature2_voice_job_asset_lookup
  ON public.feature2_voicestudio_jobs(shop_id,campaign_id,audio_asset_id);

ALTER TABLE public.feature2_voicestudio_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feature2_voicestudio_jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.feature2_voicestudio_plans, public.feature2_voicestudio_jobs
  FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.feature2_voicestudio_plans TO authenticated;
GRANT SELECT, INSERT, UPDATE ON
  public.feature2_voicestudio_plans, public.feature2_voicestudio_jobs
  TO service_role;
-- Authenticated editors see only their own non-revoked plan. Jobs remain
-- service-only and are never exposed as direct Data API rows.
CREATE POLICY feature2_voice_editor_read
  ON public.feature2_voicestudio_plans
  FOR SELECT TO authenticated USING (
    revoked_at IS NULL
    AND (SELECT auth.uid()) IS NOT NULL
    AND EXISTS (
      SELECT 1 FROM public.shop_memberships m
      WHERE m.shop_id=feature2_voicestudio_plans.shop_id
        AND m.user_id=(SELECT auth.uid())
        AND m.active IS TRUE
        AND m.role IN ('OWNER','EDITOR')
    )
  );

-- SECURITY INVOKER + service_role EXECUTE only; no public definer escalation.
-- The central worker authenticates a JWT and supplies its verified actor_id.
-- Every RPC independently rechecks active editor role and campaign shop.
CREATE FUNCTION public.feature2_voicestudio_plan(
  p_actor_id uuid, p_shop_id uuid, p_campaign_id uuid
) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=''
AS $$
DECLARE v public.feature2_voicestudio_plans%ROWTYPE;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.shop_memberships m
    WHERE m.user_id=p_actor_id AND m.shop_id=p_shop_id
      AND m.active IS TRUE AND m.role IN ('OWNER','EDITOR')
  ) OR NOT EXISTS (
    SELECT 1 FROM public.campaigns c
    WHERE c.id=p_campaign_id AND c.shop_id=p_shop_id
      AND c.status IN ('DRAFT','READY')
  ) THEN
    RAISE EXCEPTION 'Current signed editor/campaign required'
      USING errcode='42501';
  END IF;
  SELECT * INTO v FROM public.feature2_voicestudio_plans p
  WHERE p.shop_id=p_shop_id AND p.campaign_id=p_campaign_id
    AND p.revoked_at IS NULL AND p.review_state='APPROVED_FOR_NARRATION'
    AND p.commercial_rights_confirmed IS TRUE
    AND p.commercial_model_review_id IS NOT NULL
      AND EXISTS (
        SELECT 1 FROM public.feature2_voicestudio_model_reviews lic
        WHERE lic.id=p.commercial_model_review_id AND lic.revoked_at IS NULL
          AND lic.weights_commercial_allowed IS TRUE
          AND lic.tokenizer_commercial_allowed IS TRUE
          AND lic.dependencies_commercial_allowed IS TRUE
          AND lic.agpl_compliance_reviewed IS TRUE
      )
    AND p.source_review_receipt_id IS NOT NULL;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Approved private plan unavailable' USING errcode='42501';
  END IF;
  RETURN jsonb_build_object(
    'shop_id',v.shop_id,'campaign_id',v.campaign_id,
    'voiceover_script',v.voiceover_script,'plan_sha256',v.plan_sha256,
    'voice',v.voice,'duration_seconds',v.duration_seconds,
    'script_review','APPROVED_FOR_NARRATION',
    'active_editor',true,'can_publish',false
  );
END; $$;
REVOKE ALL ON FUNCTION public.feature2_voicestudio_plan(uuid,uuid,uuid)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.feature2_voicestudio_plan(uuid,uuid,uuid)
  TO service_role;

CREATE FUNCTION public.feature2_voicestudio_claim(
  p_actor_id uuid,p_shop_id uuid,p_campaign_id uuid,p_request_id uuid,
  p_plan_sha256 text
) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=''
AS $$
DECLARE v public.feature2_voicestudio_jobs%ROWTYPE;
BEGIN
  -- CURRENT signed editor, exact user-approved plan and campaign match.
  IF NOT EXISTS (
    SELECT 1 FROM public.shop_memberships m
    WHERE m.user_id=p_actor_id AND m.shop_id=p_shop_id
      AND m.active IS TRUE AND m.role IN ('OWNER','EDITOR')
  ) OR NOT EXISTS (
    SELECT 1 FROM public.campaigns c
    WHERE c.id=p_campaign_id AND c.shop_id=p_shop_id
      AND c.status IN ('DRAFT','READY')
  ) OR NOT EXISTS (
    SELECT 1 FROM public.feature2_voicestudio_plans p
    WHERE p.shop_id=p_shop_id AND p.campaign_id=p_campaign_id
      AND p.plan_sha256=p_plan_sha256
      AND p.review_state='APPROVED_FOR_NARRATION'
      AND p.revoked_at IS NULL AND p.commercial_rights_confirmed IS TRUE
      AND p.commercial_model_review_id IS NOT NULL
      AND EXISTS (
        SELECT 1 FROM public.feature2_voicestudio_model_reviews lic
        WHERE lic.id=p.commercial_model_review_id AND lic.revoked_at IS NULL
          AND lic.weights_commercial_allowed IS TRUE
          AND lic.tokenizer_commercial_allowed IS TRUE
          AND lic.dependencies_commercial_allowed IS TRUE
          AND lic.agpl_compliance_reviewed IS TRUE
      )
  ) THEN
    RAISE EXCEPTION 'Original-key private voice claim denied'
      USING errcode='42501';
  END IF;
  IF p_plan_sha256 !~ '^[0-9a-f]{64}$'
     OR substring(p_request_id::text FROM 15 FOR 1)<>'4'
  THEN RAISE EXCEPTION 'Invalid voice job identity' USING errcode='22023';
  END IF;
  INSERT INTO public.feature2_voicestudio_jobs (
    shop_id,campaign_id,request_id,actor_id,plan_sha256
  ) VALUES (
    p_shop_id,p_campaign_id,p_request_id,p_actor_id,p_plan_sha256
  ) ON CONFLICT (shop_id,campaign_id,request_id) DO NOTHING
    RETURNING * INTO v;
  IF NOT FOUND THEN
    -- NO fresh job token is returned and caller MUST NOT replay provider.
    RAISE EXCEPTION 'Voice original-key already claimed or uncertain'
      USING errcode='23505';
  END IF;
  RETURN jsonb_build_object(
    'shop_id',v.shop_id,'campaign_id',v.campaign_id,
    'request_id',v.request_id,'plan_sha256',v.plan_sha256,
    'status','CLAIMED_ONCE','paid_inference_calls',0
  );
END; $$;
REVOKE ALL ON FUNCTION public.feature2_voicestudio_claim(uuid,uuid,uuid,uuid,text)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.feature2_voicestudio_claim(uuid,uuid,uuid,uuid,text)
  TO service_role;

CREATE FUNCTION public.feature2_voicestudio_register(
  p_actor_id uuid,p_shop_id uuid,p_campaign_id uuid,p_request_id uuid,
  p_plan_sha256 text,p_original_sha256 text,p_render_sha256 text,
  p_original_bytes integer,p_render_bytes integer
) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=''
AS $$
DECLARE v public.feature2_voicestudio_jobs%ROWTYPE;
BEGIN
  IF p_original_sha256 !~ '^[0-9a-f]{64}$'
     OR p_render_sha256 !~ '^[0-9a-f]{64}$'
     OR p_original_bytes NOT BETWEEN 44 AND 8388608
     OR p_render_bytes NOT BETWEEN 44 AND 8388608
  THEN RAISE EXCEPTION 'Unverified private WAV digest or size'
    USING errcode='22023';
  END IF;
  -- Atomic CAS: an expired/duplicate/revoked claim cannot register audio;
  -- actor and approved plan must STILL be valid at this exact transaction.
  UPDATE public.feature2_voicestudio_jobs j
  SET state='REGISTERED_PRIVATE_NEEDS_REVIEW',
      original_object_key=p_shop_id::text||'/voicestudio/'||
        p_campaign_id::text||'/'||p_request_id::text||'/original.wav',
      render_object_key=p_shop_id::text||'/voicestudio/'||
        p_campaign_id::text||'/'||p_request_id::text||'/render.wav',
      original_sha256=p_original_sha256,render_sha256=p_render_sha256,
      original_bytes=p_original_bytes,render_bytes=p_render_bytes,
      registered_at=now()
  WHERE j.shop_id=p_shop_id AND j.campaign_id=p_campaign_id
    AND j.request_id=p_request_id AND j.actor_id=p_actor_id
    AND j.plan_sha256=p_plan_sha256
    AND j.state='CLAIMED_ONCE' AND j.claim_expires_at>now()
    AND j.revoked_at IS NULL
    AND EXISTS (
      SELECT 1 FROM public.shop_memberships m
      WHERE m.user_id=p_actor_id AND m.shop_id=p_shop_id
        AND m.active IS TRUE AND m.role IN ('OWNER','EDITOR')
    )
    AND EXISTS (
      SELECT 1 FROM public.campaigns c
      WHERE c.id=p_campaign_id AND c.shop_id=p_shop_id
        AND c.status IN ('DRAFT','READY')
    )
    AND EXISTS (
      SELECT 1 FROM public.feature2_voicestudio_plans p
      WHERE p.shop_id=p_shop_id AND p.campaign_id=p_campaign_id
        AND p.plan_sha256=p_plan_sha256
        AND p.review_state='APPROVED_FOR_NARRATION'
        AND p.revoked_at IS NULL
        AND p.commercial_rights_confirmed IS TRUE
        AND p.commercial_model_review_id IS NOT NULL
      AND EXISTS (
        SELECT 1 FROM public.feature2_voicestudio_model_reviews lic
        WHERE lic.id=p.commercial_model_review_id AND lic.revoked_at IS NULL
          AND lic.weights_commercial_allowed IS TRUE
          AND lic.tokenizer_commercial_allowed IS TRUE
          AND lic.dependencies_commercial_allowed IS TRUE
          AND lic.agpl_compliance_reviewed IS TRUE
      )
    )
  RETURNING j.* INTO v;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Original-key registration/review fence denied'
      USING errcode='42501';
  END IF;
  RETURN jsonb_build_object(
    'status','REGISTERED_PRIVATE_NEEDS_REVIEW',
    'shop_id',v.shop_id,'campaign_id',v.campaign_id,
    'request_id',v.request_id,
    'original_sha256',v.original_sha256,'render_sha256',v.render_sha256,
    'publish_approved',false
  );
END; $$;
REVOKE ALL ON FUNCTION public.feature2_voicestudio_register(
  uuid,uuid,uuid,uuid,text,text,text,integer,integer
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.feature2_voicestudio_register(
  uuid,uuid,uuid,uuid,text,text,text,integer,integer
) TO service_role;

CREATE FUNCTION public.feature2_voicestudio_receipt(
  p_actor_id uuid,p_shop_id uuid,p_campaign_id uuid,p_request_id uuid
) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=''
AS $$
DECLARE v public.feature2_voicestudio_jobs%ROWTYPE;
BEGIN
  SELECT j.* INTO v FROM public.feature2_voicestudio_jobs j
  JOIN public.feature2_voicestudio_plans p ON
    p.shop_id=j.shop_id AND p.campaign_id=j.campaign_id
  WHERE j.shop_id=p_shop_id AND j.campaign_id=p_campaign_id
    AND j.request_id=p_request_id AND j.actor_id=p_actor_id
    AND j.state='REGISTERED_PRIVATE_NEEDS_REVIEW'
    AND j.revoked_at IS NULL AND p.revoked_at IS NULL
    AND j.plan_sha256=p.plan_sha256
    AND p.review_state='APPROVED_FOR_NARRATION'
    AND p.commercial_rights_confirmed IS TRUE
    AND p.commercial_model_review_id IS NOT NULL
      AND EXISTS (
        SELECT 1 FROM public.feature2_voicestudio_model_reviews lic
        WHERE lic.id=p.commercial_model_review_id AND lic.revoked_at IS NULL
          AND lic.weights_commercial_allowed IS TRUE
          AND lic.tokenizer_commercial_allowed IS TRUE
          AND lic.dependencies_commercial_allowed IS TRUE
          AND lic.agpl_compliance_reviewed IS TRUE
      )
    AND EXISTS (
      SELECT 1 FROM public.shop_memberships m
      WHERE m.shop_id=j.shop_id AND m.user_id=p_actor_id
        AND m.active IS TRUE AND m.role IN ('OWNER','EDITOR')
    )
    AND EXISTS (
      SELECT 1 FROM public.campaigns c
      WHERE c.id=j.campaign_id AND c.shop_id=j.shop_id
        AND c.status IN ('DRAFT','READY')
    );
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Private job receipt unavailable or rights revoked'
      USING errcode='42501';
  END IF;
  RETURN jsonb_build_object(
    'audio_asset_id',v.audio_asset_id,'shop_id',v.shop_id,
    'campaign_id',v.campaign_id,'request_id',v.request_id,
    'plan_sha256',v.plan_sha256,'original_sha256',v.original_sha256,
    'render_sha256',v.render_sha256,
    'private',true,'review_status','NEEDS_REVIEW',
    'commercial_rights_confirmed',true,'publish_approved',false
  );
END; $$;
REVOKE ALL ON FUNCTION public.feature2_voicestudio_receipt(uuid,uuid,uuid,uuid)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.feature2_voicestudio_receipt(uuid,uuid,uuid,uuid)
  TO service_role;
COMMIT;

-- Subsequent reviewed changes before DEV activation:
-- 1. Human-reviewed plan writer RPC with audit/provenance, actual verified
--    JWT current membership and subscription/budget, race-free revision CAS.
-- 2. Source app currently has no live F2 approved plan rows and DEV has zero
--    campaigns. No signed two-shop E2E or real model inference is possible yet.
-- 3. Actual source/WAV model/commercial speaker rights must be reviewed by
--    separate authority, then source plan revision and model evidence stored.
-- 4. A separate review step may promote the REGISTERED audio to a signed,
--    independently authorized media_assets row for Feature4, not here.
-- 5. Inspect Supabase advisors, applicable app/API authorizations, and
--    independently approve migration before DEV execution.
