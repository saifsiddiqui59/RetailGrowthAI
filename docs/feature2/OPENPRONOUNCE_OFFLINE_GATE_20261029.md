# Feature #2 OpenPronounce optional CPU reviewer (source-only, 2026-10-29)

**Current state: no real local OpenPronounce inference or CPU benchmark recorded.** Feature7 Faster-Whisper owns real original-WAV speech-to-text. OpenPronounce is a separate optional English-phoneme reviewer; its scores are heuristics, not brand pronunciation proof or permission to replace human review.

## Real existing dependency (not an invented service)

- [Halleck45/OpenPronounce](https://github.com/Halleck45/OpenPronounce), PyPI `openpronounce==0.3.0`, upstream MIT license. The project has an actual exported `openpronounce.compare_audio_with_text(sound, expected_script, lang="en")` function. Source audited on 2026-10-29.
- Upstream dependency examples: [`facebook/wav2vec2-large-960h`](https://huggingface.co/facebook/wav2vec2-large-960h) for English ASR and [`facebook/wav2vec2-lv-60-espeak-cv-ft`](https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft) for phonemes (model cards list Apache-2.0). Each checkpoint is approximately 1.26 GB; **do not package 2.5 GB of models** in Azure Functions, production ZIP, frontend or container build by default. Independent exact Git SHA, model file hashes and voice licensing require operator pinning before a real run.
- [Upstream README](https://github.com/Halleck45/OpenPronounce#readme) explicitly says English is the calibrated language; multilingual confidence does **not** establish accuracy for Hindi, Marathi or accented Indian retailer brand names. It warns that short words may be falsely flagged; do not auto-replace TTS voices based on a score.
- Upstream defaults to **gTTS reference audio**, which can make a **network call**. The Feature2 wrapper requires explicit `OPENPRONOUNCE_TTS=piper` or `kokoro`, `OPENPRONOUNCE_DEVICE=cpu`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and an operator assertion `RETAIL_F2_REFERENCE_AUDIO_PRELOADED=true` before it attempts a real import/inference. The operator must independently verify that all reference voice, model and tokenizer artifacts are present and licensed. Otherwise it fails closed.
- Existing `ai-agents/src/ai_agents/feature2_voice_quality.py::run_openpronounce_lazy` invokes actual upstream code only after the above gates, an approved English script and bounded private PCM16 audio. It now passes the result through `project_offline_openpronounce_review`, which refuses malformed/excessive errors, fake probabilities, invalid IPA, injection markup and unbounded scores. It emits only word-level *possible* pronunciation errors and never leaks raw transcripts, arrays, JWT or audio bytes.
- Source tests simulate the result **without** downloading or invoking the multi-gigabyte models; those tests **do not count as a genuine pronunciation benchmark**. They are tests of fail-closed parsing, network-disabled configuration and reviewer-only semantics.

## Remaining task #18 gates

1. Operator must approve exact pinned `openpronounce` revision and the **two** original model checkpoint hashes, reference TTS files and license notices; preload in an isolated private offline CPU worker with memory limits. Never automatically download in authenticated HTTP functions.
2. Measure actual cold and warm CPU time/RSS on a specified target machine for fixed synthetic English phrases; do not infer a universal cost or phoneme accuracy from source tests.
3. Compare **real registered original-WAV** audio against an exact current retailer-approved script and human reference. Feature7 original-byte hashes, tenant job authorization, fresh rights and current editor/reviewer decision must remain separate.
4. Human-review false positives for English/Indian-English brand names; keep unsupported Hindi/Marathi spelling and spoken-correction flags separate and labeled unknown. Only a reviewed pronunciation dictionary can propose a new TTS retake; fresh ASR and F4 listening required.
5. Coordinator must resolve [P0 package issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) before integrating this source branch; heavyweight `torch`, checkpoints and offline reference audio do not belong in the existing Functions ZIP.

**No inference performed, no customer WAV inspected, no paid APIs, no PROD or WineShopPOS changes.** Task #18 remains IN_PROGRESS after parser/CPU gates but genuine checkpoint benchmark remains blocked on independently verified files and compute.
