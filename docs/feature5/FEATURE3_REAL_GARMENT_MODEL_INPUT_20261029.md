# Feature #3 actual garment + model demo image bytes consumed by Feature #5 (2026-10-29)

## Status

**Implemented and committed on F5 draft PR #465** as a GPU-OFF, TEST-ONLY input path. This is not a generated try-on nor permission to run paid ComfyUI or show a customer result. Feature #3 has indeed supplied **actual verifiable photographic bytes** for a fictional model and a separate garment. Feature #5 must not hold up **source or FFmpeg technical testing** waiting for a retailer's live assets. A final faithful fashion try-on, however, still requires a model actually wearing the precise product and independently current commercial authorization.

## Inputs taken verbatim from Feature #3

Source is Feature3's existing `poster-engine/feature3_demo_inputs_v1.py` and pinned authoritative manifest `tests/fixtures/feature3/openvto_demo_sources_v1.json`, whose actual pinned original bytes were already verified in Actions [#40820810387](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40820810387). Publisher [Prompt-Haus/OpenVTO](https://github.com/Prompt-Haus/OpenVTO/tree/10140178cdb198ff17ad7b226c432bd63d732fc2), source revision `10140178cdb198ff17ad7b226c432bd63d732fc2`, MIT demonstration media notice copyright 2026 Prompt Haus.

| Role | Exact upstream source | Git *blob* SHA-1 (actual copied bytes) |
| --- | --- | --- |
| Fictional model pose | `packages/sdk/openvto/assets/people/1_posture.jpg` | `72a86a60280976ce5c73db9525d9648b54d1126a` |
| Separate apparel still | `packages/sdk/openvto/assets/clothes/shirts/1_front.jpg` | `878fde8857f58862723f85d7f8bd723c65a8e498` |
| Required MIT notice | `LICENSE` | `d246e4160c1d8c59bc9e99a90b095ec42ee5cec5` |

Transferred **unaltered original Git blobs** via GitHub's base64 source read plus creation of the *same* blob SHAs in RetailGrowthAI's Git database. Test files are now materialized at `tests/fixtures/feature5/f3_real_openvto/{model_posture.jpg,garment_front.jpg,LICENSE-OpenVTO.txt}`. Every blob matches its upstream Git SHA-1. Actual model and apparel file sizes and decoded JPEG bounds are independently revalidated by **Feature3's own** `verify_demo_image` when consumed, with runtime SHA256 recorded. No third-party fetch is required by offline CI, and no customer photos or secrets are checked into source.

## Concrete Feature #5 ingestion

- New `feature5_motion/feature3_mit_demo_input.py` calls Feature3's real `validated_manifest` and `verify_demo_image` through trusted Python imports and checks the exactly pinned demo-only F5 flags. Verifies raw model and garment original Git blob SHA and license, disallows linked/hardlinked, replaced or mutated files and rejects any forged paid/publish/private tenant flag.
- Creates an ephemeral **0700** private test directory and **0600** 704x1280 PNG from original model JPEG, preserving proportions with background letterboxing rather than swapping apparel. Generates a native **704×1280, 24 fps, 121 frames** ComfyUI Wan2.2 graph with the actual staged model image name; it **does not** POST or run inference and yields a source provenance + denial receipt.
- `tests/ai/test_feature5_real_feature3_mit_input.py` uses **the actual Git-tracked two JPEG originals** and the real Feature3 validators, not Pillow-generated stand-ins. It decodes the resulting PNG and checks dimensions/digest, graph topology/profiles, private cleanup and all negative flags; falsified images, MIT notice, source claims/permissions and fake validation receipts must fail. These are **offline development tests**, not a replacement for the existing `stage_fresh_feature3_consumer_input` + `resolve_feature3_worker_handoff_first_frame` private rights+lease path.

## Current outcome: exactly what this unblocks

**Ready:** Feature5 model pose *and* garment reference are now available to offline contract and native graph tests, without asking Feature3 to resend demo files or waiting for GPU/FLUX. They are actual upstream photographic bytes, not merely public URLs or generated internal fixtures. Feature3 has not generated an image proving this particular model wears that particular garment. There are two independent inputs, not a verified outfit-on-human fashion photo.

**Still mandatory for billable image-to-video:** current signed OWNER/EDITOR, tenant/RLS and approved/revocable source media, separate selected first frame *actually wearing correct SKU*, human/curator fidelity approval, Part3 leased reserved-cost job, approved model/runtime/OCI and an explicit capped GPU/inference authorization. Without those, `provider_call_permitted=false` is enforced. The demo image is not a customer-owned SKU, provider-inferred VTON or approved advertisement.

No shared schema, Feature3 or Feature2 owner source, hosted cloud, GPU, provider spending, customer data, PROD or WineShopPOS was changed by the ingestion.
