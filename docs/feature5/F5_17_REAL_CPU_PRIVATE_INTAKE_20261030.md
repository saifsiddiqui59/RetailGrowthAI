# F5-17 — Real CPU native-format private output end-to-end (source acceptance)

Date: 2026-10-30. This explicitly distinguishes actual FFmpeg-decoded **synthetic CPU media** from the genuine model output required for original F5-17.

## Implementation and evidence

Added `tests/ai/test_feature5_wan22_real_cpu_private_intake.py` with real local **FFmpeg and ffprobe executables**, not mocks:

1. Encode an original synthetic moving test pattern at native 704×1280 H.264 24 fps × 121 frames (duration 5.041667s) in an isolated private attempt directory `0700`, output file `0600` under the pinned `rgai/feature5_00001_.mp4` SaveVideo naming convention. Pass it through the existing real source flow `find_single_private_wan_mp4 -> inspect_native_mp4 -> screen_motion_frames -> pending_private_receipt` and enforce exact media SHA, source lineage, five decoded frame samples, two independent test-fenced source/attempt checks and receipt SHA256. Passing output **must** remain `NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW`, `output_is_ai_proven=false`, `approved_for_feature4=false`; no publishing or Storage writes.
2. Encode an actual silent static 121-frame H.264 video with matching native profile. FFprobe accepts codec/profile; real five-frame FFmpeg screening rejects it as obviously static, so private intake denies a receipt.
3. Encode an actual brief 2.35–2.65-second **single-flash** overlay on a static 121-frame H.264 video. The real CPU decode at sample times 0.25/1.25/2.50/3.75/4.90 seconds produces luma differences [0,239,239,0]; it must be **REJECTED** even though its maximum difference is very high. The previous max-only threshold allowed this false positive. Requires at least three of four active intervals, never a human/production approval.
4. Encode an actual native-shaped H.264 video **with an additional AAC stream**. Real ffprobe rejects the non-silent/stowaway content before motion screening or receipt.

Local FFmpeg command probes checked static, flash-only and audio streams with exact duration/fps/framing. Automated Python CI must independently verify these tests in its runner and all four exact PR-head jobs pass. No golden media file, sample customer reel or synthetic bytes are persisted after the temporary test folder closes.

## F5-17 actual release blocker

These tests verify decoder and private-output adapter behavior, **not** Wan/Comfy GPU inference, original model weights, commercial garment and likeness licensing, operator budget, authentic Part3 claim, independent model provenance, Feature4 editorial approval or reviewer signature. The authentic licensed 5s Wan render at 704×1280, 24fps, 121 frames plus actual human garment/face/anatomy review is still required; **F5-17 remains BLOCKED**.

Coordinator alone integrates existing one-batch source PR #781 into parent #465 and then main, with fresh all-four post-integration CI. Original 22-task ledger stays **0 integrated DONE / 3 IN PROGRESS / 19 BLOCKED**. GPU OFF; no paid providers, Azure remote requests, Supabase hosted SQL, PROD or WineShopPOS modification.
