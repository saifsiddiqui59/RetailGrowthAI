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

## F4-02 — 28 October: strict approved storyboard-to-render translation

`video-engine/feature4_intent_compiler.py` now translates a `rg_video_v2` browser draft into the *existing* `creative_reel_v1` backend contract from a trusted immutable Feature2 approval snapshot. It refuses unreviewed offers/headlines/CTA, cross-shop or unlicensed Feature3 posters and Feature5 clips, claimed browser-provided origin/type, bad timing/format and unapproved beats. Only server-reviewed media IDs are included in the returned bundle. It reuses `feature4_worker_handoff._bundle` to enforce **the same actual Supabase private-bucket/rights/MIME/path validations used at worker claim time**. `tests/media/test_feature4_intent_compiler.py` covers combined F3 + F5, idempotent lineage, approved 60s still-only export and malicious inputs.

Coordinator's one atomic `create_feature4_intent` must supply frozen `snapshot` with shop, campaign, job, approved Feature2 script/brand, current reviewed media DB rows and idempotency key; call compiler *inside that transaction*, persist `result["bundle"]` and only then make existing usage reservation/outbox. This changes no HTTP route, DB migration or Azure runtime and **does not certify realistic AI motion**.

## F4-15 — executing an approved Feature #7 edit decision (source-only)

`video-engine/feature4_edit_execution.py` exposes `draft_fingerprint(draft)` and `execute_approved_edit(draft, snapshot, approved_edits)`. This is an additive **private integration adapter**; it does not alter the existing public API, DB shape, queue, browser UI, worker, or `creative_reel_v1` schema. Its tested source-scene order/timing/approved transition edits are lowered through the exact existing `feature4_intent_compiler.compile_approved_storyboard` and `creative_contract.render_inputs` pipeline, so the HyperFrames scene list receives the reviewed edits.

**Required coordinator transaction (NOT currently implemented):**

1. After cryptographic JWT/RLS and write-membership verification, load the approved `rg_video_v2` draft, immutable Feature #2 copy/offer/CTA snapshot, approved media rows, and **server-persisted** Feature #7 edit decision. Do not take `approved_edits` from an HTTP body or accept a browser approval flag.
2. Bind the persisted edited decision to the original draft SHA-256, `shop_id`, `campaign_id`, `approval_id`, and `creative_reel_v1` review version. Never let the LLM produce raw HTML, shell, FFmpeg filters, storage paths, JWT claims or rights attestation.
3. Call `execute_approved_edit` inside the coordinator's frozen approval/intent transaction, then persist the returned `bundle` and lineage in the existing one-charge outbox/lease flow. Recheck media rights/reviews at worker claim; reject stale/revoked approvals instead of silently recalculating or billing a new intent.
4. The bounded Feature #7 instruction set only permutes existing approved source scenes, retimes to exactly 15/30/60 seconds, selects approved transition/animation primitives, and trims/mutes existing authorized clips. It **cannot** introduce new media, rewrite copy, alter product identity, change the output profile, infer a model from a still, or independently verify the real clip's quality.
5. Keep the existing browser/HTTP v2 feature flag OFF until coordinator-owned backend migrations, private Node/Chromium packaging, live tenant-negative acceptance, and genuine product-motion visual review pass. Feature #7 must separately provide **actual** multimodal understanding and approved shot-selection inference; this adapter is deterministic execution only.

Offline evidence: `tests/media/test_feature4_edit_execution.py` covers positive timeline lowering plus stale/cross-shop/unreviewed edit rejection and denial of forbidden fields, unsafe transitions, forged media and marketing claims. Only the **exact-head** CI after the new commits can certify these tests; previous 4/4 evidence refers to the predecessor code.

## F4-08 / F4-12 — GitHub CPU benchmark integration (no Azure resource)

The existing `video-engine/hyperframes/ci-smoke.sh` will now run the same actual 30s Full-HD producer export under `benchmark_render.py` on Linux GitHub Actions, observing wall seconds, process-group/descendant sampled RSS, sampled CPU tick lower bound, processes and output bytes. It writes JSON evidence to the existing `ffmpeg-smoke` artifact. The wrapper preserves the existing 420s Node limit, runs **one** real Full-HD encode, and leaves separate ffprobe H264/AAC/format and visual quality checks intact. Sampling is never a deterministic memory ceiling; hosted Azure cold-start, Node/Chromium packaging and resource quota require separate coordinator review and benchmarks. It cannot attest quality of model movement or exact embroidered clothing.

A CI-generated npm lockfile for producer 0.8.185 is available in `ffmpeg-smoke` under `feature4-review-package-lock.json` from #40669534025, but still requires an owned reviewed source commit and subsequent `npm ci` qualification before package reproducibility can be marked complete. The lock includes 138 packages and SRI integrity hashes; licensing of actual distributed FFmpeg and npm transitive notices must still be checked. Feature #4 never provisions new Azure storage, alters coordinator runtime or deploys V2 to PROD.

## F4-08 benchmark observed resources (GitHub, not Azure)

GitHub Actions #40671108819 passed 4/4 and 114 media unit tests. Full-HD 30s synthetic HyperFrames execution on 4 visible runner CPUs took 119.612 seconds, sampled 1,790,390,272 process-tree RSS bytes (about 1.67 GiB) across 580 samples, with sampled CPU-time lower bound 182.09 seconds and up to 8 observed processes. These are bounded **GitHub CI** measurements, not Azure Flex billing, hosted cold starts, memory guarantee or a sizing decision. Do **not** provision a larger Azure plan solely from this observation. Coordinator must benchmark package/browser/host under approved DEV constraints before enabling live v2.

## Optional F4-08 deployment qualification prerequisite

Before adding a production Node/Chromium sidecar or worker, compare the real deployed image against the offline `qualify_runtime.py` checks: Node >=22.12.0, pinned HyperFrames producer 0.8.185, actual executable Puppeteer Headless Shell, working FFmpeg/FFprobe and observed cgroup memory ceiling. These checks must be run **inside the intended Azure worker**, not simply on GitHub. Reported GitHub resource measurements and any sample license status are not transferable to Azure. The script itself has no tenant/media network calls and produces only a local diagnostic JSON.

## Verified F4-08 source/runtime checkpoint — 28 October 2026

The latest exact code-head [Actions #40672638751](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40672638751) passed all four jobs and **117 media tests**. Its offline local runtime preflight validated Node **22.23.3**, minimum **22.12.0**, HyperFrames producer **0.8.185**, executable Chrome Headless Shell and available FFmpeg/FFprobe. The Full-HD 30s synthetic CPU render took **135.280 seconds**, reported **1,769,979,904 bytes peak sampled process RSS**, and passed final H.264/AAC 1080×1920 24fps checks. GitHub synthetic CPU is NOT an Azure sizing/cost result; 2GB memory is a potential risk to benchmark, not a guaranteed fit or an instruction to pay for more capacity.

The separate [#40671875262](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40671875262) passed **115 media tests** with a real negative H.264/AAC **yuv444p** output rejected by the Python final-output verifier; current code retains that independent defense. Source-only PR #322 stays draft. No public API, Azure, schema, feature team, WineShopPOS or production changes. The code does not generate a photorealistic wearer or execute AI shot understanding.

## F4-12 dependency freeze / commercial notice gate

The owner-scope new lock guard pins the complete npm v3 transitive graph by prior CI-verified **SHA-256** before executing install scripts. It limits 138 entries, origin to `registry.npmjs.org` HTTPS + integrity checks, locks HyperFrames producer 0.8.185 and Puppeteer 25.16.0, and uses `npm ci` for the render smoke. It is an interim safeguard while the source branch still has **no committed standard `package-lock.json`**; producing one in a developer workspace and committing it remains a separate step. The guard's local JSON report includes unresolved notices and explicitly returns `legal_signoff_for_commercial_saas=false`. Six HyperFrames package lock records omit license metadata; upstream repository LICENSE is Apache-2.0 but release-specific notices must be validated. Several Sharp/libvips platform variants declare LGPL and FFmpeg/Chromium licensing must be independently considered before packaging a commercial runtime. No Azure hosting, generated retailer media or publication is approved.

## 2026-10-28 — F4-12 frozen dependency CI PASS

[CI #40676843934](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40676843934) is 4/4 SUCCESS on exact F4-12 source commit `34ef8af7`: **121 media tests**, fresh temporary lock resolves to the archived **69,904-byte SHA256-pinned** npm v3 tree, strict pre-install SHA check then real `npm ci`, Chromium launch and actual Full-HD 30s output 5,449,687 bytes H.264/AAC at 24fps. Sampled HyperFrames CPU wall 142.501s / RSS 1,773,772,800 bytes on GitHub runner. This is *not* an Azure Functions result.

See [THIRD_PARTY_LICENSE_REVIEW.md](hyperframes/THIRD_PARTY_LICENSE_REVIEW.md) for explicit missing metadata, LGPL/libvips, Chrome and FFmpeg binary obligations. The standard uncompressed Git-tracked `package-lock.json`, production SBOM and commercial counsel/review still need coordinator qualification before deployment. Avoid false claims that the source-only CI has commercially cleared runtime/media.

## Feature4 Timeline Studio real source-adoption handoff

See [feature-local adoption map](FEATURE4_TIMELINE_STUDIO_ADOPTION.md). This source-only P0 integration imports MIT-pinned upstream editing behavior, not its independent hosted/local cloud or browser renderer. It reuses existing React/Vite private-media preview and `rg_video_v2` server-approval contract, keeping HyperFrames/FFmpeg single renderer and default disabled v2 network transport. Feature2 owns approved creative content; Feature4 cannot alter detailed motion briefs, copy, script or offers. New `feature4_motion_handoff.py` creates source-only proposed F2→F5 commands and requires existing coordinator atomic reservation/tenant private image grants; no paid actual inference. Coordinator still owns the final F2 `creative_direction_v1` cross-team schema, F5 Wan contract, source grant, v2 HTTP/DB queue and real Azure browser acceptance.

## Additive voiceover assembly contract — review-only, 2026-10-28
The Feature4 private builder now accepts **optional** `voiceover_asset_id` (null or absent preserves old drafts). Coordinator should store a reviewed tenant-approved `audio` row and server-authorized `voiceover_source` (currently retailer/stock provenance) along with the frozen Feature2 package before accepting any browser intent. The existing `_bundle` validates private scoped rights/media type; `professional.validate` ffprobes real duration and refuses shortened recordings; the single HyperFrames renderer handles narration with deterministic music ducking. No public HTTP, DB/enum, billing API or queue contract changes are claimed. Feature2 must eventually provide an approved voice receipt with lineage and accurate captions; Feature4 does not synthesize TTS. This is a proposed additive Feature4 interface pending coordinator review and real-voice acceptance, not a deployed production contract.

## 2026-10-28 — F4-25 ACTUAL EDITOR→ENCODED VIDEO VERIFIED (offline, original fixtures)
- Source head `2dc971bbe97b7258e7175b0e835bfbf99a97b74b` verified [push CI #40725721193](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40725721193) and independent [PR CI #40725731267](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40725731267), **4/4 SUCCESS each**. Branch recorded **54 Playwright** and **139 media** tests; PR media run recorded 307 tests due to independently changing other test suites. Both passed their actual audio/video/codec and tenant isolation jobs; no bypass, paid inference, Azure deployment or public endpoints.
- New `video-engine/demo_feature4_edited_reel.py` invokes the **actual borrowed JS Timeline Studio** operations (split original video at +4sec, reorder four resulting scenes) via `tests/media/test_feature4_editor_to_render_contract.py`. Its output is accepted by `compile_approved_storyboard`, `creative_reel_v1`/private-manifest rights checks and the **same existing HyperFrames compositor**. Mock F3 kurti image/poster and F5 moving human are generated with deterministic original illustrated fixture media and a **clearly disclosed repeated 8→10sec** synthetic walking clip. It preserves two source-video in-points (0/4 seconds), exactly one approved 2-second scene SFX, source authorization, CTA and `20% OFF`, and fails closed if HyperFrames HTML loses these attributes.
- `ci-smoke.sh` now **actually encodes a second 30-second MP4** based on that edited timeline (540×960, 24fps, H.264/AAC, 2,382,922 bytes); ffprobe and 2/15/26s visual frames are archived. Separate existing source benchmark still exports genuine Full-HD synthetic 30s 1080×1920/24fps H.264/AAC MP4 (5,450,263 bytes) and proves 863Hz narrator test tone survives AAC at 13s/27s. The previous handoff was only source/plan parity; this demonstrates **real edited-frame/video export** for the supported subset without a second renderer.
- **Manual visual QA:** frames demonstrate changing illustrated garment/motion/poster scenes and an exact `20% OFF` plus approved store CTA. Not photoreal (faceless vector-style garment fixture) and not human approval. `commercial_fashion_realism_accepted=False`, `real_ai_motion=False`, `spoken_word_qa_accepted=False` remain explicit. No rights/voice/garment fidelity claim can be inferred from synthetic assets.
- **F4-12 reproducibility confirmed**: the *actual Git-tracked* 69,904-byte HyperFrames npm v3 lock hash `2b4016fde9514ac2771660a3a1e81389ee3b1237c72db6acfa1fc540494948a6` passed before direct `npm ci` in both latest exact-head runs (no install-time lock generation). Full library/Chromium/FFmpeg/libvips redistribution-license signoff, Azure Node/Chromium RAM/cold-start and commercial asset licenses still unresolved.
- **Clear scope boundary:** This validates F4-25 mock **edit→approved source staging→30s MP4 export** for currently supported commands. It does not establish full upstream `Timeline.jsx`/advanced PreviewStage, word-level captions and intelligible spoken narration, genuinely approved Feature3 garment + Feature5 AI motion, Azure HTTP #249 reliability, coordinator JWT/RLS/claim/usage/outbox integration or authenticated hosted retailer E2E. Keep PR #322 DRAFT and main untouched; coordinator owns shared docs.

## 2026-10-28 — F4-26/27 exact-code-head verified, offline readiness (NO production release)
- At source commit `bc1a63412b3871e0c7db4c7a43bebdf2aadebe3a`, [GitHub PR CI #40728552814](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40728552814) PASSED **all 4 jobs**: Python, isolated Supabase, Frontend/**97 Playwright tests**, FFmpeg/**307 media tests**. The original 30s Full-HD synthetic Reel passed H.264/AAC verification (1080×1920, 24fps, 5,449,447 bytes) and the **actually edited** 30s 540×960 synthetic Reel passed H.264/AAC verification (2,392,330 bytes). The lockfile was Git-tracked and exact SHA-256 checked before direct `npm ci`. The branch-push equivalent [#40728539257](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40728539257) must be independently observed before claiming a second green run.
- **F4-26 visual compositor bug CLOSED for video-led openings**: previously a 44%-width root `hero-logo` covered the actor face in the actual editor-driven first scene. `professional.py` now shows that giant logo ONLY for text/brand-only intros while retaining a small corner logo on all compositions. The actual edited mock project fails compilation if the big logo appears over a video-led scene or the small brand logo disappears. Reviewed 2s updated MP4 frame shows unobscured stylized model and corner branding. Text-only intro fixture still retains hero logo.
- **F4-27 stale signed-preview bug CLOSED in tested UI**: `VideoStudio.jsx` now displays a completed private MP4 as the CURRENT composition only when its draft remains in the submitted state; editing/retiming/source switching invalidates current-display status instead of silently replaying an older signed result. Playwright exercises prior job vs new submission vs changed timeline draft. Backend job snapshot/tenant authorization remains independently authoritative; no new public endpoint.
- This establishes **Feature4 offline source/editor/mock-render acceptance for the supported subset** and a genuine inspected video artifact, NOT the full professional product definition. Original MIT Timeline Studio full application/advanced PreviewStage tools are not completely adopted. User-specific garment detail, authentic human motion from Feature5, spoken real-voice subtitle sync, live JWT/RLS claim/quota/outbox, issue #249 HTTP reliability, third-party commercial licenses, signed-in hosted DEV E2E, and final commercial human visual signoff remain **OPEN**. The illustrated media and test sine-wave narration are explicitly synthetic and do not meet professional retailer quality. Do not enable paid GPU/cloud deployment, merge or declare production-ready.


## 2026-10-29 — Coordinator packaging fix proposal for PR #322 merged CI (task 22)

**Verified merged-base failure:** PR Python/uv job #123425652275 in run
#40867400353 fails four infra tests at `scripts/deploy/package.py:134`
with `ValueError: Duplicate or excessive ZIP members`. The validator rightly
rejects more than 120 entries; it must **not** be disabled or blindly raised.
Current `source_files()` collects every `video-engine/*.py`, as well as
`poster-engine/*.py`, `campaign-api/*.py` and agent runtime files. The
current main root `video-engine` has **4** Python files while Feature4 adds
**27** QA/editor/fixture/export scripts, many intentionally not used by the
running Functions host. Blind globs add test/dev machinery to the production
package, producing ~126 total merged ZIP members, even though branch-only CI
is green. This package failure is independent of the five-point pixel QA.

**Checked current main runtime import roots:**
- `azure-functions/campaign-api/render_worker.py` imports `render` from
  `video-engine` (via its private `VIDEO_DIR` sys.path), not Feature4's
  Timeline Studio/HyperFrames preview modules.
- `video-engine/render.py` imports `probe.verify_reel` and
  `asset_preflight.preflight_assets`.
- A coordinator-reviewed allowlist for the *existing v1 render worker*
  therefore begins with `video-engine/render.py`, `probe.py` and
  `asset_preflight.py`. Do **not** infer poster-engine closure from this
  observation; the coordinator must run full static+runtime import closure for
  ALL live workers before changing `source_files()`.
- `video-engine/generate_test_assets.py`, `feature4_stock_showcase.py`,
  reviewer-only `feature4_review_contact_sheet.py`, synthetic QA scripts
  and demo files are not production runtime modules of the **existing v1**
  Function and should not be included by a wildcard solely to placate tests.
- No assertion is made that a future v2 HyperFrames worker can run with only
  these 3 files; it requires separate reviewed Node22/Chromium/FFmpeg packaging
  and the worker dispatcher/queue/RLS integration.

**Acceptance for coordinator**: runtime-only deterministic manifest, explicit
missing-required-module negative tests, reject any unexpected source inclusion,
retain ZIP size/member + Linux ELF/license + lease/rollback guards, rerun
exact PR merge four-job CI then fresh postmerge main. Feature4 branch **does
not edit** coordinator-owned `scripts/deploy/**`, workflows, Supabase, Azure,
shared docs or force-merge PR #322.
