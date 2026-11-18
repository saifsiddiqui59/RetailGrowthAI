# Feature #2 — VoiceStudio upstream adoption (2026-11-11)

## Owner direction and decision proposal
Reuse **unmodified VoiceStudio** rather than recreating TTS, dubbing, voice cloning and transcription. Upstream: https://github.com/debpalash/VoiceStudio, examined on 2026-11-11 at commit `e5da4aa6461eeea913232bc25be13609e377965c`. This is a **source-only integration proposal**, not a deployed, licensed or proven voice service.

**Implementation choice:** use the upstream, version-pinned, headless VoiceStudio Docker runtime and its `POST /v1/audio/speech` OpenAI-compatible API. The maintained browser renderer also works in Docker; there is no requirement to ship the desktop Electron runtime to SaaS customers. The alternative of copying hundreds of upstream Electron/backend/model/desktop files into RetailGrowthAI would introduce avoidable rebase work, native build dependencies and potential AGPL scope ambiguity. Reusing the upstream container is the closest maintainable form of "copy exact code and customize our SaaS" without changing VoiceStudio itself.

## Source implemented in this PR
- `feature2_voicestudio_adapter.py`: minimal server-only direct upstream WAV request, disabled by default; refuses an unverified commercial model; server-selected voice only; HTTPS or loopback with explicit port; no client-supplied URL, downloads, installation, GPU, retries or storage writes; bounded input, response and WAV validity.
- `test_feature2_voicestudio_adapter.py`: mock transport tests only. No real model loaded, no voice copied, no remote service called.
- Existing React/Vite, Supabase Auth/RLS, private storage, quota/ledger and Feature4 FFmpeg/HyperFrames compositor remain authoritative.

## Upstream licensing and deployment
- Application: **AGPL-3.0-only**. Modified network-served versions require AGPL corresponding-source obligations. If a proprietary combined product is desired, obtain an appropriate commercial license before embedding/reworking upstream code.
- Default `k2-fsa/OmniVoice` weights: **CC-BY-NC** according to upstream license notice/model inventory, **NOT** approved for our paid SaaS; the associated audio tokenizer has other terms. Upstream application code's AGPL grant does not permit noncommercial model weights to be used commercially.
- No model is selected or installed by this proposal. Never download default weights, start a paid provider, or enable voice/clone/dub in RetailGrowthAI until a **specific compatible model revision and dependencies** are cleared.
- Do not bind the default backend anonymously to a public interface: upstream is unauthenticated on loopback by default. Keep backend private, require a trusted API key for non-loopback traffic, TLS, strict network ACL; DO NOT expose upstream admin/system/settings endpoints to retailers. Never give users VoiceStudio's root API key.
- Pin a release image by **digest** after reviewing build/dependency provenance, and maintain license notices and a source-offer plan if modifying AGPL code. No Docker resource, Azure service, storage, private model weights or PROD changed here.

## Scope and PR closure plan
1. First validate the existing real retailer JWT/RLS/rights/one-shot budget contracts around a server-to-server VoiceStudio call; integrate signed private WAV and original tenant-safe job identity with Feature2. Test mocked CPU path and real CPU voice with a commercially cleared model when available. No bypass of `#249` or protected packaging `#650`.
2. Reuse VoiceStudio transcription/dubbing after proving compatible downstream Feature7 signed transcript and Feature4 WAV/AAC audio-mix contracts. Keep F2 creative copy/script editor, F4 final compositor, F7 edit advice/caption timing, and security/billing functionality that VoiceStudio does not replace.
3. **Do not close #551, #848, #513, #322 or their stacked source PRs merely because upstream advertises similar features.** First map every voice-specific source delta to a tested equivalent (or explicitly retire a duplicate), review retained tenant/rights checks, integrate the replacement and verify exact-head + fresh-main 4/4 CI. Then close only superseded PRs *unmerged*, with a concrete link to replacement and tests. Do not mark original task DONE just because a duplicate PR was closed.

## Verification and next
`cd ai-agents && uv run pytest tests/test_feature2_voicestudio_adapter.py` or `PYTHONPATH=ai-agents/src pytest ai-agents/tests/test_feature2_voicestudio_adapter.py`; CI should run all four standard jobs on PR head.
Status: **CODE PROPOSED / PROVIDER DISABLED / NO REAL SYNTHESIS OR MODEL LICENSE CLEARED / 0 old-approach PRs closed in this checkpoint**.
