# Feature #2 fixed task #20 — original WAV private registration revocation race

2026-10-29 · **IN PROGRESS**, source-only, stacked on unified F2 draft #551.

Existing CPU `synthesize_and_stage` previously checked signed current editor and plan *before* private store, then accepted a minimal callback indicating original WAV SHA/private visibility. The backend could revoke an editor or update a creative plan **during private storage**, yet F2 would return a successful registered audio asset. It also did not check the callback's pending-review state.

Source now requires a trusted store reply with `review_state=PENDING_HUMAN_LISTEN_AND_RIGHTS`, `can_publish=false` and `can_dispatch_motion=false`, in addition to matching original private SHA/asset/scope. It then revalidates signed editor and exact authoritative plan **after** the store callback. Existing injected-model positive smoke fixture was updated and a revoked-after-writer mock negative added (no real model inference).

## Coordinator acceptance required
This source-layer check cannot revoke or delete bytes already committed when a permission changes. The real backend must bind durable rights, shop and plan to the **atomic write/lease**, cancel or clean up orphaned private objects, and enforce current rights on every read/download. Genuine Kokoro weights, authorized original WAV, F7 transcript, F4 audio assembly, human rights review, hosted JWT/RLS, protected ZIP #650, Azure #249 and exact-head/postmerge 4/4 remain separately blocked. No GPU, paid inference, production or WineShopPOS changes. Do not count task #20 as DONE.
