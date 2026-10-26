# Feature #5 motion adapter — disabled source-only

`MotionSpec` and `AssetGrant` are authenticated **server-authoritative** contracts. Run only behind the existing Part3 approved subscription reservation / source-media RLS / ledger / outbox / lease fences. Incoming queue messages contain just the canonical job UUID. This module does not create a queue, cloud API or Supabase schema and does not modify Part3.

`HunyuanLocalRunner` is a no-download optional local official 1.5 `generate.py` adapter; requires explicitly configured preinstalled model checkout + weights + licensed GPU, `enabled=True`, `license_approved=True`, and `gpu_budget_approved=True`. Default off. A pinned model/runtime is still required before execution. No user-facing endpoint or keys here.

`MotionWorker` expects injected existing `JobStore` and `TenantMedia` adapters. The downstream collaborator MUST supply transactional atomic claim/finish/failed fencing with existing credit accounting. Generated clip is checked with local-only ffprobe and private output upload; a human must compare garment with source and approve before publishing. Feature4 remains responsible for promotions, logos, music and final Reel assembly.

Tests: `python -m pytest tests/ai/test_feature5_motion.py`. All tests are CPU-only/mocked. They do not generate real AI video.

No production use until the gates in `docs/feature5/NEXT_TASK.md` are closed.

## Security contract (2026-10-26)
- The offline Tencent CLI must omit `--image_path` for T2V; image/poster mode supplies only a decoded, bounded file inside a private job directory. Zero unapproved network model fetching.
- BF16-capable CUDA hardware and a reviewed 14 GiB minimum are required before launching; a Central India T4 alone is not verified suitable.
- `TenantMedia.upload_private` must return a verified exact, private receipt with `shop_id`, `job_id`, `attempt_token`, `bucket=retailgrowth-media`, `path={shop_id}/renders/{job_id}/{attempt_token}.mp4`, `private=True`. Receipt ambiguity remains UNKNOWN; the injected existing DB store must reconcile it without paid retry.
- Scratch image/video files are deleted after processing. Use encrypted/ephemeral private worker disks; do not log local source content, prompts, provider credentials or private URLs.
- All CLI subprocess and GPU readiness tests remain simulated. No real garment, face, movement or temporal quality has passed acceptance.

## Explicitly approved real GPU test (not part of Actions)
Run only on a preprovisioned/licensed GPU already authorized by the owner. Supply `RETAIL_FEATURE5_REAL_GPU_TEST=true`, `RETAIL_FEATURE5_GPU_COST_APPROVED=true`, `RETAIL_FEATURE5_LICENSE_APPROVED=true`, `RETAIL_FEATURE5_PINNED_CHECKOUT`, and `RETAIL_FEATURE5_PINNED_WEIGHTS`. For I2V additionally supply `RETAIL_FEATURE5_RIGHTS_APPROVED_IMAGE` after consent/rights review. Run `python -m unittest discover -s tests/gpu -p 'test_feature5_local_acceptance.py'`. The test deletes its temporary assets and never activates a hosted service. Its success only validates machine media, not visual/garment QA.

## Mandatory integration and activation details — 2026-10-26
- IMPORTANT: Part3 draft SQL only supports Wan 720P/1080P models; current `feature5_motion/interop.py` adapter is a **source contract only** and has not been wired to a live Part3 service-role RPC. Coordinator must reconcile an additive 480p model/profile, atomic subscriptions, rights and outbox first. Existing Wan implementation is untouched.
- Feature4 `feature4_asset_entry` now requires a tenant-authorized, media-hash-bound `VisualReview` (approved garment/quality/disclosure) as well as true output provenance, codec, lease and rights. Synthetic fixtures only validate code contracts; they do not certify motion.
- Logical motion reservation key `feature5-lease-v2` includes an SHA-256 of the approved prompt plus the generation seed. The canonical coordinator must persist the matching versioned key; no client-supplied hash can authorize expense.
- HunyuanLocalRunner fails closed without a reviewed `HunyuanLicensePolicy` covering deployment/retailer/intended publication territories, actual legally named service provider, AUP/notice/rights and Tencent MAU terms. This policy is not real commercial legal signoff, IP geolocation or royalty clearance.
- Separate real local GPU harness requires explicit spend permission, operator licence review, provider legal name, allowed countries, installed weights, pinned runtime and BF16-capable hardware. No GPU execution has occurred.

## Budget runtime contract (added 2026-10-26)
Even with `enabled=True`, `MotionWorker` refuses to claim/launch without a `MotionSpendGuard` based on a verified active A100/vCPU/RAM quote, allowed max billed execution seconds and ancillary cost reserve. The existing DB must already reserve at least that full worst-case quote and the runner timeout must fit. No additional ledger/table is created. `compute_seconds_measured` and `estimated_observed_compute_usd` are subprocess estimates, not paid-cloud invoice measurements. A GPU overrun or lost acknowledgment goes to UNKNOWN/reconciliation and MUST NOT automatically retry/credit/refund.

## Official pinned upstream and review-fixture workflow
The optional runner hard-codes `HunyuanVideo-1.5` upstream `generate.py` Git blob `ba18ce85661d2cc2ebfe5a7fe4ad80994899d07d` at Tencent commit `60783e704160023913bee78f0b47036d393d4dfa` and rejects altered/symlinked code before CUDA. It does **not** verify complete model weight shards or dependencies; operator must separately record immutable licensed weight revision/checksums and pin deployment artifacts. Changing upstream versions requires a reviewed source-and-model change.
`prepare_visual_review(clip, private_new_output_dir)` provides CPU-generated six-frame PNG sampling, 3×2 contact sheet and SHA256 manifest from an already validated tenant-private H.264 MP4. Existing service must authenticate tenant, provide private staging, dispose of artifacts and obtain an independently persisted human `VisualReview`; this utility never automatically passes quality or publishing approval.
`tests/ai/test_feature5_real_ffmpeg_media.py` makes **real synthetic FFmpeg clips**, verifies the exact 5s/24FPS/480p bytes and checks negative profiles. This is not AI motion, not an Azure end-to-end test and not evidence of garment fidelity.

## Complete model/weights integrity and real manual acceptance (2026-10-26)
`HunyuanLocalRunner` requires **both** official `generate.py` Git blob identity and an `ArtifactLock` for every installed runtime code file + every licensed weight file. Source tree must be a **clean materialized** copy, no `.git`, symlinks or temp cache. Reviewer generates a CANDIDATE locally, for example:

```bash
python -m feature5_motion.seal_artifacts --checkout /private/hunyuan-clean-checkout --weights /private/licensed-hunyuan-model --out /private/operator/feature5-model.lock.json
```

Operator must verify Tencent license/territories, model supplier, model revision, full shard SHA256 list, dependency versions and exact manifest, then store the candidate's SHA256 in a **separate trusted deployment configuration**. The manifest cannot approve itself. Neither generator nor verification downloads any model or starts CUDA; a model lock merely detects mutations and is not licensing proof.

Manual genuine GPU acceptance `tests/gpu/test_feature5_local_acceptance.py` now ALSO requires `RETAIL_FEATURE5_ARTIFACT_LOCK_PATH`, independently reviewed `RETAIL_FEATURE5_APPROVED_LOCK_SHA256`, and an **existing owner-controlled mode-0700** `RETAIL_FEATURE5_MANUAL_EVIDENCE_ROOT`. Preserve all previous legal/region/spend/license/rights environment gates documented above. Once a real GPU succeeds, it retains the original validated clip + source still for I2V and six-frame contact sheet + SHA256 under a new output folder. Evidence stays `PENDING_HUMAN_REVIEW` and must be checked by a real authorized reviewer before Feature4 can compose it. No customer data should be sent to an unapproved region.

## $0-first routing and unknown-billing guard (2026-10-26)
`plan_lowest_cost_delivery(requires_realistic_ai_motion=..., existing_media_approved=..., allow_paid_gpu=False, max_premium_usd="0", guard=None)` defaults to `EXISTING_FFMPEG` for already licensed still/video assets when suitable, `DEFER` for unapproved/no media/expensive photorealistic motion, and only `GPU_BUDGET_ELIGIBLE` for explicit budget, guard and a sufficient worst-case quote. It **does not invoke FFmpeg/GPU, bypass licensing, or alter Part3 quota**. Feature4 coordinator must wire the cheapest actual composition route; do not present a slideshow as an AI model walking.

`MotionWorker` now records failures prior to runner invocation as `FAILED`, and any post-runner-start exception as **`UNKNOWN`**, preventing accidental charged auto-retry or refund on CUDA timeout, invalid output or encoder failures. An UNKNOWN persistence failure raises `ReconciliationRequired`. This source contract depends on the coordinator's atomic Part3 ledger/lease/RPC to be honored in hosted DEV.

Azure documentation (2026-10-26) currently lists Central India with T4 only, not serverless A100; never silently move Indian customer media to an A100 region outside their approved scope. Tencent's 14 GiB minimum plus BF16 requirement does not validate older T4 GPU. Keep real GPU disabled until legal, rights, region, licensed pinned weights, quota, pricing, explicit budget and actual visual QA gates pass.

## Real fashion sample, authenticity, and exactly-one-GPU-attempt controls
The canonical example is `feature5_motion/demo_fashion.py` (5s 480p/24fps portrait T2V, adult fashion model in red embroidered kurti). **No MP4 has been generated yet**, because this execution environment is CPU-only and no licensed model weights are installed. The previously shown still image was generated by ChatGPT and is not a Feature5 artifact.

The existing manual CUDA harness `tests/gpu/test_feature5_local_acceptance.py` now demands `RETAIL_FEATURE5_ACCEPTANCE_MODE=text` **or** `image` (never both); `RETAIL_FEATURE5_AZURE_PRICE_SNAPSHOT` (a current reviewed official Azure Container Apps USD JSON price response), `RETAIL_FEATURE5_GPU_REGION=eastus` only with reviewed geography, `RETAIL_FEATURE5_MAX_BILLABLE_SECONDS`, and `RETAIL_FEATURE5_MAX_TOTAL_GPU_USD`. It checks an all-in A100+vCPU+RAM+ancillary worst-case quote before the CUDA/weights gate. All previous licensing/territory/model-lock/0700 evidence flags still apply. Missing or insufficient budgets fail closed. Manual GPU test always writes an independent PENDING_HUMAN_REVIEW packet, not a published Reel.

The external public `multimodalart/Hunyuan-Video-1-5` Space is an optional free **third-party** 480p I2V-distilled demo, requiring a local image upload; it is NOT our worker execution, and the tool-driven public test did NOT generate any MP4. Never substitute Tencent's stock clips, ChatGPT image, or FFmpeg still animation for a genuine Feature5 proof.
