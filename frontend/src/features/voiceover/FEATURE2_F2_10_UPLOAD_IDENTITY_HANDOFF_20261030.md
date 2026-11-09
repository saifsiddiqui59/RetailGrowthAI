# Feature #2 F2-10 — private upload File-identity fencing (2026-10-30)

**Status:** IN PROGRESS, source-only stacked on draft #551; not integrated DONE.

Existing voice selector invalidated in-flight private upload responses using tenant, plan, script and file **metadata** (name/size/lastModified). A different local File can carry identical metadata. This scoped change additionally compares the exact submitted File object with the currently selected File through a ref, synchronously refreshed on picker changes; stale success/error/finally responses are ignored. It does not authorize private rights or uploads, or expose local bytes.

Owned changes: `frontend/src/features/voiceover/VoiceoverSelector.jsx`, `voiceover-model.mjs`, `tests/frontend/feature2-voiceover-model.test.mjs`. The pure regression covers same-metadata replacement, source changes, null/empty scope; JSX compile and full CI must still be inspected. This is not a hosted Playwright signed-in test. No credentials, samples, model calls, GPU, cloud mutations, PROD or WineShopPOS.

Coordinator must mount genuine JWT/RLS uploader, verify original asset/rights and signed tenant receipt, accept reviewed PR, and record status only after merged main 4/4 CI. Existing coordinator ISSUE-650 protected ZIP packaging and ISSUE-249 503 remain unresolved; never bypass either. Parent #551 and this PR remain unmerged until coordinator review.
