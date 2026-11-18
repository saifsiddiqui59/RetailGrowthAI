# Feature #3 original F3-07 / F3-13 — immutable private media commit receipt attempt fence

**Source-only, GPU OFF.** This code does not call FLUX, Wan, Azure, Supabase, any paid service or a deployed database.

## Exact original task coverage
- **F3-07**: Private generated PNG registration and SQL CAS evidence. The service-only `PrivateOutputRegistrar` formerly accepted a forged commit acknowledgement with `attempt=True` or `attempt=1.0`, because Python compares either as equal to integer `1`.
- **F3-13**: Negative authorization/unknown ACK regressions. Add untrusted receipt cases `True`, `1.0`, `"1"`, `0`, `2`, `None`, `False`, together with metadata attempt negative cases. The success case keeps exactly one integer attempt.

## Behavior and non-retry boundary
- Reject any returned CAS receipt whose `attempt` is not genuinely `int` or is not exactly `1`, even when all source SHA, claim token, original image and object path values match.
- A rejected post-commit receipt represents **AMBIGUOUS DB OUTCOME**. Never attempt a second commit or quarantine/delete the staged PNG automatically; a human operator reconciles it.
- Existing `_metadata` intake already enforces integer attempt. New tests prove both input and post-commit sides fail closed.
- Scoped code: `poster-engine/feature3_private_output_v1.py`; offline tests: `tests/media/test_feature3_private_output.py`.

## Review, test and original package state
- Targeted: `python -m unittest discover -s tests/media -p 'test_feature3_private_output.py'`; required four-job final-head Part 1 CI on this PR; independent private-output/financial review before merge, then fresh `main` four-job CI.
- F3-07 remains **source partial**, not DONE until genuine immutable hosted output, signed user rights/lease, approved model/garment/license and real provider/financial evidence. F3-13 also remains hosted incomplete until real signed negative tests. A success in offline fixtures is not commercial approval.
- Do not duplicate prior merged Wave A/B source work; original source-component receipt tracker is proposed in #860. This PR addresses a genuinely new typed **post-commit ACK** check (separate from already-integrated F3-06 operator evidence typed-attempt guard in #834).
- No sample, GPU, paid image generation, PROD, hosted SQL, user accounts, WineShopPOS or cloud deployment.

## Same coherent F3-07/F3-13 batch: runtime lease + CAS type fences
- The composed `Feature3PrivateGPUWorker._validate_claim` prepaid reservation check also used Python `== 1` equality: mocked/corrupt `attempt=True` and `1.0` passed. It now requires a genuine Python integer, matching the one-shot expected attempt, **before staging any Storage bytes**.
- The runtime `_commit` composition similarly requires a strict integer post-SQL CAS receipt before returning it to the registrar. Failure after SQL commit is **ambiguous**, with no automatic delete or replay.
- Added `tests/media/test_feature3_private_gpu_runtime.py` negative matrices for boolean/float/string/None/wrong attempt: pre-stage denial performs no HTTP POST, and a postcommit denial retains staged private bytes for manual reconciliation and never calls `finish` or DELETE.
- This code is not a live worker activation, not a direct payment/SQL authorizer or a generated output. F3-07 and F3-13 hosted task completion remains blocked. Both runtime tests and private-output tests must pass exact-head 4/4 before review.

## 2026-11-02 — original F3-07/F3-13 one-shot claim + late funding recheck (same PR #861)
- Before any paid provider call, `PrepaidGPUJobCallbacks.claim` and `.reserve` now require a **genuine integer** attempt in the exact SQL claim and prepaid reservation. Python dictionary equality previously allowed `attempt=True` or `1.0` to equal `1`, even when the token/shop/job matched. `tests/api/test_feature3_prepaid_gpu_bridge.py` uses a no-runner assertion for both negative paths; no private output or metering is accepted.
- After inference but **before any private Storage POST**, the composed `Feature3PrivateGPUWorker._validate_claim` also validates the *fresh* SQL reservation UUID and positive finite budget-bounded amount. It no longer trusts a row with the correct shop/job/token/attempt but invalid, zero, revoked, NaN or above-cap funding. `tests/media/test_feature3_private_gpu_runtime.py` asserts no Storage method or SQL commit is called for malformed late lease data.
- These are offline synthetic fixtures. The checks are **not** an independent guarantee that a valid changed reservation ID belongs to the original claim: production SQL still MUST atomically enforce current one-shot lease, reserved funds, source rights and immutable output CAS. No GPU, provider, cloud, hosted SQL, PROD or WineShopPOS changes.
- Targeted commands: `python -m unittest discover -s tests/api -p 'test_feature3_prepaid_gpu_bridge.py'` and `python -m unittest discover -s tests/media -p 'test_feature3_private_gpu_runtime.py'`. Run all four mandatory Part 1 CI jobs on the **new exact head** before any merge. **Review gate:** independent private-output + financial/lease reviewer, then fresh postmerge main 4/4. F3-07 and F3-13 remain source-partial/hosted-blocked; never append DONE from this PR alone.

## 2026-11-02 — F3-07 paid execution entry-point gate (same existing PR #861)
- `PrepaidGPUJobCallbacks.execute` now requires the **incoming** `InferenceJob.attempt` to be an actual Python `int` equal to 1 before calling `provider.status()`, avoiding Python's `True == 1` and `1.0 == 1` ambiguity. This is an additional pre-provider gate; the downstream provider still performs its own `job.validate`.
- The separately injected provider status must be an actual `dict` with `enabled is True`, never a truthy string, integer, list, or missing key. This prevents malformed injected adapters from reaching SQL claim or paid runner through the bridge's preflight. It does **not** grant provider activation or replace the provider's own cost/license checks.
- New offline negative tests in `tests/api/test_feature3_prepaid_gpu_bridge.py` prove malformed attempts do not even query status, and malformed paid statuses do not claim, execute, reserve, write or settle. Existing valid one-shot synthetic path remains exercised by prior tests.
- **F3-07 and F3-13 remain source-partial / hosted-blocked.** Review needs independent private-output and financial authorization reviewer; mandatory final-head Part 1 CI 4/4 and, only after reviewed eligible merge, fresh main 4/4. No actual GPU/provider invocation, cloud deployment, hosted SQL, PROD or WineShopPOS mutation.

## 2026-11-02 — F3-07/F3-13 late reservation identity and amount fence
- The bridge now reads the authoritative existing SQL reservation again **after inference and before calling the private output writer**, and requires exact same canonical UUIDv4 reservation ID, genuine integer attempt, shop/job/claim token and unchanged bounded reserved amount from the pre-inference snapshot. A different valid reservation ID with the same job and cost is no longer accepted.
- Offline regressions cover late ID swap, reduced/increased reserved amount, forged attempt and changed token. The composed worker test asserts no private Storage POST/GET, SQL output commit or settlement after a late swap. No new reservation or retry is created. A late read denial is conservative: leave any paid inference outcome for independent financial reconciliation; never report hosted success.
- Source changes are confined to this existing **PR #861**: `poster-engine/feature3_gpu_prepaid_bridge.py`, `tests/api/test_feature3_prepaid_gpu_bridge.py`, and `tests/media/test_feature3_private_gpu_runtime.py`. Targeted tests are those two unittest modules; mandatory exact-final-head **four-job** CI remains the acceptance gate. Independent private-media/financial/lease reviewer required before merge, followed by fresh main 4/4. No GPU, hosted SQL, PROD, paid inference, rights approval or WineShopPOS.
- **Original status remains:** F3-07 source-partial and F3-13 source-partial, 0/33 hosted accepted. This is an offline source hardening checkpoint, not a new task completion or permission to activate GPU.

## 2026-11-03 — F3-07/F3-13 complete generated PNG decode before private CAS
- Continued existing PR #861, original F3-07/F3-13. A valid PNG chunk CRC and `Image.verify()` do not guarantee the compressed IDAT pixel stream can decode. A synthetic CRC-correct PNG with corrupted zlib header passed `verify()` but failed `load()`, potentially allowing an unusable SHA-matching generated PNG to be staged and registered.
- `_verified_png` now reopens and fully decodes the image before lease/rights checks, private staging or DB CAS. New deterministic regression for a CRC-recomputed malformed IDAT requires zero claim, rights, stage, commit or quarantine calls, despite the metadata SHA matching the forged bytes. A valid synthetic PNG success remains covered.
- Run targeted `python -m unittest discover -s tests/media -p "test_feature3_private_output.py"` and exact-final-head four-job Part 1 CI. Independent private-output/financial/security review remains mandatory before safe main merge and fresh main 4/4. Source partial, hosted 0/33; no GPU/paid inference, hosted SQL, PROD, real media or WineShopPOS changes.
