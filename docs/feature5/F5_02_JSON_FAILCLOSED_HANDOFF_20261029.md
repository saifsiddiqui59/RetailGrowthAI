# Feature #5 — F5-02 source import fail-closed hardening (2026-10-29)

- Parent: Feature #5 stacked draft PR #465, branch `feat/feature5-a100-safe-control-20261028` at `af4cc21b69382f6b1b45fbd916861569740f7677`.
- Scope: F5-02; the GPU-OFF Feature2 source-only JSON boundary catches malicious deep nesting / `RecursionError` and returns the same non-authorizing rejection as other malformed packets.
- Acceptance tests: `python -m unittest discover -s tests/ai -p 'test_feature5_verify_feature2_export.py'` and four mandatory Part 1 CI jobs on this exact branch head. A CLI negative test requires exit code 2, no stdout, and no Python traceback for 20,000-deep JSON. No inference, paid model, provider or cloud actions.
- Not DONE: original Feature2 PR #551 remains unmerged draft. The existing authentic 15/30/60 Node exporter integration test intentionally skips until the coordinator integrates the exporter. F5-02 remains IN PROGRESS; no generated video, rights approval or Part3 hosted job is asserted.
- Integration: one isolated stacked draft PR targeting existing F5 draft branch. Coordinator owns parent merge to main and fresh postmerge 4/4 validation.
- External gates: `F2-CREATIVE-SOURCE` / Feature #2 source exporter (PR #551); `PART3-WAN22-CONTRACT` / coordinator versioned native lease/credits; `F3-LICENSED-MEDIA` / Feature #3 genuine commercial approved original, and `F5-GPU-AUTHORIZATION` / user budget/legal/one-shot approval. All remain separate.
- Paid GPU OFF; no production, hosted SQL, user samples or WineShopPOS modifications.
