# Feature2 F2-19 / F2-20 — VoiceStudio private binary writer

This PR adds a server-only **no-upsert** private WAV writer using the existing Supabase service-key header helper and private `retailgrowth-media` bucket. It targets exact `<shop_uuid>/voicestudio/<campaign_uuid>/<request_uuid>/{original,render}.wav` keys, validates actual bounded PCM16 WAV and SHA256, requires a prior exact tenant/job `CLAIMED_ONCE` receipt, verifies private origin/ack and never retries ambiguous writes.

This preserves existing Feature2 `create_private_voiceover` callback semantics without implementing another TTS engine. All local tests use synthetic WAV bytes and stub HTTP. There is **no live job route, SQL claim RPC, authoritative rights receipt, readback, signed playback or customer upload** included in this component. The second object may be absent after an uncertain ACK; operator reconciliation (NOT an automatic replay) is required. Do not mark F2-19/F2-20 DONE from this source alone.

Next: bind existing JWT/RLS reader and original-key transaction, register both paths with SQL original SHA + review state and readback, then run two-shop negative tests with signed DEV identities. Keep upstream VoiceStudio API private, default model CC-BY-NC weights OFF, AGPL obligations visible, paid/GPU/PROD/WineShopPOS unchanged.
