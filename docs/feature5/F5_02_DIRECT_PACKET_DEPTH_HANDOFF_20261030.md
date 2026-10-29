# Feature5 F5-02 — Direct Feature2 packet recursion denial (2026-10-30)

- **Task:** F5-02 (in progress; not integrated DONE).
- **Base:** parent Feature5 branch `feat/feature5-a100-safe-control-20261028` at `af4cc21b69382f6b1b45fbd916861569740f7677`; parent PR #465.
- **Owned changes:** `feature5_motion/feature2_storyboard_bridge.py` now catches `RecursionError` and `OverflowError` when digesting untrusted direct Python packets. This is distinct from PR #685's `verify_feature2_export.py` stdin JSON decoder hardening.
- **Negative regressions:** `tests/ai/test_feature5_f2_direct_packet_depth_denial.py` exercises deeply nested, cyclic and nonfinite extra editorial metadata; 15/30/60s synthetic valid packets remain explicitly not provider/publishing approved.
- **Verification requested:** `python -m unittest discover -s tests/ai -p test_feature5_f2_direct_packet_depth_denial.py`, plus exact-head four-job GitHub CI. No test is claimed passed until inspected.
- **Dependency F2-CREATIVE-SOURCE:** Feature2 / coordinator; requires original PR #551 exporter runnable from the reviewed integrated source and its exact stdout 15/30/60s, including tamper negatives. The synthetic fixtures here are NOT original exporter evidence.
- **Dependency F3-LICENSED-MEDIA:** Feature3 / rights reviewer; requires current tenant-private, approved garment/model original bytes, signed rights and revocation readback. No fake approval.
- **Dependency PART3-WAN22-CONTRACT:** Part3 / coordinator; requires JWT/RLS, durable claim/credit, idempotency and single-use paid provider execution, unknown-ACK reconciliation and private output.
- **GPU/paid inference:** OFF. No real Wan inference, media samples, DEV/PROD deployment, hosted SQL, user credential use or WineShopPOS modifications.
- **Task-manager proposal:** Keep F5-02 `in_progress`; do not create an `integrated_done` event. Coordinator to review PR, integrate accepted source, and run fresh main 4/4 CI before changing canonical counts.
