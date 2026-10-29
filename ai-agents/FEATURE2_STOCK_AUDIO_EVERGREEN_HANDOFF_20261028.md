# Feature2 independent completion work — real stock candidates, test rights and audio (2026-10-28)

Status: SOURCE-ONLY, GPU OFF, no new paid Foundry or video generation. This is an implementation handoff on unified draft PR #551, not a production launch authorization.

## Genuine stock candidates located online (source pages checked)

* **Samar Layek, Pexels #26761190**, 10-second **9:16** clip of Diwali oil lamps. Source https://www.pexels.com/video/burning-lamp-during-diwali-celebration-26761190/ . License https://www.pexels.com/license/ .
* **Suhas Hanjar, Pexels #34579328**, 11-second **9:16** clip of glowing Diwali diyas. Source https://www.pexels.com/video/glowing-diya-lamps-celebrating-diwali-34579328/ . License https://www.pexels.com/license/ .
* **Ramakrishna Reddy y, Wikimedia Commons Diwali candles.jpg**, Pune Diwali still. Source https://commons.wikimedia.org/wiki/File:Diwali_candles.jpg . License https://creativecommons.org/licenses/by-sa/2.0/ ; creator attribution + license link + modification disclosure and share-alike obligations mandatory for derivative use.

Pexels allows commercial photos/video in advertisements and social posts without mandatory attribution **subject to third-party rights and no implied endorsement**. Any recognizable person, trademark, brand or physical object may need additional releases. A Pexels/general stock license does not prove an actual retailer's garment shape, color, embroidery, catalog ownership, model release or user consent, and does not automatically authorize AI model training/image-to-video transformations. All three catalog rows deliberately carry source_review_status CANDIDATE_NOT_IMPORTED and downloaded_original_sha256 null. **The real Pexels videos and Commons JPEG were not downloaded or reproduced in the repository or CI.** No original media byte hashes, license-grant receipts, human model waivers or FFmpeg media outputs were fabricated. The rights byte-path tests use explicitly synthetic self-generated MP4/JPEG signature-shaped bytes, not original stock assets.

## Implemented Feature2 source and tests

1. ai-agents/stock-references/diwali_stock_candidates_20261028.json contains only externally checked discovery pages/creator, source duration, original license and purpose=ATMOSPHERE_BROLL or CULTURAL_CUTAWAY, no imported media. The frozen catalog is a discovery aid, not approved footage.
2. ai-agents/src/ai_agents/feature2_stock_media.py accepts **only current reviewed rights+private exact-byte SHA evidence** under the correct shop, rejects mismatched owner, stale license, revoked source, model/brand endorsement, missing additional releases, unsigned source, wrong MIME or file signature, changed bytes, missing attribution and revoked membership after private source read. Server-only inspect_stock_from_trusted_shop_jwt requires JWT verifier plus original current role-checked RLS reader functions: no client-provided approval flags. Returns offline preview receipt with can_publish/can_dispatch_motion/gpu_enabled=false.
3. ai-agents/src/ai_agents/feature2_stock_cutaway.py uses an actually compiled pinned MIT Director plan, matches 5-second story shot in a 30/60-second draft with an eligible reviewed vertical Pexels video and exact original SHA. It will NEVER replace a garment product shot, hook or retail CTA, truncate a clip, change the signed motion JSON, authorize paid motion or claim to have rendered. 15-second ads without a story beat cannot silently gain B-roll.
4. ai-agents/src/ai_agents/feature2_audio_evidence.py validates bounded exact private current-shop 16-bit PCM WAV bytes, sample rate, time length vs 15/30/60s script, original SHA and commercial rights record with repeated membership checks. **Silent generated WAV test files do not prove words, real human narration or lip sync**. Returned can_publish/paid_motion/gpu=false and actual_human_speech_verified=false.
5. ai-agents/src/ai_agents/feature2_editorial_basis.py permits trusted owner/editor seasonal original brief **offline-only** when authentic trends had zero relevant match. It forbids inventing trend_id, viral claims or POSTing to the trend-backed DRAFT API. Real live trends still require approved relevance with source citations.

Negative/source tests: ai-agents/tests/test_feature2_stock_media.py, test_feature2_stock_broll_integration.py, test_feature2_audio_evidence.py, test_feature2_editorial_basis.py. They use test-only JWTs, local original bytes and 15/30/60s pinned original real Node compilation. No paid services or external media used during CI.

## What is still ACTUALLY pending

**Source integration:** coordinator must choose unified #551 or seven duplicate source PRs, merge once, update main docs PROJECT_STATE / NEXT_TASK / DECISIONS / WORK_LOG and verify postmerge 4/4 independent CI.

**Azure execution:** actual Functions ZIP still lacks reviewed executable Node22+ and MIT JS; no real deployed route, binary verification or Function initialization was performed.

**Retailer/live rights:** current signed JWT/RLS profile, stock original downloads under private tenant ownership, identity/rights/consent and every original SHA need real acceptance; old synthetic account is inactive and cannot be impersonated. Only stock atmosphere clips may be composited. Do not represent stock model as retailer-approved model, claim source clothing as the customer's actual product, or falsely endorse.

**Real creative/editor motion:** actual GPT-4.1-mini 15/30/60s original provider prose, human blind creative approval, true voiceover recording + word timestamps, visual garment six checks against a genuine commercial first frame, F4/F5 versioned Wan provider/480p mismatch and actual FFmpeg Reel remain unverified. No paid motion or GPU startup authorized.

**Hosted:** signed positive DRAFT save+readback is blocked by lack of relevant fresh fashion trend in protected DEV and original Azure #249 503; seasonal no-trend mock plan is not a substitute for hosted persistence. Any future paid model or rendering needs separate budget approval. All source-only workflows default publish=false and GPU OFF.

Ownership: feature worker edits only ai-agents/** in this handoff. Coordinator alone changes docs shared APIs, deployment package, platform release and GitHub workflow. WineShopPOS and PROD untouched.
