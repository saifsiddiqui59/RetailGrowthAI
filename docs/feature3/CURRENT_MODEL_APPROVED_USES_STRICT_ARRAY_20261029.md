# Feature #3 strict model allowed-use authorization — 2026-10-29

## Scoped source reliability fix (F3-02/F3-03/F3-13)
- The original `Feature3GPUJobPlanPreflight._snapshot` accepted `"poster" in approved_uses`, which is true even when an untrusted API/transport maps an array to a plain string or dictionary key. Such values are not reliable proof of explicit per-use approval.
- The current backend read-only model-rights preflight now requires an actual nonempty 1–3 element **list**, all elements exact strings in `poster`, `try_on`, `video_reference`, no duplicates, and the explicit `poster` entry. This is checked before any independent private source-byte/license authority callback.
- CPU/disposable-only Python regressions cover string, mapping, tuple, set, null, missing poster, unknown, duplicate and non-string elements, alongside legitimate one/three-use arrays. All legal/rights/GPU approvals remain external.
- This source patch does not import, approve, or generate a real model; no hosted Supabase migration, provider activation, queue mutation, new model weights, PROD or WineShopPOS changes.

## Coordinator handoff and acceptance
- Branch `feat/feature3-approved-uses-strict-array-rights-20261029` requires four exact-head PR CI jobs, coordinator-owned code review/integration and fresh postmerge main 4/4. This is progress within source-partial F3-02/F3-03/F3-13, not completion of hosted acceptance.
- Original 33-package ledger is already being edited by concurrent PR #683; coordinator should append this handoff only after integration rather than conflicting shared edits.
- **0/33 hosted packages DONE.** F3-LICENSED-MEDIA (independent commercial rights) and F5-GPU-AUTHORIZATION (paid model OFF) are still external blockers; no synthetic fixture is a production approval.
