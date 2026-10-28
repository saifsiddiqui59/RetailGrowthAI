# Feature #3 P0 — Human model review + revocation service gate (2026-10-28)

**Status:** feature-owned source + synthetic tests. Existing DEV model catalog
remains zero models, zero approved. No user-facing API, cloud writes, migrations,
GPU or actual reviewed customer imagery were made by this task.

## What is newly implemented

`poster-engine/model_review_gate_v1.py` provides
`decide_model_review` and `revoke_approved_model`, **fail-closed**:
- Reads current `public.feature3_models` fields already in real DEV:
  `owner_shop_id`, `model_id`, `created_by`, `media_asset_id`,
  `status`, `scope`, `source_kind`, `image_sha256`,
  `license_id`, `license_evidence_sha256`, `rights_verified`,
  `synthetic_adult`, `attribution`, `approved_uses`, `rights_revision`.
- Models first enter `PENDING_REVIEW`. Current human reviewer must be
  independently verified as an active signed-in same-shop OWNER or EDITOR.
  Shared platform assets additionally require an independently authorized
  curator **other than the original creator**.
- Independently verified *per-image* original HTTPS provenance, model pose,
  commercial license evidence, third-party rights, synthetic adult status and
  existing asset linkage. A code repository license is not an image license.
- Reads **actual private PNG bytes** from the exact current owner-prefixed
  `{shop}/model-library[/platform]/{model_id}/{sha256}.png`, validates the
  registered same-shop media row, PIL dimensions and SHA256 of unmodified
  bytes. No public image/object path or bytes are returned in the receipt.
- Requires six explicit booleans from an accountable human reviewer:
  synthetic adulthood, likeness/consent, image licensing, media integrity,
  visual quality and permitted usage. No missing/failed check can approve.
- Builds an immutable review proposal with current rights revision, source
  digest, reviewer identity, media UUID, evidence revision, pose and exact
  review checks. **Only** an injected `persist_review_atomic` may commit
  one authoritative DB transaction that re-checks all current facts,
  persists a durable reviewer/audit event and transitions to
  `APPROVED` or `REJECTED` while incrementing `rights_revision`.
  Uncertain results are NOT automatically replayed.
- A separate `revoke_approved_model` must use atomic current-revision CAS
  with persisted reason and event, set `REVOKED`, `rights_verified=false`,
  increment rights revision and invalidate cached downstream image use.
- Returns `gpu_authorized=false`, `generation_executed=false` regardless
  of an approved human image. This grants **no** paid FLUX or VTON inference.

The source supports the import-first library and Feature3's real catalog
fields, but **does not implement persistence, reviewer DB grants or an HTTP
route**. This division is intentional: the deployed catalog lacks durable
human-review events, per-image provenance and model-pose columns.

## Mandatory database/operator integration (coordinator P0)

1. Define a versioned, additive review evidence and review-event schema
   (or equivalent private linked records), including immutable
   `owner_shop_id/model_id/media_asset_id/image_sha256`, verified pose/source
   per exact image, evidence SHA, reviewer, decision, checks, notes, rights
   revision, audit created time and immutable evidence changes. **Do not
   expose review event writes directly to browser roles.**
2. A server-only, least-privileged DB transaction/RPC must lock model and
   current media/license rows, validate the currently signed-in actor and
   current rights, compare the expected state/revision/hash/evidence revision,
   insert the human audit event and update `feature3_models.status` and
   `rights_verified/rights_revision` atomically. Return exact new revision,
   owner, status and stored event UUID; unexpected/no ACK fails closed.
3. Verify photo/likeness commercial rights independently and attach a true
   private Storage asset/media row. Do **not** reuse an old synthetic
   Feature2 revoked test tenant or mark a fictional test human as a
   commercial advertising model.
4. Test signed OWNER/EDITOR, revoked memberships, VIEWER/anon/expired JWT,
   foreign tenants, platform curator self-approval, uncertain response,
   double approval/revoke/replay, altered PNG, license change and concurrent
   stale revisions **in disposable Supabase**, then protected legitimate DEV.
5. Integrate approved catalog into existing `Feature3V2API.models` and
   `fashion_reference_v1` only after real pose/audit/rights data is durable,
   and verify Feature2 metadata, Feature4 timeline and Feature5 private
   first-frame current-rights consumption. Do not introduce another
   renderer/wallet, and keep GPU default-off.

## Evidence and boundaries

Offline tests in `tests/media/test_feature3_model_review_gate.py` create
illustrative Pillow 720x1080 adult geometry with fake authorized reviewers,
fake independent license evidence and an in-memory CAS callback. They test
source-level denial and wire shape, NOT actual auth/database atomicity or
consent of a real human. All externally provided original image rights must
be verified separately before any commercial display. No GPU, Azure
paid action, live migration, production data, or WineShopPOS change.
