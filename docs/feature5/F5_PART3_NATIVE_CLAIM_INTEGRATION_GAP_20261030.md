# Feature5 ↔ Part3 original source compatibility gate (GPU OFF)

Verified date: 2026-10-30. This is a **source review** of Part3's existing **draft** PR #125 at `3d985127e495d839e3e1f657080cbd8885561e6e`, checked against Feature5 consolidated PR #781 at `18cbc016b0a2914c886e75328366d46f85901901`. **No runtime/GPU, provider charge, hosted claim or database SQL test is asserted.**

## Actual incompatible original code, not an assumed missing integration

| Dimension | Part3 PR #125 actual source | Feature5 native contract | Result |
| --- | --- | --- | --- |
| Provider | `wan2.7-i2v-2026-04-25` / `wan2.7-t2v-2026-06-12` in `ai-agents/src/ai_agents/premium_video.py` and `premium_video_jobs.py` | `wan22_ti2v_5b_comfy_v1` | **DIFFERENT MODEL; never alias silently** |
| Resolution | `("720P", "1080P")` in `premium_video_jobs.py`, `premium_worker.py` and proposed SQL CHECK | Exact **704×1280** native | **NOT ACCEPTED by old API/SQL** |
| Cadence | Cloud Wan2.7 provider output 30fps (Part3 provider handoff) | **24fps × 121 frames, 5-second native clip** | **DIFFERENT** |
| Cost | Per-job Wan2.7 remote API estimate/cost cap and 720P/1080P reservation | Reviewed, separately capped Wan2.2 Comfy local GPU, native profile | **NO VALID NATIVE CREDIT RESERVATION** |
| Tenant lease and rights | Draft Part3 vendor-specific job/retry/private import scaffold | F5 `part3_native_claim_gate.verify_native_wan22_claim` requires authoritative source, tenant, attempt, reservation, rights, budget; two fresh consistent reads before one POST | **No live Part3 claim reader** |
| Release integration | Part3 PR #125 remains DRAFT and GitHub reports `mergeable_state=dirty` against `main` | F5 branch #781 remains ready for source review, #465 parent draft | **Two distinct integration gates remain** |

Relevant original paths: `ai-agents/src/ai_agents/premium_video.py`, `azure-functions/campaign-api/premium_video_jobs.py`, `azure-functions/campaign-api/premium_worker.py`, `azure-functions/campaign-api/part3_sql/PROPOSED_20261023180000_premium_video_reservations.sql`; comparison path `feature5_motion/part3_native_claim_gate.py`. The Part3 proposed SQL was **not applied** to hosted DEV/PROD, and should not be treated as existing hosted authorization.

## Exact owning dependency / required deliverable

**Part3/Coordinator owns F5-06 through F5-12 external dependencies.** Their accepted output must be **new versioned service-only NativeWan22 reservation and claim**, not translation of an old Wan2.7 authorization. Required fields, already validated by Feature5 source:

```json
{
  "schema": "retailgrowth.part3-f5-native-lease-claim.v1",
  "shop_id": "<canonical UUID>",
  "job_id": "<canonical UUID>",
  "attempt_token": "<canonical UUID>",
  "source_asset_id": "<canonical UUID>",
  "campaign_id": "<original Creative Director campaign ID>",
  "scene_id": "<original scene ID>",
  "shot_id": "<original shot ID>",
  "provider": "wan22_ti2v_5b_comfy_v1",
  "mode": "image_to_video",
  "native_width": 704, "native_height": 1280,
  "fps": 24, "frames": 121, "duration_seconds": 5,
  "prompt_sha256": "<approved original prompt SHA256>",
  "lineage_sha256": "<verified same-shop original lineage SHA256>",
  "credit_reservation_id": "<canonical UUID>",
  "reserved_max_usd": 2.0,
  "lease_valid": true,
  "source_rights_current": true,
  "budget_authorized": true
}
```

**All example values are CONTRACT SHAPE ONLY**, not a real approved claim or suggested spend. This is the existing F5 adapter schema; actual reservation cost and consent must be independently approved; never hardcode the example amount or grant flags. Never treat a user-provided JSON document as an authoritative claim. Part3's trusted server must derive these from same-shop tenant/RLS, durable compare-and-swap lease, current signed F3 rights and actual reserved credit; deny browser forgery, missing rights, foreign tenant/attempt, stale claim, unknown provider and release paths. Unknown provider POST results require independent non-retrying reconciliation. F5 tests must be rerun against authentic Part3 service output after coordinator integration.

## Actions to unblock (minimal-cost)

1. **Coordinator/Part3 lead:** reconcile PR #125's merge conflict on latest main without disabling current Wan2.7 source or touching PROD; create/review a **separate versioned Wan2.2 provider/profile and corresponding reserved-credit/claim API**, not an alias. Own schema migration review, with no hosted execution before approval.
2. **Feature3 owner:** supply signed current same-shop commercial/likeness/garment permissions and tenant-private pinned source asset bytes separately. Synthetic fixtures aren't original approved garments.
3. **Feature5/Coordinator:** wire the original new claim reader into existing F5 one-shot local Comfy dispatcher and current first-frame resolver; verify strict two-read snapshot and all negative lease/cost tests. **No A100/GPU, model download or paid submission** until separately authorised.
4. **CI owner:** call `python3 -m feature5_motion.ci_native_media` in existing FFmpeg CI job; previous PR #781 4/4 standard CI did **not** execute the three actual video-intake tests (Python 12 skipped).
5. Only after source integration and a **fresh main 4/4** plus explicit owner spending/licensing approvals may a separately gated real test be proposed. No automatic merge into main here.

Original F5 22-item **integrated DONE 0 / IN PROGRESS 3 / BLOCKED 19** is unchanged. This is evidence/coordination only, no completed dependency or production access. WineShopPOS untouched.
