# Feature #4 F4-11 — stock endcard source identity handoff (2026-10-30)

**IN PROGRESS.** Feature4-only branch `feat/feature4-endcard-inode-proof-20261030` is stacked on draft #831. Source-only technical QA; no user-facing video.

## Code change
The existing `feature4_endcard_qa.py` inspected a private 60s stock clip, decoded frames at 53, 57.5 and 59.3s and compared only a SHA256 from reopened paths. Atomic replacement of the original path by a byte-identical file could make both hashes equal while the actual source object had changed. This is a local TOCTOU integrity risk; the claimed proof should not be returned.

Reuse Feature4's `feature4_encoded_motion_qa._stable_source` validator. The encoded original must have the same regular-file inode/device/size/mtime and streaming SHA256 **before and after** the three real FFmpeg frame reads. Change/symlink/replacement/incomplete read denies the report. Original codec, duration, 55-60s disclaimer, source content and no-commercial-approval guards remain intact.

## Negative tests, remaining acceptance
A new regression physically encodes the pre-existing 60s synthetic stock fixture, decodes the first genuine frame, replaces the MP4 pathname with a **different inode containing identical bytes**, and asserts `EndcardProofError`. Its bytes remain unchanged, demonstrating why SHA-only comparison was inadequate. Original encoded hold/reveal and mutation tests remain.

New exact-head branch four-job CI, coordinator-approved draft/main merge, fresh main 4/4, actual revised 60s approved owner video and real human legibility/rights signoff are still required. This test is not a retailer release, a full frame-by-frame anti-blank proof, or a hosted tenant/lease check.

No GPU, paid inference, PROD, WineShopPOS or customer media exports.
