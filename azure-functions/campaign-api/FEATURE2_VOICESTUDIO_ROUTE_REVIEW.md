# Feature2 VoiceStudio root Azure Function route — independent review REQUIRED

**Source only; NOT deployed or enabled.** This stacked change adds one protected root Functions route,
`POST /api/shops/{shop_id}/voicestudio-jobs`, using the existing `VoiceStudioSignedAPI`
and the existing Supabase JWT verifier + `TenantStore.member(write=True)` on each
request. Body accepts only trusted resource references
`{campaign_id,request_id}`. Actor is always derived from the JWT; voice,
language, script, commercial model, claim and media path come solely from
server-side current approved SQL plan/asset readers.

The route builds lazily and returns HTTP 503 unless **both**
`RETAIL_VOICESTUDIO_HTTP_ENABLED=true` and
`RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED=true`, all private
backend credentials, and a 64-character exact model license-evidence digest
are configured. A flag/digest is **not sufficient legal authorization by
itself**. The SQL RPC must independently check an actual approved model
revision, signed owner/editor, approved script, current membership and
original-key lease; default OmniVoice CC-BY-NC weights remain OFF.

Imports are lazy to avoid loading model or starting workers on Azure host
indexing. No new billing, public signed audio, auto-publish, file download,
GPU or model activation occurs in this source PR. The call is synchronous;
the current PostgREST job claim blocks duplicate uncertain retries, but a
durable queue/outbox is preferable before production because proxy timeouts
can outlive the request. Neither the four RPCs (review-only PR #923)
nor the human plan approval writer are deployed yet.

This PR changes protected root `function_app.py`, so per
`docs/FEATURE_SELF_MERGE_POLICY_20261031.md`, obtain independent review
of all JWT/RLS, activation flags, provider network and async timeout gates
before merging/DEV deployment. Do not bypass by green CI alone. No
WineShopPOS changes.

Tests: `tests/api/test_feature2_voicestudio_route_review.py` loads
the exact Azure function definitions in isolation, proves default OFF,
incomplete/forged flags DENIED, no model initialization or provider egress,
and boundary status/error hygiene. Hosted two-shop tests require real
DEV auth/migrations/approved commercial model; source tests are not those.
