# Feature #2 — audio recommendations and Pexels clothing fixture (2026-10-28)

## Open-source code selection (not hypothetical rewrites)

* **Kuble-Lab/open-creative-director**: 9 stars / 0 forks at live repository review, MIT, active October 2026; **best functional match** to brief -> director -> script -> beat-aware music video -> voice. We already vendor and verify four unchanged pinned upstream blobs at commit `4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f`. Continue modifying/adapting this actual engine, not building a duplicate standalone director.
* **librosa/librosa**: ~8,716 stars / 1,093 forks, ISC, actively maintained; high-usage technical candidate for tempo, BPM, musical features from **licensed actual audio bytes**, not a viral-feed or copyright source. Optional future backend dependency; **not imported or run** by this commit, because no verified licensed source audio has been obtained.
* **beetbox/beets**: ~15,860 stars / 2,170 forks, MIT, active; excels at music library metadata, but does not certify commercial-use rights or provide real-time platform virality. **Not added**, to avoid a large unrelated dependency.
* **pexels/pexels-javascript**: official Pexels API client, ~180 stars / 27 forks; official source adapter for future server-side authenticated Pexels discovery/import. Pexels video API uses `/v1/videos`. **No API key present; no official client or actual downloads invoked**. API terms request prominent Pexels credit and photographer credit when possible.

Stars are discovery metadata recorded 2026-10-28, not an approval or correctness metric. Functional fit, MIT license, reproducibility and existing working integration outweigh star count alone.

## New working source

`ai_agents.feature2_music_recommender.recommend_audio` ranks bounded metadata for Instagram Reels, YouTube Shorts, Meta Sound Collection, Pixabay Music and private retailer uploads. Ranking is category/context/observed score-based; it cannot claim a track is viral. Optional **trusted server-side approved-model** ranker can reorder sanitized audio IDs (no fake IDs, unbounded calls, client-provided approval or changes to rights). Result is only a DRAFT shortlist, with sound attachment, publication and GPU execution always OFF. **A new optional \`AzureFeature2AudioRanker\` reuses the existing tested Azure Foundry v1 transport, endpoint allowlist, durable maximum-cost reservation, original billable token accounting and single-attempt/no-retry rules. It is OFF by default unless the server sets \`RETAIL_FEATURE2_AUDIO_AI_ENABLED=true\` after tenant JWT/RLS, subscription and budget consent. Mocked Azure response tests verify AI audio-ID reordering, rejected hallucinations, no calls when disabled and no egress when reservation fails. **No real Azure AI/music provider call was made; only mocked responses were used.**** The actual imported audio and original license evidence must be checked before Feature #4 mixing or Part #2 platform-native attachment. Platform music licensing may differ for commercial business Reels.

`ai-agents/test-fixtures/clothing-shop-pexels/manifest.json` is a cross-feature test shop **discovery catalog**: 2 genuine Pexels image pages and 2 genuine Pexels video pages, creators, media purposes, durations and explicit unresolved rights. Feature #2 may use it for offline storyboards; Feature #3 must substitute actual authenticated and garment-accurate shop-owned references; Features #4/#5/#7 may use it to plan tests but **must not treat URLs as media bytes or signed storage assets**. Stock people/models have no documented release in this fixture. Original media were not downloaded (environment has no outbound connectivity); all original SHA-256 fields and private storage refs remain null. There is no real authenticated DEV shop/media record. A catalog entry is not a usable audio/video file.

## Existing prompt improvement UI

`/trends` already supports **Improve Prompt with AI** checkbox, `Improve Prompt` action, side-by-side original + editable enhanced prompt, change reasons, restoration, explicit `Use Improved Prompt`, and a separately opt-in approved-budget live AI toggle. No paid inference occurs by checking the basic box. Existing Playwright tests exercise preview, editing, save and viewer restrictions.

## Unverified for hosted production

No licensed audio bytes, AI sonic analysis, provider-authenticated live viral sound feed, commercial music clearance, rights-approved original stock downloads, tenant-private source imports, real paid LLM response, signed hosted draft, or playable customer Reel. Do not conflate passing fixture/code tests with those acceptances. No cloud provisioning, PROD, main merge or WineShopPOS modifications.

Owned-path worker handoff: coordinator chooses unified PR #551 **or** overlapping constituent PRs, never both; coordinator alone revises canonical shared documentation/contracts and imports approved media. 

## Reproducible manual Pexels import (source-only)

The shared fixture has an official-SDK downloader at \`ai-agents/test-fixtures/clothing-shop-pexels/import-official-pexels.mjs\`, plus README. \`node .../import-official-pexels.mjs --plan\` is exercised without network in CI. An authorized operator may \`npm install --no-save pexels@1.2.1\`, set \`PEXELS_API_KEY\`, and run \`--import\` to download Pexels original photos/MP4s into an ignored local review folder, checking SHA256 and media signatures. **It does not install dependencies in the repo, upload media to Supabase, assert person releases or commercial rights, or make a real hosted shop.**

## More suitable high-adoption upstream discovered and integrated

**MoneyPrinterTurbo** (`harry0703/MoneyPrinterTurbo`) was inspected directly on GitHub: **136,107 stars, 21,627 forks, MIT**, updated 2026-10-28. It more closely matches the end-to-end requirements than the 9-star Director alone: script generation, Pexels/Pixabay/Coverr stock, automatic or imported narration, subtitles, background music, and full-HD vertical output. We do **not replace existing Feature2 Director**; its script/scene contract already has 4/4 CI. We **adapted actual MIT implementation logic** from MoneyPrinterTurbo `app/services/material.py`, pinned commit `fd5127e81721f36f0a85aee21b298cc5f4452f42`, original blob `84431d1152a3e2adebfe83fdfe90ebd600ee51a3`: portrait/landscape resolution filtering, smallest acceptable 1080p source, and voice-duration-aware prefix selection. The adapted pure-data code and test live in `ai_agents.feature2_pexels_renditions`; the official Pexels SDK importer now selects smallest adequate 1080p instead of a wasteful 4K file. Upstream MIT LICENSE is retained verbatim at `ai-agents/oss/MoneyPrinterTurbo/LICENSE`.

**Important:** MoneyPrinterTurbo's README warns that its bundled `resource/songs` may have copyright issues. We did **not copy any MP3 or unverified song**, and did not transplant its live HTTP/API credential configuration or publishing backend. This adaptation uses pinned real code without mixing platform rights or rewriting the existing project. No external downloads, paid AI requests or original media files were performed during this change.
