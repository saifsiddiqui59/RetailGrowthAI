# Feature4 F4-07 — audio-master source inode continuity (2026-10-30)

**IN PROGRESS.** Feature4-owned source/test branch `feat/feature4-audio-master-source-fence-20261030` stacks on reviewed F4-06 draft #830. No new renderer, model, paid service, public video or user media.

## Actual issue
The private FFmpeg loudness-master path checked SHA256 by `source.read_bytes()` at the beginning and end. If the local MP4 path is atomically replaced with a **different inode containing identical bytes**, the end SHA remains unchanged even though the source object that was inspected is no longer the original authorized file. This also leaves a path mutation window between preflight and FFmpeg source selection.

## Source-only repair
`video-engine/feature4_audio_master.py` now hashes the bounded original source through no-follow `os.open` and stable fstat/lstat checks, binding its original dev/inode/size/mtime and SHA256. The exact same bytes **and inode** must persist across ffprobe, actual FFmpeg AAC loudnorm/streamhash, and final no-clobber publication. Empty/malformed/symlink inputs fail closed. Output video packet hash, FFmpeg loudness bounds, existing `os.link` no-overwrite behavior and private-temp cleanup remain unchanged.

`tests/media/test_feature4_audio_master.py` adds an actual 15s synthetic encode plus forced same-content `os.replace` between mastering and release; receipt/output must be rejected and scratch media cleaned up. The existing actual append-mid-mastering and loudness/video-packet tests remain. Synthetic tone is **not** a human voice or approved music.

## Still blocked / acceptance
Run exact-head four-job branch CI. Coordinator reviews staged PRs #322 -> #779 -> #808 -> #816 -> #828 -> #830 -> this branch, reconciles #650 protected ZIP and main, then proves fresh main 4/4. F4-07 still needs human listening review, full 15/30/60 actual approved audio-mix/fades, signed/rights-scoped source, and Azure #249 recovery/hosted E2E, so do not mark task DONE. These path checks do not replace an atomic server lease/CAS and cannot prevent every malicious concurrent write immediately after the final local check.

**Safety:** no GPU, A100, priced model, PROD, hosted service, WineShopPOS, public sample or automated rights approval.
