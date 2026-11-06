# Feature #2 F2-09 / F2-15: CPU Kokoro safety and benchmark integrity

Date 2026-10-30. Original ledger tasks #9 (CPU startup/cache) and #15 (time/RSS benchmark) remain **IN PROGRESS**, source-only.

One coherent offline batch hardens verified Kokoro model cache hashing to a single no-follow regular-file descriptor (detect symlink substitution before hashing) and maps missing operator cache to a bounded error. The model runner still requires an **operator-enforced immutable cache while the upstream ONNX loader opens paths**; no claim of fully transactional filesystem immutability is made.

Benchmark receipt verification now requires full PCM16 mono 24kHz WAV framing, actual accessible sample frames and matching measured duration. It also refuses test-synthesizer receipts claiming publishing, verified speech/transcripts or word timestamps. Zero billable calls remain mandatory; no mock is promoted to real model proof.

Injected negative fixtures test attempted model-path symlink replacement, unavailable cache, fake RIFF, forged duration, claimed publishing, transcript and fabricated timing. Existing waveform and CLI positive tests are retained. This is offline source QA, **not** a genuine CPU speed/memory/cost measurement or a real approved spoken result.

Coordinator must reconcile the owner draft branch with unified #551 and sibling #684/#697/#700/#704/#780/#807/#809, protect #650 ZIP package and Azure #249 reliability, verify 4/4 exact-head and fresh postmerge main 4/4. GPU OFF, paid inference disabled, no customer samples, hosted writes, PROD or WineShopPOS.
