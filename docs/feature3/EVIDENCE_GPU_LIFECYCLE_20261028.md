# Feature3 — verified model evidence and FLUX GPU lifecycle (source only)

Date: 2026-10-28. User direction: continue without waiting for Feature2/4/5; all demonstrations use synthetic local PNGs and mocked Azure CLI. Feature3 GPU remains OFF.

## Evidence adapter

The existing merged Feature3 model registration and signed model-review SQL are reused, not replaced. The new server-only `poster-engine/model_evidence_v1.py` accepts **trusted backend callbacks**, never browser-supplied credentials or public image links. It reads a CURRENT PENDING_REVIEW model (revision 1), its registered same-tenant private `media_assets` row and exact `{shop}/model-library[/platform]/{model_id}/{sha256}.png` byte stream, verifies actual PNG dimensions/type/SHA and blocks EXIF/XMP. It then independently validates per-image synthetic-adult, likeness/component, commercial rights, pose, provenance URL and verified license digest, before calling an **immutable one-time private evidence insert callback**. It requires a positive exact receipt and never reports that mere evidence means the model is approved.

**Critical production dependency:** this is an **injected source boundary**, not an actual live Supabase Storage API or independently licensed-image verifier. The future privileged writer must re-check exact current model/media/revision and prove one immutable insert in the DB transaction; no blind upsert and no automatic retries after uncertain acknowledgements. `retail_private.feature3_model_evidence` from merged migration #542 has not been deployed to hosted RetailGrowthAI DEV. Real original human likeness rights cannot be satisfied by fictional fixtures. Tests use Pillow-made plain adult-geometry PNGs and mocked backend callbacks.

## GPU scripts — do not start yet

Reuses the **existing official pinned FLUX.2 Klein 4B worker** at `poster-engine/flux_t4_container_entrypoint.py`; it does not invent a model implementation or take over Feature5's Wan job. Azure Container Apps **manual job** is preferred because a bounded execution is more appropriate than a continuously running service.

- `scripts/ops/start-feature3-flux-gpu.sh` calls the shared `feature3_flux_gpu.py start`.
- `scripts/ops/stop-feature3-flux-gpu.sh` calls `feature3_flux_gpu.py stop`.
- **Default is DRY_RUN** and makes *zero Azure CLI calls*. It accepts explicit canonical Azure DEV subscription UUID and **existing** Feature3 job name, but no create/provision command.
- Real start additionally needs `--execute`, **both** `RETAIL_FEATURE3_GPU_ENABLED=1` and `RETAIL_FEATURE3_FLUX_START_APPROVED=YES`, a currently verified all-in GPU+CPU+RAM USD/second estimate, `--max-usd` no greater than $2.50 and estimated 900-second full job cost within that limit. This is an admission estimate **not a hard Azure billing cap**; storage and network may still incur costs.
- Before any Azure write, the script verifies the subscription, `rg-retailgrowth-dev`, exact existing `rgai-f5-gpu-canary-eastus` environment, required `project=retailgrowthai/environment=dev/feature=feature3` tags, manual trigger, replica timeout at most 900s, retry=0, one replica/completion and immutable SHA256-pinned container image. Rejects any existing pending/unknown active job execution, but concurrent independent manual operators still require a protected single-operator deployment gate.
- **STOP** is allowed with GPU still disabled (does not require spend approval), but requires the exact named Feature3 execution and verifies the protected existing job first; no blanket stop of Feature5 or the environment. Stopping an execution does not destroy a VM, delete storage, guarantee deletion of billed files or mean the already accrued bill is reversed. Output is `COMMAND_SUBMITTED_NOT_VERIFIED` until separate Azure readback.

### Dry-run examples (safe, no Azure call)

```bash
bash scripts/ops/start-feature3-flux-gpu.sh --subscription <actual-retailgrowth-dev-subscription-uuid> --job <pre-created-feature3-manual-job> --rate-usd-per-sec <verified-current-all-in-rate> --max-usd <approved-per-run-ceiling>
bash scripts/ops/stop-feature3-flux-gpu.sh --subscription <actual-retailgrowth-dev-subscription-uuid> --job <pre-created-feature3-manual-job> --execution <exact-execution-name>
```

The optional `--execute` **must not be used now**. No actual Feature3 GPU job is known to be provisioned, A100/T4 GPU availability and price must be freshly verified, and the user has explicitly said keep GPU disabled. These scripts **cannot create a new job or launch an unknown GPU**. The official pinned model weights / private Azure share are not automatically downloaded or verified by these scripts.

## Pending P0 / P1 / P2 (independent sample inputs first)

1. Implement true protected private Storage credentialed reader and per-image licensing authority; wire the atomic evidence insert to actual service DB. Then signed model import/review from active OWNER/EDITOR with independent platform curator; preserve model revision fencing and test foreign/VIEWER/expired.
2. Exercise Feature2 creative-direction / Feature4 editor / Feature5 private-first-frame interfaces with fictional shop IDs and original dummy media receipts, never requiring the other teams' live outputs. Do not falsely certify cross-feature production integration from mocked tests.
3. Complete private generated output registration, real licensed VTON fidelity, prepaid worker/outbox and retry/revocation gates, real visual QA and Azure issue #249 hosted reliability. Keep no-cost synthetic testing separate from real marketing rights.
4. Operator later provisions and checks an actual FLUX manual job, model weights + image signature, cost and hard idle cleanup, then explicitly approves bounded one-run GPU test **only when Feature3 is ready**. No hosted database migration, GPU activation, PROD, WineShopPOS, external model calls or charges in this branch.

Source test commands used by existing FFmpeg/media CI: `python3 -m unittest discover -s tests/media -p 'test_feature3_model_evidence.py'` and likewise `test_feature3_gpu_lifecycle.py`; all standard four GitHub Actions jobs still required.

## Signed retailer reviewer RPC transport (additional source work)

`azure-functions/campaign-api/feature3_v2_store.py` now includes `review_model` and `revoke_model` transports for the already-merged `public.feature3_review_model` / `public.feature3_revoke_model` SQL RPCs. It accepts the user's *already-verified* JWT and shop IDs, passes six explicit human checks and immutable expected SHA/revision/evidence revision, and verifies a private durable `review_event_id` and revision receipt. It refuses a service-role/publishable key passed as a user token; SQL independently checks `auth.uid()`, active membership, per-image evidence and the curator requirement. There is NO exposed reviewer HTTP endpoint or hosted integration until separately reviewed release authorization. Synthetic tests in `tests/api/test_feature3_model_review_transport.py` mock PostgREST without a network or fake live user session.

**Do not infer token signature verification** from this transport or synthetic JWT text. The existing authenticated API handler must validate the signed user's session and shop before calling it. No GPU work is triggered by approving a model.
