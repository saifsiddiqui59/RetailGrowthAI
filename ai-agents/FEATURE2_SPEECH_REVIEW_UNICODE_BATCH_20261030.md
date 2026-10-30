# Feature2 signed speech-review Unicode safety batch (2026-10-30)

Original task IDs **F2-17, F2-18 and F2-26**: source IN PROGRESS, not DONE.

The single existing Feature2 voice quality source module now declines transcription token text and English phoneme review hints containing Unicode bidi override/isolate, zero-width separators, Unicode paragraph breaks or active markup. Independently signed human transcript WER references also receive the same bounded safety check. Legitimate Hindi/Marathi combining marks and Unicode ZWJ/ZWNJ joiners remain eligible in whole word tokens. We intentionally do not remove suspicious characters and then silently call the words verified; the source fails closed.

Existing mocked Feature7 receipt fixtures now include synthetically **re-signed** transcripts to ensure a matching HMAC alone never certifies a safe reviewer display. An additional set of fake quality and OpenPronounce negative tests covers unsafe display, with a positive Indic conjunct token test. All tests are offline; no actual STT/ASR, real human listening, deployed model/rights, or licensed source media is implied.

One coherent branch change invokes full four-job CI at the batch boundary. No isolated paid GPU, provider inference, PROD or WineShopPOS, and no user-visible samples. Coordinator owns real audio source rights and output proofs, F7 signed original-WAV worker, issue #650 immutable Functions ZIP, issue #249 Azure HTTP 503, merge to latest main and fresh postmerge 4/4. 
