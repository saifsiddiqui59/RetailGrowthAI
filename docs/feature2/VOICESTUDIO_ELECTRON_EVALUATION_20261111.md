# VoiceStudio Electron — RetailGrowthAI voice integration evaluation (2026-11-11)

**Status: NEW REQUIREMENT / EVALUATION ONLY; no production or source integration claimed.**
The owner requested using the GitHub VoiceStudio Electron application for voice in RetailGrowthAI. This evaluation identifies `debpalash/VoiceStudio` as the likely intended upstream; exact choice remains confirmable before implementation.

## Verified candidate
- Upstream: https://github.com/debpalash/VoiceStudio — Electron desktop/web UI plus a separate Python FastAPI speech backend. Features include voice synthesis/cloning, dubbing, narration, transcription and speech workflows.
- Local API: https://github.com/debpalash/VoiceStudio/blob/main/docs/speech-platform.md (local API, `/.well-known/voicestudio-speech` capability discovery on default loopback port 3900; no assumption that a production-hosted remote API exists).
- App license: AGPL-3.0-only; commercial use is possible **under those terms**, but a proprietary embedded/forked service requires independent license review or upstream commercial license. See https://github.com/debpalash/VoiceStudio/blob/main/LICENSE-NOTICE.md.
- **CRITICAL MODEL GATE:** VoiceStudio's default `k2-fsa/OmniVoice` pretrained weights are documented as CC-BY-NC (noncommercial) and have further tokenizer/subcomponent terms; they MUST NOT be used for RetailGrowthAI commercial voice generation by default. The upstream model-inventory documentation explicitly says **no model entry currently asserts reviewed commercial-use clearance**: https://github.com/debpalash/VoiceStudio/blob/main/docs/licensing/model-inventory.md. Audit each exact candidate model/weight/dependency and generated-audio terms separately; commercial code licensing is not model licensing.

## Existing RetailGrowthAI work — REUSE, DO NOT RESTART
- Feature #2 already has **open/unintegrated** proposed CPU Kokoro TTS (#750), a consolidated voice + Azure Speech/local workflow (#848 stacked on #551), and private voiceover WAV/MP3 registration, revocation and authorization logic (#777). Confirm current PR heads, upstream license and integration status before any change.
- Feature #4 already has an **open/unintegrated** proposed voice/music/SFX gain/mixing contract (#830 stacked on #322). Existing main `video-engine/render.py` accepts rights-checked audio assets, currently as `music_asset_id` for v1; do not silently reinterpret that v1 contract as a narrator track.
- Feature #7's editing/STT can consume approved speech transcripts and timing information only through existing reviewed cross-feature contracts. Do not add a second unrelated STT pipeline.

## Proposed integration (not implemented)
1. Feature #2 owns editable narration script, language, timing, voice identity/consent and editorial approval. Preserve current CPU Kokoro/Azure Speech proposals rather than replacing them blindly.
2. Implement a **provider-neutral, opt-in** VoiceStudio speech adapter, preferably connecting to its separate FastAPI service from a controlled trusted backend, **not embedding Electron desktop code into the React/Vite SaaS**. Treat desktop app as an optional authoring tool. Keep feature flag disabled until review.
3. Once a legally cleared model and deployment route exist, normalize each generated voice file to a trusted private audio asset with shop/campaign/script-revision lineage, integrity hash, provider+model revision, explicit voice-consent/rights evidence, audio codec/duration and safe idempotency. Server—not browser—handles storage and signed access; protect against cross-tenant reads, replay and revocation races.
4. Feature #4 blends approved narration, licensed music and SFX via its existing proposed mixer; use actual FFmpeg/ffprobe AAC and timing verification. Feature #7 may use transcript timing for cuts/captions. No publishing until review.
5. Start with deterministic local mock API/bytes and tenant/rights negative tests. Later gate real CPU-only hardware performance and actual audio quality tests. NO auto model downloads, GPU spin-up, paid inference, cloud deployment, PROD or WineShopPOS changes.

## Acceptance and owners
- **F2**: identify matching existing task ID(s), decide whether this is an alternate voice provider to F2-09/F2-29 or an explicitly new dependency; do not silently increase the 159 pinned task IDs. Build opt-in connector + safe private audio metadata and tests only after licensing/contract review.
- **F4**: review compatibility with F4-06 mixer and voiceover timing; avoid shared-contract changes without affected lead review.
- **F7**: use existing transcript/editor handoff, not a separate transcription product.
- **Security/licensing**: verified model/weights/commercial output rights and speaker consent before commercial activation. Verify AGPL obligations and any commercial license with counsel or upstream where necessary.
- **Release status**: NOT STARTED for VoiceStudio; existing TTS/voice source PRs remain separately open/unintegrated as of inspection 2026-11-11; no tests, voice samples, or model calls executed for this new candidate.

This evaluation is a dependency/intake note, **not** proof of installed software, licensed voices, running voice generation or accepted integration.
