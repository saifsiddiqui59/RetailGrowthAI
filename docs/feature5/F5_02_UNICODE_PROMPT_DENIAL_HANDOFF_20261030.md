# Feature #5 F5-02 — escaped-surrogate editorial prompt denial

Status: **IN PROGRESS — source-only, not integrated DONE**.

## Owned source change
- On a dedicated branch stacked on existing Feature5 F5-02 PR #785, reject escaped lone UTF-16 surrogate code units in the original Feature2 motion prompt with `WanCompatibilityError`, rather than letting `UnicodeEncodeError` escape the consumer trust boundary.
- New isolated negative tests cover four invalid surrogate code units in the direct Python bridge, bounded JSON importer and CLI; the CLI must return code 2, no receipt on stdout, no traceback. Positive synthetic 15/30/60 contracts remain non-authorizing.
- This addresses a separate malformed-Unicode failure mode; do not duplicate or replace the existing F5-02 timing/camera fixes in PR #785.

## Acceptance and evidence
- Source: `feature5_motion/feature2_storyboard_bridge.py`.
- Tests: `tests/ai/test_feature5_f2_unicode_prompt_denial.py`.
- Targeted command: `python -m unittest discover -s tests/ai -p 'test_feature5_f2_unicode_prompt_denial.py'`.
- Targeted and exact-head four-job CI: **not verified yet** at handoff creation. Coordinator must inspect PR head, run CI, and integrate in dependency order; then require fresh main four-job CI.
- Task manager: propose a source-progress note for existing **F5-02** only; **do not** mark integrated DONE or alter `coordination/task_progress.json` without coordinator acceptance.

## Remaining dependency gates
- **F2-CREATIVE-SOURCE / F2#551** — Feature2 + coordinator: integrate original pinned MIT Creative Director exporter and execute authentic 15/30/60 Node stdout plus negative tamper tests; fixtures do not satisfy this.
- **F3-LICENSED-MEDIA** — Feature3 + rights reviewer: current tenant-private model/garment originals, independently reviewed commercial/likeness rights and revocation readback.
- **PART3-WAN22-CONTRACT** — Part3 + coordinator: signed JWT/RLS, lease/credit/unknown-ACK and private output proof.
- **F5-GPU-APPROVAL** — user/operator: separate bounded cost/legal/teardown approval before any actual model inference.

GPU OFF; no cloud, paid inference, PROD, SQL, test-account login, samples, or WineShopPOS changes. No customer or model output was generated.
