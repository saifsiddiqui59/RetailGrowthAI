# Feature #4 — additive Azure/Private Media worker handoff

**Status:** source-only adapter, NOT deployed. This document is owned by Feature #4. Canonical `docs/**`, RLS migrations, queue bindings, public APIs and React app routing remain coordinator-owned.

## Existing verified system we must preserve

- `azure-functions/campaign-api/render_api.py`: JWT-scoped member/rights checks, idempotent `instagram_reel_30s` queue request and RLS-limited GET/signed download.
- `azure-functions/campaign-api/render_worker.py`: service-role claim, server-side reread, tenant-private Storage download, FFmpeg fallback, lease-token-suffixed Storage upload and `admin.complete_render`.
- `azure-functions/campaign-api/private_media.py`: one existing `retailgrowth-media` private bucket, canonical tenant paths and no-overwrite uploads. Its current input limit is 25 MiB **per object**.
- `video-engine/feature4_worker_handoff.py`: new **separate** trusted renderer dispatch target for a future coordinator-approved versioned v2 preset, without changing those v1 modules.

**Do not** switch an old v1 render job over to Feature #4 or reinterpret its existing image-only storyboard as a new creative contract. The `feature4_reel_v1` preset, its persisted approved source records, and the atomic RPCs below are NOT in the current DB API. Feature #4 cannot claim hosted readiness until the coordinator provides them.

## Proposed minimal dispatcher extension (not committed to coordinator files)

Use the **existing** `retail-reel-render` trigger and `job_outbox.kind = 'render'`. Reuse the existing job ID / quota reservation; no new Azure queue or billing ledger. On the trusted queue side:

```python
# Coordinator illustrative code only -- NOT a current runnable Azure route
if job["preset"] == "instagram_reel_30s":
    return existing_process_render(job["id"], admin, media)  # unchanged FFmpeg
if job["preset"] == "feature4_reel_v1" and flags.feature4_v2_enabled_for_shop(job["shop_id"]):
    return process_feature4_render(job["id"], admin, media)
raise UnsupportedJobPreset()
```

Never route based on a browser-provided `mode` or unauthenticated raw request. The public POST, status GET and download still go through cryptographically verified JWT and server-side tenant membership. If the coordinator cannot add a versioned preset without breaking v1, keep Feature #4 disabled.

## Required transactional backend methods (coordinator implementation)

| Feature4 service callback | Atomic invariant |
| --- | --- |
| `render_status(id)` | Existing v1-compatible status, called before attempting a claim |
| `claim_feature4_render(id)` | Claim only v2 preset, lock with UUID lease/fencing token; preserve immutable `shop_id`, `campaign_id`, `idempotency_key`; reject stale/unauthorized concurrent claims |
| `render_authorized(claim)` | Re-read membership, subscription, approved script, approved media and quotas; explicitly return boolean `True` only if currently eligible |
| `load_feature4_bundle(claim)` | Fetch approved Feature #2 script, Feature #3/5 media and optional Feature #7 edit-plan with verified DB provenance; never load client manifest; bind script version, rights and final offer to immutable job |
| `feature4_claim_current(claim)` | Recheck same live lease token and review rights after CPU encode and before private upload |
| `complete_feature4_render(claim,key,probe,rendered_as)` | One compare-and-set transaction by same lease token: check auth and job status, register private `video/mp4` media, mark SUCCEEDED, finalize one existing usage reservation, persist actual rendered type; return `False` on stale attempt |
| `render_failure(claim,code,permanent=False)` | Existing claim-fenced failure/recovery rules; bounded retries for transient errors; permanent rejection must not retry/bill |

The `feature4_reel_v1` row must additionally record the exact approved creative request hash and server-verified media IDs. The original `render_jobs` table constraint accepts only legacy presets today; migration belongs to coordinator. **No second usage reservation on retries**. If a lease is lost between blob upload and finalize, the token-prefixed blob remains private orphan data for lifecycle reconciliation, not a signed customer download.

## Private source record contract

Backend emits exactly the approved media used by the `creative_reel_v1` request. Each authoritative asset record contains `shop_id, kind, source_feature, approved, storage_bucket, object_path, mime_type, license_name, rights_evidence, rights_source`. This is **service-created data**, never a customer-signed rights assertion. The worker rejects cross-shop objects, unapproved model/media, source-kind mismatches, unrelated extras, wrong MIME, missing rights, untrusted paths and unrecognized licenses. Generated staging names are enumerated, not copied from Storage keys.

The existing private Storage helper enforces per-input byte size (25 MiB) and upload (80 MiB). The worker adds a 36-asset and 300 MiB aggregate staging limit. Feature #5 clips exceeding those bounds must be downsampled/transcoded in a separately authorized trusted staging service—not by loosening the request security boundary. No real retailer media is stored in the public repo or CI artifacts.

## CPU / Azure operational gates

- The current Python-only Azure Functions zip does not establish Node >= 22, supported Chromium/headless-shell dependencies, or CPU/RAM for HyperFrames. Package as an independently benchmarked **private, no-egress** media runtime *only after coordinator rollout approval* and preserve the existing FFmpeg worker fallback.
- Render behind an idempotent queue attempt with hard process-group kill, lease renewals coordinated with the existing claim-fencing logic, at-most-one active job per conservative worker instance, accurate RSS/CPU/disk/time observations, and a cost ceiling. The HyperFrames local adapter bounds its subprocess to <=780 seconds, but staging/download/upload also consume time; the coordinator must set an appropriate Azure trigger timeout and claim renewal plan.
- No GPU needed for Feature #4 assembly. **Feature #5 actual model inference** is separate, default-off and subject to licenses/pricing and approved caps.
- External HTTP gateway issue #249 remains separate; a good queue-render MP4 does not prove authenticated HTTP upload/download is reliable.

## Current test matrix (source-only)

`tests/media/test_feature4_worker_handoff.py` mocks the existing admin/Storage interfaces and covers: one successful fenced finalize, no duplicate upload after final, existing job busy, revoked rights, concurrent stale lease, failed CAS, wrong job IDs/campaign/shop, forged idempotency, cross-shop private paths, invalid licenses/MIME, foreign source provenance, extra unapproved media, wrong renderer output, and unapproved Feature #2 scripts.

Real all-up acceptance still needs: reviewed coordinator migration/API implementation; authenticated DEV queue E2E; tests for expired JWT/cross-shop, quota and one-charge semantics; signed 15/30/60s private downloads; actual source media and photorealistic motion approval; full memory and cost benchmark. Until then **this module is a secure additive integration seam, not a deployed Azure worker**.

## Integration fixture mode (owner decision 2026-10-28)

The owner permitted Feature #4 to continue **as though upstream assets were delivered** for contract testing. This permits local mock source rows for Feature #3 `image/poster` and Feature #5 `video`, but **does not create real approved DB media records** or authorize deploying their synthetic fixture to customers. Source-only tests verify that true Feature #5 clip status `ready` is required for an `AUTHORIZED_ASSEMBLY`; fallback `IMAGE_ANIMATION_FALLBACK` is permanently distinct and can only occur with explicit `allow_image_fallback=True`. The worker compares both `rendered_as` and the full `fallback_events` lineage with the pre-render authorization snapshot before private upload. Production human-model realism remains an owner visual acceptance gate.

## Browser/HTTP integration handoff — 2026-10-28

The feature-owned `frontend/src/features/video/VideoStudioConnected.jsx` and `video-transport.mjs` prepare a **real authenticated browser transport** but remain disabled unless coordinator explicitly supplies `enabled=true` plus v2 route builders and reviewed per-shop props. Do **not** call the old v1 `POST /campaigns/{campaign_id}/renders`: it expects `day_id` and `instagram_reel_30s`, not a v2 plan. Suggested additive routing shape for coordinator review only:

- `POST /api/campaigns/{campaign_id}/creative-renders`: accept `{shop_id,campaign_id,approval_id,draft}` as **untrusted intent**; JWT/RLS membership + plan/version/licensing/copy/retailer approval are checked again using DB media and **server-minted** immutable `creative_reel_v1` request; creates one claim-fenced existing-ledger reservation; respond HTTP 202 `{shop_id,job_id,status:'QUEUED'}`.
- `GET /api/creative-render-jobs/{job_id}`: JWT/RLS-scope existing job status and return `{shop_id,job_id,status}` with `QUEUED|RUNNING|SUCCEEDED|FAILED`; never enumerate other shops.
- `GET /api/creative-render-jobs/{job_id}/download`: JWT/RLS scope SUCCEEDED job then issue short-lived signed HTTPS URL under existing private `retailgrowth-media/{shop_id}/renders/{job_id}/{lease_token}.mp4`. Return `{shop_id,job_id,url}`; never return the service-role token or an external video URL.

Client needs a current JWT for each request; does not automatically replay POST after Azure issue #249 timeouts; polls only GET, shop/job validates every response, clears stale signed URLs on shop/account changes. Client checks are defense-in-depth **not** a substitute for server JWT, RLS and compare-and-set quota. Coordinator owns actual HTTP routes and migrations, feature owns only integration code/tests/documentation. Default-off until deployment and release gates.

## Feature-owned drop-in API class for coordinator review

`video-engine/feature4_http_handoff.py` implements the three methods matching the UI's v2 request/response JSON without touching live routes. The coordinator can import `Feature4HTTP` in its authenticated router **after** the existing verifier returns a JWT-scoped user ID, and only with the new transactional `admin.create_feature4_intent` and RLS `user_store.feature4_job` backing calls implemented. `create` checks RLS campaign/shop ownership and write membership, rejects foreign draft shop IDs, derives a stable idempotency hash and passes the untrusted draft into a **server-enforced immutable approved-data snapshot transaction**. `get` verifies read membership and returns the selected shop/job only. `download` requires SUCCEEDED job, same-shop `video/mp4` private asset and exact `{shop}/renders/{job}/{lease}.mp4` path before using the existing JWT-signed Storage service. Neither the source adapter nor UI performs quota charges, queue provisioning, JWT verification, or production media upload themselves. Tests: `tests/media/test_feature4_http_handoff.py`. Backend implementation, DB transaction, Azure routing and runtime remain coordinator-owned and pending.
