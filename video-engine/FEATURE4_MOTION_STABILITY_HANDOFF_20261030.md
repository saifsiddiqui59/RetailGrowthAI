# Feature4 F4-11 motion source stability — 2026-10-30

**IN PROGRESS / source-only; not approved encoded quality or retailer media.** Independent Feature4-only draft `feat/feature4-motion-source-stability-20261030` built from #816 at `d01e3c716b4f651809d645684c921c6f0413c343`; this is a *sibling* to F4-05 #822 and F4-15 #824, with disjoint changed files.

## Fixed risk
Before this patch the F4 actual-encoded moving-pixel QA sampled two frames per nominated scene and only SHA-hashed the **end-state** video when writing the receipt. If a same-path file changed during the probes, the receipt could bind post-swap SHA to pre-swap pixel observations. A same-byte atomic pathname replacement could also pass a SHA-only guard. Also, NaN in threshold/offset/separation could bypass numerical range validation; tightly neighboring scene-start probes could measure motion across a cut rather than within a single authorized moving scene.

## Source-only mitigation
`video-engine/feature4_encoded_motion_qa.py` now opens the decoded source using no-follow O_RDONLY, hashes in 1 MiB chunks, and verifies regular inode/device/size/mtime on open descriptor and final pathname **before AND after** real FFmpeg frame decoding. Any mutation, symlink, swap, or changed bytes refuses to issue a verified-motion proof. The encoded-duration and portrait H264/AAC codec preflight remains. Config parameters must be finite, bounded real numbers (never bool), and each sample pair must finish inside the same requested moving-scene window. This is a local technical QA control, not an authenticated cloud storage/rights guarantee.

`tests/media/test_feature4_encoded_motion_qa.py` adds real FFmpeg synthetic encoding with an after-first-decode unauthorized append and a same-content `os.replace` swap, plus non-finite config and cross-scene probe negatives. No customer content, model inference or GPU. Existing moving/frozen codec tests remain. **Only exact-head four-job green CI + coordinator approved merge/main 4/4** qualifies accepted source work. Even then, F4-11 remains IN PROGRESS pending real revised Full-HD 60s visual sequence, approved rights, human QA; no commercial release claim.

Dependencies #650 protected ZIP, #249 Azure 503, approved F2/F3/F5/F7 outputs and DEV signed integration remain coordinator/external. No PROD changes, paid services, or WineShopPOS modifications.
