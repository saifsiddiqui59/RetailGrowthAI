# Feature5 F5-13 — Azure A100 quota snapshot fail-closed hardening

Status: **IN PROGRESS — source-only, not integrated**. Tracking PR: #763 (draft, stacked on #465); branch `feat/feature5-f5-13-finite-azure-quota-20261030`.

## Scope and verification

- GPU-OFF preflight rejects NaN/Infinity/overflow, booleans, fractional GPU counts, missing used quota, and malformed inventory instead of interpreting them as an eligible free GPU slot.
- Adds offline positive/negative tests in `tests/ai/test_feature5_azure_gpu_preflight.py`; expected targeted command: `python -m unittest tests.ai.test_feature5_azure_gpu_preflight -v` (or `python -m unittest discover -s tests/ai -p 'test_feature5_azure_gpu_preflight.py' -v`).
- **Test execution and exact-head 4/4 CI are pending independent verification.** No successful CI or hosted test is claimed by this handoff.
- This is an inventory safety guard, **not** authorization for an A100 start. No GPU activation, Azure mutation, model inference, DEV/PROD deployment, Supabase writes, media samples, or WineShopPOS changes.

## Coordinator receipt proposal

Original registry ID: `F5-13`. Source status remains `in_progress` until reviewed. Proposed evidence is draft PR #763 and its exact-head CI when available. Do **not** emit a `DONE` event in `coordination/task_progress.json` until accepted merge to main and fresh four-job postmerge CI. Feature5 cannot edit coordinator-owned shared status or canonical documents.

## Remaining F5-13 gate

Immutable, reviewed OCI digest, pinned CUDA/wheel ABI, complete license/SBOM review, and protected runtime approval are still required. Owner: Feature5/Runtime; dependencies: F5-OCI and the human review of actual build/license artifacts. Acceptance: reviewed build digest + ABI + legal/SBOM evidence, with paid GPU OFF until separately authorized.
