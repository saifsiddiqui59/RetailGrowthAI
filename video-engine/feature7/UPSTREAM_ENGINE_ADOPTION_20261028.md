# Feature #7 — Existing GitHub engine reuse, not a new editor

## Selected upstream projects (28 October 2026)

| Upstream | License | Why chosen | This branch |
|---|---|---|---|
| [AutoBroll](https://github.com/andriidrok1/autobroll) — pinned `4aef3afb099c866bd2977c184f9912ba57318f77` | MIT (original `AUTOBROLL_MIT_LICENSE.txt` retained) | Original short-form edit: word captions, B-roll time anchoring, silence-based edit planning, reviewer timeline, retake organization | Previously adapted in `autobroll_semantics.mjs`, `gap_cut_advisory.mjs`, `semantic_suggestions.mjs`, etc. Full paid Gemini/Remotion UI not imported |
| [AutoClip Core](https://github.com/branmendo/autoclip-core) — pinned **`56311d24788361978d2c20ffcdcc5dd9bd43319a`** | MIT (Brandon Mendoza, 2026; exact license included `vendor_autoclip/LICENSE`) | Actual CPU speech-based retake removal, pause cutting, safe maximum cut budget, FFmpeg concatenation **with short AAC audio acrossfades** | **Copied actual upstream modules** unchanged into `vendor_autoclip/autoclip/`: `retakes.py`, `pauses.py`, `models.py`, `constants.py`, `ffmpeg_util.py`, `compose.py`; adapted only a binding wrapper `autoclip_cpu_adapter.py` |
| [Auto-Editor](https://github.com/WyattBlue/auto-editor) | Unlicense | Large/active original project for loudness & motion first-pass cuts and editor timeline interchange | **Evaluated, not copied/installed**: current core is in Nim and requires separate runtime/build compatibility; adding it to the active Python/Node CI without adapting the actual implementation would not prove real integration |

**Feature #4** still owns `MartinDelophy/ai-video-editor` integration, the professional timeline, final render/audio mix, brand, captions/B-roll and signed media. **Feature #7** owns source footage AI edit decisions: real speech evidence, retake/gap cuts, caption/B-roll source timing, reviewer confidence. Feature #2 owns script and dialogue. No second editor built.

## How the new upstream implementation actually runs

`video-engine/feature7/autoclip_cpu_adapter.py` is small integration glue:

1. Read a **trusted absolute private MP4** and exact source SHA256; require H264/HEVC-compatible FFprobe evidence of existing video **and audio** and bounded duration.
2. Validate bounded word-level timestamps. The test uses human SRT/reference words; the wrapper **cannot claim real WhisperX inference**. For real SaaS the independent authenticated, rights-bound CPU ASR worker must supply `verified_signed_cpu_asr` evidence.
3. Directly invoke original AutoClip Core methods `detect_retake_cuts`, `detect_transcript_pause_cuts`, `merge_cut_windows`, `enforce_removal_guardrail` (max 40% original footage), and `cuts_to_keep_segments`. No custom retake or pause cut algorithm is implemented.
4. Emit **NEEDS REVIEW** cut/keep coordinates, source SHA256, audio preserved and actual upstream source revision. This packet cannot approve itself or be sent to a browser as trusted authorization.
5. Optional **local test preview only** invokes upstream `compose_media` (FFmpeg trim/concat; 30ms audio-acrossfade joins, retains recorded AAC source) and independently verifies the output is shorter, has both video/audio and original source SHA unchanged. Real Feature4 rendering and tenant signing remain separate.

Tests: `tests/media/test_feature7_upstream_autoclip.py` exercises actual upstream false-start repetition, source-attested pause plans, real local FFmpeg video+audio edit, shorter output with AAC stream and non-silent volume statistics, and forgery/unknown-transcript/output-replay negatives. This synthetic transcript/voice tone does not prove **natural speaking quality**.

The existing `tests/media/test_feature7_public_cc0.py` uses a pinned public CC0 source with real spoken English and human-provided SRT to validate private speech evidence. The actual WhisperX model has not run. Public Pexels assets from the existing FullHD sample are **retail stock shots with no verified matching speech**, so fabricating retakes for them would be invalid.

## Explicit not-done gates

- Install legally reviewed CPU speech/word-aligner weights and prove real word-level ASR accuracy and speech quality.
- Apply real old/new media rights, input validation, JWT/RLS, private upload and durable signed approval/outbox. Local fixtures do not confer retailer ownership or human consent.
- Test real multi-take speech footage through actual AutoClip Core + human visual/audio review, caption legibility/safe zones, correct product-matching B-roll, true hook narrative and acceptable pacing.
- Feature4 must execute cross-feature multi-cuts, word-timed captions, B-roll and final music/audio mix inside its existing professional editor, with signed private 1080p output and tenant approval. Do **not** claim the old one-crossfade Pexels slideshow is professionally accepted.
- Hosted DEV two-shop rights/revocation/readback, release quality and human approval. **Owner rejected the former Pexels sample** for visual quality, even though encoding CI was green.

**GPU remains off; no paid API, Azure GPU, PROD or WineShopPOS changes.** Only Feature7-owned source/tests/docs changed; canonical shared docs belong to coordinator, as specified by `AGENTS.md`.
