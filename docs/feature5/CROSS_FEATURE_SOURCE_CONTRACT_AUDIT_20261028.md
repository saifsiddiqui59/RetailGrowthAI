# Feature #5 — 2026-10-28 cross-feature code audit and source handoff

## Verified actual connected branches

| Source | Actual public/internal contract | Feature5 implementation | Integration status |
|---|---|---|---|
| Feature #3 / PR #561, `poster-engine/feature3_consumer_packets_v1.py` | `assemble_consumer_packets` returns `retailgrowth.feature3-offline-consumer-packets.v1`, F2 approved 15/30/60-second shots, F4 matching timeline, F5 source SHA/fingerprint with `provider_call_permitted=false` | NEW `feature5_motion/cross_feature_packet_gate.py` validates exact source/timeline/tenant/fresh source packet hash. Gives a **non-executable** `NativeInputPacket`. Existing `feature3_reference_bridge.stage_approved_fashion_first_frame` separately handles real private bytes after a durable claim. | GPU-off offline fixture passes, not a deployed F3 backend integration |
| Feature #3 / main, `poster-engine/fashion_reference_v1.py` | Real `prepare_fashion_references` and `resolve_first_frame` APIs with current RLS/rights callback-based byte verification | Existing F5 bridge uses injected resolver, staging approved non-cropped 704x1280 PNG with immutable SHA + cleanup and revocation tests | Needs coordinator to wire actual authenticated DB readers and source rights; no retailer photo fetched |
| Feature #4 / draft PR #322, `video-engine/feature4_motion_handoff.py` | `prepare_feature5_requests` sets `model_id=hunyuanvideo-1.5-480p`, `prompt_version=feature5-v1`, 5-second `480p` commands | NEW `check_coordinator_motion_profile` rejects Hunyuan and any non-native Wan2.2 profile rather than quietly converting. Existing `wan22_feature4_handoff.reviewed_wan_clip_for_feature4` requires strict settled private receipt and human visual review. | Versioned coordinator mapping and genuine model output absent |
| Part3 / draft PR #125, `premium_video_jobs.py` and `PROPOSED_20261023180000_premium_video_reservations.sql` | Wan2.7 text/image model, 720P/1080P and 2–15-second jobs, initially zero credit. SQL **proposal**, not hosted migration | Existing F5 `part3_private_import_bridge` uses trusted fenced claim, unique durable import intent, exact private Storage scope/SHA, uncertain ack -> UNKNOWN, settled receipt | **Provider/profile/credit schema incompatible** with F5 native Wan2.2 TI2V-5B 704x1280/121frames/24fps. Requires reviewed additive versioned service-only shared migration; worker leads must NOT invent a second ledger |
| Feature #7 / draft PR #513 | Uploaded video auto-broll semantic edit suggestions, not real video virtual try-on | F5 does not label stock-footage editing as Wan inference | Actual video outfit swap is not integrated in Feature7 yet |

## Synthetic test inputs used on our branch

- Fictional boutique teal embroidered SKU; two mocked user sessions/shops, 30-second 3-shot reference plan, native 704×1280 approved first frame (Pillow fixture) and FFmpeg 121-frame testsrc video; neither real retailer photo nor model-generated motion.
- Read-only `NativeInputPacket` is never a fresh tenant media grant. Test callback simulates a re-read of the exact F3 consumer packet; real Feature3 reader MUST revalidate current source bytes, rights, model approval, same-tenant approved brief and revision.
- Caller must separately provide existing transactionally claimed and uniquely reserved Part3 job before Comfy POST or Storage upload, plus independent human review for F4 release. No actual inference or paid API.
- F3/Part3/F4 code is **not copied into Feature5**; only documented exact source contracts were used, to preserve parallel branch ownership and avoid duplicating code.

## Remaining real integration blockers (not passing synthetic test evidence)

1. Coordinator merge/rebase cross-branch source and reconcile ONE versioned Wan2.2 provider/profile, Part3 premium quota/check constraints/transactional paid and import CAS, outbox/queue, private Storage, secure download and signed DEV tenant verification. Current Azure #249 / 503 remains a separate HTTP reliability gate.
2. Feature3 actual tenant-owned licensed model wearing approved exact garment, current server-side bytes & human likeness/retailer rights; model artifacts not in test fixture.
3. Feature4 real professional edited and independently reviewed 1080x1920 customer Reel (audio, garment/face quality, brand/legal signoff).
4. Pexels public pages/license verified but selected raw photo/video files not retrieved (DNS); these are different people/outfits and can't pass wardrobe preservation acceptance. No implied endorsement.
5. License/hardware/weight SHA OCI immutable CUDA runtime and explicitly capped real GPU/API Wan inference. A100 OFF until explicit paid decision.

**Only Feature5-owned source contracts, tests and docs may be changed in this branch. No shared migration, GPU, DEV/PROD/WineShopPOS edits.**


## 2026-10-28 — F3 verified consumer-to-private first-frame staging + hosted catalog reality

\n## Verified DEV Supabase catalog (read only, no writes)\n\nConnected DEV project `jeearzffnjbvghwjjjrf` public catalog returned RLS-enabled `feature3_models` (0 rows), `feature3_gpu_jobs` (0 rows), `media_assets` (1 row), `shops` (2 rows), and **no deployed `premium_video_jobs` table**. Installed migrations end at Feature3 GPU budget jobs `20261028101328`. This proves shared Part3 premium jobs/credits/import CAS NOT deployed; no hosted job can be labeled successful. Test-only local HMAC sessions and portable FFmpeg imports are not hosted auth. No customer rows or secrets were queried.\n\n## New Feature3 consumer-to-private bytes connector\n\n`stage_fresh_feature3_consumer_input` in Feature5 uses exact feature3 consumer packet (`#561`), original garment/model/try-on IDs and first-frame SHA, independent current private Feature3 manifest and `resolve_first_frame` staging; independently re-fetches current consumer packet after staging and cleans the ephemeral PNG on revocation. Real synthetic CPU test confirms byte hash and no GPU entitlement; revoked second read leaves no file. Actual F3 pending branch is not merged into this stacked F5 branch and all native callbacks must be connected by coordinator.\n

## 2026-10-29 — Additive private Storage reader coordination requirement

The Feature5 native Part3 importer now **requires** `read_back_private_chunks(shop, job, attempt, bucket, key)` where the coordinator's trusted Part3 backend authorizes the existing active lease and returns the actual immutable tenant-private MP4 object in bounded byte chunks. The importer SHA256-checks byte stream against ffprobe/inspection, validates full expected byte length, and does **not** finalize reservation/usage or Feature4 media manifest on a receipt alone. No new migration, external URL or independent billable submission is introduced. Any missing/changed/foreign unreadable object after the unique intent is UNKNOWN and must be investigated through existing Part3 read-only reconciliation. The mock reader in media CI does NOT verify real Supabase Storage or signed DEV auth.
