# VoiceStudio upstream source (pinned, not reimplemented)

RetailGrowthAI reuses the **exact original upstream VoiceStudio code** as a Git
submodule at `vendor/VoiceStudio`, pinned to commit
`e5da4aa6461eeea913232bc25be13609e377965c` from
https://github.com/debpalash/VoiceStudio.

This keeps the original Electron/web app, FastAPI backend, tests, licensing
notices and upstream source available without blindly copying thousands of
files or maintaining a divergent fork. It is independent of WineShopPOS.

## Fetch source during development

```sh
git submodule update --init vendor/VoiceStudio
git -C vendor/VoiceStudio rev-parse HEAD
# Expected: e5da4aa6461eeea913232bc25be13609e377965c
```

A normal shallow GitHub Actions checkout does **not** recursively clone the
large upstream by default. Do not change global CI to download models.
Use `git submodule update --init` on a dedicated authorized dev machine only.

## SaaS adaptation

- Keep upstream application unchanged where possible; call the existing
  private server-side `POST /v1/audio/speech` API through
  `ai_agents.feature2_voicestudio_adapter` (source merged in PR #900).
- Feature2's secure private WAV/review bridge creates **NEEDS_REVIEW** assets,
  which Feature4 can separately authorize for narration; Feature7 must
  independently verify transcribed words and captions. No browser receives
  the upstream root API key or admin controls.
- The Electron shell is useful for local authoring; SaaS customers do not
  need to install it. Upstream's Docker backend can serve its browser UI
  and API, but deploy only after licensing, tenancy/security, cost review
  and safe private networking. The upstream loopback API is anonymous
  by default; never expose it publicly.
- Old Kokoro/Azure/ASR PRs are **NOT** automatically accepted, merged or
  closed just because the upstream source is now pinned. Deduplicate
  source engine logic only after coverage and required tests are preserved.

## License boundary

The upstream VoiceStudio app/backend is **AGPL-3.0-only**. Retain upstream
copyright/license notices. Changes served to network users trigger
corresponding-source obligations; embedding upstream in a proprietary
combined product may require an upstream commercial license.
Model weights are a **separate** issue: VoiceStudio's default OmniVoice
pretrained weights are CC-BY-NC and are not cleared for a commercial SaaS.
The upstream model-license registry currently does not certify a complete
commercial model installation. Do not auto-download those weights, enable
voice cloning, run billed models or ship them to customers.
Obtain revision-specific model/component rights and speaker consent before
actual production use.

**Checkpoint:** source pinned, model NOT downloaded, GPU OFF, no Azure/Supabase/
PROD deployment, no commercial inference, no WineShopPOS modifications.
