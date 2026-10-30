# Feature #4 F4-02 — full-minute evidence safe inode/bytes reading (2026-10-30)

**IN PROGRESS; source-only pending exact-head 4/4.** Branch `feat/feature4-minute-proof-stable-read-20261030` builds on F4-08 PR #839 source.

## Fixed defect
In `feature4_minute_quality_receipt.py`, the same provenance/caption/visibility/endcard JSON evidence was first SHA-hashed as a path, then **reopened independently** for `read_text` and parsed. A concurrent replacement could make the hash and parsed evidence refer to different local filesystem objects. Moreover, replacing an MP4 path with a new inode containing byte-identical media was not caught by SHA-only `_sha` guards.

## Changed behavior
New `_stable_file` uses no-follow O_RDONLY open plus fstat regular-file and length bound (80 MB media / 2 MB JSON / caller caps). It hashes bytes in bounded streaming chunks and checks exact read size and unchanged original descriptor AND current path dev/inode/size/mtime. JSON is decoded from **the same single verified read**, never reopened after SHA. An atomic replacement with identical bytes is now explicitly rejected; neither local file links nor any report are published by this verifier. Existing semantic evidence checks remain as before.

Deterministic negative tests replace `minute-proof.json` after the first actual digest update with an atomically swapped **identical-byte new inode**, for both media digest and parsed JSON paths, and verify fail-closed; symlink, oversized and malformed JSON negatives included. Tests use synthetic local bytes and do NOT prove an actual valid 60s MP4/video, customer rights, anti-fraud signing, or remote storage CAS.

## Remaining gates
Coordinator accepts only after exact-head four-job branch CI, main conflict/package issue #650 reconciliation, and fresh main 4/4. Real current native revised 60s media and its synchronized F2/F3/F5/F7 rights/quality proofs remain missing, plus #249 Azure 503 DEV E2E. F4-02 remains IN PROGRESS, never production DONE based solely on a local QA code change.

No paid GPU/AI, PROD, WineShopPOS, real branded sample or user approval bypass.
