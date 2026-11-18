# Feature #3 — GPU-OFF fashion consumer contract checkpoint

Date: 2026-10-28. Scope: **source-only**, never a hosted release, renderer or paid inference. This branch continues the merged Feature3 review/import/evidence changes, including #553, #555 and #559. GPU is OFF.

## Implemented in this branch

- `poster-engine/feature3_consumer_packets_v1.py` assembles **non-executable, metadata-only** fashion handoffs for Features #2 (approved creative shots), #4 (timeline), #5 (leased-first-frame request only), and optional #7 (approved retailer-uploaded footage metadata). This is a private server adapter, **not** a substitute for their writers, editors, queue workers or actual consumers.
- Each of the three purpose-specific expected fashion manifests is independently refreshed through existing `prepare_fashion_references` and trusted signed/RLS backend callbacks. It verifies actual registered media bytes/sha, current tenant rights, approved catalog identity and consistent model/garment/try-on lineage. It refuses stale model rights revision, changed first-frame hashes, changed garment identity and mismatched per-purpose source state. Canonical UUIDv5 model IDs are supported to match the existing feature library; shop and media UUIDs remain v4.
- Only a current backend-fetched `APPROVED` creative brief may enter. It must pin the source fingerprint, garment original SHA and approved revision; 15/30/60-second stories require contiguous bounded shots, safe camera instructions and explicit preserved garment identity. An optional uploaded MP4 must have current same-shop APPROVED editing rights and a stable hash. The result contains no private Storage URL, raw image bytes, service keys or paid execution allowance.
- Feature #5 packet keeps `provider_call_permitted=false`, `lease_claim_required=true`, `cost_reservation_required=true`; a real private worker **must additionally** call `resolve_first_frame` against fresh rights with an authoritative durable lease immediately before GPU execution. Feature #4/#7 must recheck rights before any output/footage consumption. No output is published automatically.
- `tests/media/test_feature3_consumer_packets.py`: 18 offline cases including mismatched shops, revoked uploaded footage, forged tokens/extra payload fields, altered hash, stale review/rights, camera shape/duration, malformed values, preserved SKU attributes, and **actual Pillow PNG** source refresh via the existing synthetic Feature3 fixture. CI's `video-engine/ci.sh` discovers `tests/media/test_*.py`.

## Fictional test scenario

One test-only Diwali retailer offers SKU `DIWALI-TEAL-001`, an A-line teal `#2B6978` kurti with gold floral embroidery, round neckline, elbow sleeves and knee length. The sample 30-second storyboard preserves the original garment through three 10-second camera-only shots. All image, reviewer and approval identities are **test doubles**, not legally-cleared fashion photography, verified commercial advertisements, authentic human decisions or actual model inferences. A second UUID represents a foreign shop for denial checks.

## Evidence and deployment boundaries

- Local mocked-backend regression is not production customer authorization. Model rights, RLS, byte SHA and human-review source gates have separate preexisting tests; this branch exercises both patched handoff cases and a real synthetic Pillow source adapter integration.
- The existing Feature3 import/reviewer/evidence SQL migrations, hosted DEV feature flags and paid GPU still require separate reviewed deployment authorization. Do **not** apply migrations, set flags, provision GPUs, call FLUX, invoke FASHN providers, or publish from this module.
- Real licensed customer photography, independent adult-likeness and commercial authorization, actual output visual fidelity of color/neckline/embroidery/sleeves/shape, private generated-output media registration, outbox/lease/settlement recovery, hosted signed two-shop browser checks, and Azure issue #249 remain open. Do **not** mark Feature3 product complete or GPU-ready on this evidence alone.
- No production or WineShopPOS resources were modified. Feature-lead branch PR requires coordinator review/merge under `docs/PARALLEL_WORK.md` and four exact-head checks, followed by independent main CI.

## Future execution steps

1. After source CI succeeds, coordinator may review and merge this internal contract **without changing shared `docs/INTERFACES_V1.md`**. Integrating Feature2/4/5/7 real handler call sites requires the respective feature owners' acceptance; no source contract claims to have deployed that wiring.
2. Independently implement/test the generated-output writer, media SHA registration, current lease/CAS, stale/revoked download deny, poison reconciliation and measured prepaid settlement in Feature3-owned source; do not call mock ledger receipts real charges.
3. Prepare protected model-import image Storage UX and owner/editor/curator proof chain, blocked until actual licensed originals and separately authorized DEV SQL deployment.
4. Only after all source/offline gates are closed, request explicit FLUX one-run GPU approval. Use existing dry-run-first GPU scripts. Benchmark actual VRAM/elapsed USD, real licensed VTON visual QA, output hashes, signed DEV acceptance, and Azure issue #249 reliability before live release.
