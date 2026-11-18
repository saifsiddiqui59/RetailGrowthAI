# Feature #5 — One consolidated GPU-OFF source batch (2026-10-30)

## Faster review, same safety gates

Six existing Feature5 draft PRs passed exact-head full four-job Actions independently, but running and merging each tiny PR repeats setup, review and CI. This **one coherent source batch** applies the exact reviewed blobs of all six, with **21 unique changed paths and no conflicts**; it adds only this handoff and consolidates existing Feature5 ledger/work-log evidence. Review/merge **this batch instead of merging all six siblings one by one**, not both.

| Original F5 task | Source PRs | Exact-head successful 4-job CI | Status |
|---|---|---|---|
| F5-02 | #685 | #40955154226 | IN PROGRESS — authentic Feature2 exporter #551 still unmerged |
| F5-13 | #688, #694, #698 | #40955476329, #40960751923, #40960990463 | IN PROGRESS — real OCI/ABI/CUDA legal/SBOM unverified |
| F5-14 | #691 | #40955817353 | IN PROGRESS — protected original Wan checkpoint full byte hash unverified |
| F5-17 | #702 | #40961284049 | BLOCKED — genuine Wan clip, approved media, signed human QA missing |

**Canonical Feature5 release count: 0/22 integrated DONE, 3 IN PROGRESS, 19 BLOCKED.** Source-only negative tests do not create actual Wan inference output or commercial approvals.

## Revised operating cadence for subsequent batches

1. Take 3–6 independent eligible Feature5 source tasks at once, using their existing original IDs. Avoid one branch/PR/full Actions cycle per tiny fix. Review all open PRs and current main before claiming new work; preserve truly completed code.
2. Only a *real* coding worker with globally atomic claims may count against the 10 parallel coding slots. The GitHub coordinator currently produces **advisory** candidates, not 10 workers. This PR consolidates individually verified independent source branches; it is not a claim of 10 simultaneous agents.
3. During development, use fast **targeted** offline unit, security/negative and cross-feature contract tests. At the coherent batch review boundary, run **one mandatory exact-head 4-job** Actions run (Python/uv, FFmpeg, frontend/Playwright, disposable Supabase). After coordinator merge to main, require fresh four-job postmerge CI. Never postpone security gates until all 22 tasks are complete; 19 tasks currently require external approvals.
4. Diagnose and fix recoverable failures (max two safe additional retries, then defer; two more only after all eligible first-pass tasks). Never rerun ambiguous payment, AI provider POST/ACK, permission denials, unapproved inference or insecure writes.
5. Coordinator selects this batch as the **single source integration route**, reconciles #685/#688/#691/#694/#698/#702, updates shared task_progress and continuity docs, and promotes the parent #465 chain after its own approvals. Full four-job batch CI must pass before source acceptance; source acceptance itself is not integrated DONE.

## Shared inputs already usable

- **Feature3** `F3-ORIGINAL-HANDOFF`, merged PR #630: genuine source-verified original MIT OpenVTO **demo** avatar and *separate* garment bytes, provenance and offline private-image pipeline. Reuse existing F5 CPU/FFmpeg tests; do not mislabel as person wearing a customer's garment or production AI output.
- **Feature2** `F2-CREATIVE-SOURCE`, PR #551: original 15/30/60 editor exporter is still **draft/unmerged**. F5 source-schema and negative tests work offline, but authentic Node exporter E2E is not passed without integration.
- **Part3** `PART3-WAN22-CONTRACT`, draft PR #125: signed tenant, one-charge lease, native 704x1280/121f 24fps, private storage and cost settlement are not yet approved.
- **Feature4** `F4-EDITOR-SOURCE`, draft PR #322: editor contracts can be checked with labeled fixtures, but reviewed licensed final video is not proved.
- **Operator** `F5-GPU-AUTHORIZATION` and Azure #249: user-approved licensed model/runtime, spend ceiling, safe shutdown, hosted reliability are absent. No GPU, paid inference, hosted SQL, PROD, samples or WineShopPOS.

Full CI must test the **combined tree**; previously green sibling CI cannot substitute for the combined exact-head run.
