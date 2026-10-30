# F4-06 — bounded independent audio gains (2026-10-30)

**IN PROGRESS; Feature4 source only**, stacked on draft #828. No user-facing control is enabled and no output is commercial-ready.

## New trusted source shape
`creative_reel_v1` and `rg_video_v2` now optionally accept `audio_mix` containing at most four reviewed channel names: `source` (original video audio, [0.20,1]), `music` (licensed bed, [0,1]), `voiceover` (licensed full-length narration, [0.20,1]) and `sfx` (licensed 2-second effect, [0,0.50]). A finite real number with 0.01-step precision is required. Boolean, NaN/Infinity, injected CSS/filtergraphs, missing authorized tracks or unrecognized keys fail closed. Existing defaults remain source 1, music 0.55, voiceover 1 and SFX 0.25.

Trusted Python compiler writes matching existing HyperFrames `data-volume` on the four existing track families with fixed per-channel gain. Under original video audio or narration, music is automatically capped to 0.12 to preserve dialogue audibility. Independent gains have **no bus automation or per-word/adaptive ducking**. Only an authoritative coordinator/backend approved snapshot may provide this map; never accept a browser draft gain as authority.

## Evidence
Source-level compiler tests verify the actual emitted HyperFrames track index + per-track volume and no regression to existing default attributes. Cross-feature source tests verify trusted request -> plan -> HTML media route with an actual offline synthetic H264/AAC video fixture. Negatives refuse unsupported/inert channel gains, nonfinite/string/bool/out-of-bounds values, false production authorization. CI four-job exact-head branch required; actual *decoded final AAC output* of each optional channel and signed owner gain selection remains separately unverified. Original 31-task ledger updated.

**Dependency/acceptance:** Real media rights and F2 approved narration/music remains separate; F4-07 human audio mix/ducking listening QA and F4-06 editor gain UI still disabled; source-specific PR requires coordinator-approved main integration and **fresh main four-job CI**. #650 protected package and #249 Azure 503 remain coordinator. No GPU, paid AI, production cloud, signed downloads, user-facing samples or WineShopPOS.
