# Feature2 original F2-07/F2-11/F2-17 source recovery — 2026-11-15

Extract five **unchanged** original Git blobs from conflicted Feature2 parent #551 head `d80d6b50705323290c4b214bf2f006eacef1ef33`:

- `src/ai_agents/feature2_voice_quality.py` (`aaa66fe01591a3f6e89051d53530737ef9ebb673`) — original in-memory PCM, objective audio checks, signed Feature7 transcript receipt consumer and **lazy** optional offline OpenPronounce gating
- `src/ai_agents/feature2_pronunciation_dictionary.py` (`8122e8bb04740ee5b6b4ec42f75cb053000e1979`) — editor-approval callback, tenant-scoped pronunciation source corrections
- `src/ai_agents/feature2_audio_evidence.py` (`ff1100207186b9e98a4e3267c2fd846a06aa4302`) — private WAV byte and plan hash evidence, never proof of human speech
- `tests/test_feature2_voice_quality.py` (`14685972a926d4194bf9176f7aed20f3d4e999fb`) — synthetic PCM/ASR and pronunciation negative tests
- `tests/test_feature2_audio_evidence.py` (`f3118775ffcc0f301a38f32cadbd2695b91b3e66`) — in-memory synthetic WAV ownership/status negatives

Reuses current-main Creative Director and newer VoiceStudio work **without activating or importing any paid TTS, STT, OpenPronounce checkpoint or audio endpoint**. Word error rate and PCM diagnostics are not approval that an audible voice says the text, nor real commercial speech quality. Browser claims and editable dictionaries do not grant tenant roles or license sounds. Signed source owners, audio SHA-256, human editorial approval and legal commercial rights must all be verified by independent hosted readers, not inferred from synthetic fixtures.

Release blockers: actual Feature7 licensed ASR/original WAV and worker receipts, current shop JWT/RLS membership and private WAV objects, verified commercial model licenses and F4 final audio/renderer approval. F2-07/F2-11 original source scopes may remain marked source-complete; live F2-17, F2-20, F2-23 and F2-35 remain open until hosted proofs. No Azure/Supabase/SQL mutation, model downloads, GPU, paid provider/API calls, PROD or WineShopPOS.
