# F4-05 renderer effect/parity repair — 2026-10-30

**IN PROGRESS, source tests pending exact-head four-job CI.** Feature4 code-only branch `feat/feature4-rendered-effect-parity-20261030` stacked on draft #816. No GPU, priced model, DEV/PROD deployment or user-facing video sample.

The previously trusted private `creative_reel_v1 -> rg_video_v2 -> HyperFrames` pipeline allowed `subtle_zoom`, `fade`, `slide`, `pop`, `glow`, but the HyperFrames CSS writer rendered **no `.anim-fade` rule** and no text-only scene `.anim-subtle_zoom` effect; `glow` only affected a selected offer. A user could request an approved effect without its corresponding visual transform. Repaired to apply deterministic bounded CSS keyframes on every scene's existing glass layer. No new effect names or untrusted style input are accepted. `creative_contract.py` now shares the trusted `professional.py` allowlists, eliminating divergence.

Added deterministic compiler regression for all five presets and all three transitions to assert emitted classes have matching CSS selectors and keyframe names. Malicious / unsupported names must fail `validate` before any project is written.

**Outstanding acceptance:** This test validates emitted HTML/CSS source, not that a Chromium encoder actually applies the intended transition/effect to every decoded 1080p MP4 frame. Real encoded effect/scene parity and manual editor UI/mobile review remain F4-05 acceptance gates, alongside coordinator-approved main merge / fresh 4/4 CI. All synthetic tests remain noncommercial and do not prove rights, actual human models, F2 creative signoff or Feature5 Wan motion.
