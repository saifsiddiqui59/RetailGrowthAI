# Feature4 F4-08 — bounded preview seek synchronization (2026-10-30)

**IN PROGRESS / browser source-only.** Feature4 branch `feat/feature4-preview-seek-sync-20261030` stacked above F4-12 draft #837.

## Actual defect and source fix
The existing read-only frame jog, OpenReel timecode entry and scene clip buttons in `TimelineStudioSurface.jsx` updated its own internal `playhead` only. The **real video element** in `VideoStudio.jsx` did not follow this playhead; its signed private rendered output and verified source video excerpt stayed at their old position. A user could believe they had frame-scrubbed while visually previewing a different frame.

Add an optional UI-only `onPreviewSeek` callback emitted by vetted 24/30fps frame snapping. Parent renders one video at a time:
- If the same-shop, non-rejected signed job is `SUCCEEDED` after the current immutable submit, seek that **rendered video element** to bounded output timeline time.
- Otherwise, for a previously independently authorized signed **source preview URL**, seek only inside the already verified `sourceClipPlaybackWindow`: source `trim_start + (timelineSeconds - scene.start)`, clamped to last usable timestamp. Image/text/mock source cannot become a video output.
- On media metadata load the pending position is retried. On shop or approved direction change, edit/rebuild or source selection, stale preview positions reset. Never supply or mint signed links; transport and backend remain responsible for tenant rights/approval. OWNER_REJECTED or edited previous exports remain concealed.
- Scene click and caption click now use the same checked `seekToFrame` path; all previously supported keyboard and timecode actions still use one snapping path. Scrubbing NEVER changes the authorized Reel plan, makes an API call, or approves music/model content.

## Tests & acceptance
Playwright browser regression mounts the actual React VideoStudio and TimelineStudio with a fake signed job and **stubbed HTMLMediaElement clock**: seek to 6.5s, click second 5s scene at 7.5s, assert the **actual selected signed video DOM element** receives both seeks, no extra render API calls and stale signed preview disappears after editing. The stub does **not** prove real decoded MP4 frame accuracy, network expiry behavior, perceptual rendering or commercial media quality.

F4-08 remains IN PROGRESS pending real browser+FFmpeg decoded video, mobile device/manual usability, approved signed DEV v2 and coordinator review/main merge/fresh four-job main CI. No GPU, paid model, external media downloads, PROD, WineShopPOS or user-facing samples.
