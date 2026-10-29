# Feature #3 execution tracker — 2026-10-28

**Scope:** Retain existing AI Poster Studio, model catalog, private Supabase media,
FFmpeg renderer and Azure DEV architecture. No duplicated editor, writer or wallet.
Paid GPU remains OFF. Original licensed customer media and third-party marketing
rights remain independent of test fixture approval. Do not modify WineShopPOS.

## Source and infrastructure reality

| Capability | Verified state | Next security/quality release gate |
| --- | --- | --- |
| Model catalog and v2 poster design DB | 24th DEV migration already applied including model catalog/CPU design tables and default-OFF GPU ledger; SQL RLS tests exist | Human authenticated rights review + model registration/revocation, real registered PNG and actual signed retailer |
| Model Storage private key | Previous prefix incompatible with Storage RLS; replacement #518 merged as `7849d24e` from current main, exact [PR CI #40686017512](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40686017512) 4/4 | Real private upload/byte-sha proof and rights-verified model object |
| Fashion image references | #515 merged as `3f9613b8`, exact PR 4/4, and its own post-merge main run #40686101352 passed; source module `poster-engine/fashion_reference_v1.py` | Inject authenticated asset/license/reviewer/product metadata services, real private image; actual feature2/4/5 calling sites |
| Real retailer upload original | #520 merged as `7dd08ebc` after exact [PR CI #40686428683](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40686428683) **4/4 PASS**, correcting distinct Storage object UUID and registered media UUID; post-merge main CI is independent | Signed original from a live OWNER/EDITOR, verified image dimensions/byte SHA, review and revoked/foreign tests |
| Feature3 generated history | #518 adds actual GET-only Azure Functions route; earlier #508 already denies unsupported POST 404, default-off GET 503 | Hosted source release flag, signed GET, per-tenant status and private download tests |
| Licensed model try-on | Existing `ai_providers_v2` has FASHN parser dependency not commercially cleared, no real inference | Legal/technical license approval, authorized capped GPU job, human exact garment comparison, no auto-approval |
| #2/#4/#5 integration | #515 metadata-only handoff and coordinator comments available, not direct model execution | Feature #2 requests approved reference IDs, #4 carries timeline/rights, #5 resolves exact first-frame privately under lease; complete consumer tests |
| GPU, queue and cost | SQL migration live **default OFF**; #493 prepaid bridge, #501 SQL transport merged; queue outbox relay/output callback not complete | Protected outbox dispatcher, one-shot lease fence, authoritative image registration + measured USD ledger, operator-controlled admission |
| Real user signed DEV E2E | 0 approved models, 0 overall models, 0 v2 designs and 0 GPU jobs at latest query; one registered media row is not an approved fashion reference | Legitimately active retailer, approved rights, signed OWNER/EDITOR/VIEWER/foreign/expired tests; no impersonation |
| Release/quality | source CI green where specified; Azure #249 original Flex intermittent 503 remains independently open | Held-off v2 public activation; genuine original & output visual QA, protected DEV deploy and repeated reliability acceptance |

## Execution order (not approval to spend)

### P0

1. **Integrate source-only fixes** #515 (merged), #518 (merged), and
   #520 (retailer original/private object UUID fix, merged after exact 4/4 CI); retire stale conflicted #504/#507 only after their
   replacements are merged. Avoid replacing already integrated #508.
2. **Registered original assets:** signed active owner/EDITOR proof, private
   object and separate media row UUID, actual bytes SHA/dimensions, unexpired
   current membership, licensing evidence and source-owner rights. User-declared
   `media_assets.license_name` alone is not commercial approval. Existing
   revoked synthetic Feature2 test PNG cannot be promoted as a production
   kurti asset.
3. **Model registry and approval/revocation:** authenticated import-first
   curator/retailer review; persisted pose, verified adult synthetic model
   provenance, per-image commercial license+attribution and evidence, approved
   uses and incrementing rights revision. Private model bytes cannot be
   delegated across shop borders just because a shared platform metadata row
   is visible.
4. **Fashion source/consumer adapter:** authoritatively reviewed SKU, garment
   shape, hex colour, neckline, sleeves, length, pattern, embroidery and
   immutable media SHA. #2 only authors shots/prompts; #4 coordinates existing
   Reel timeline; #5 rechecks shop, reference fingerprint, leased claim and
   private bytes; no browser object paths/signed links as inference inputs.
5. **Secure output:** before enabling output downloads, require a truly
   generated, registered same-shop PNG with measured byte SHA, human review,
   current job/attempt lease, existing JWT/private Storage RLS, expiry and
   revoked/foreign cache prevention.
6. **Signed release regression:** actual eligible positive auth; deny VIEWER
   writes, foreign/shop-exchanged, malformed source, revoked rights, changed
   hash, unsigned/expired JWT, non-approved VTON output; keep public GPU POST
   absent and feature flags OFF before reviewing DEV rollout.

### P1

7. **Virtual try-on:** reuse vetted actual provider code and commercially
   cleared dependencies; separately authorize each potential paid
   output. Human review source vs generated result for precise color, print,
   embroidery, sleeve, neck, hem and model identity. A model portrait plus
   garment picture does *not* prove that the model is wearing that SKU.
8. **Worker/orchestrator reliability:** bridge existing SQL reserve/claim/finish
   and prepaid ledger to protected queue outbox, retry/poison reconciliation,
   private output writer+media registration, bounded actual USD and immutable
   claim-token fencing. Never blindly retry uncertain charged inference.
9. **Creative Studio quality:** approved model and product previews, saved
   source-linked designs, private downloads, realistic kurtis in final
   reviewed posters/reels, exact #2 shot direction handed to #4/#5, with
   model outputs reviewed rather than inferred from test pixels.

### P2

10. **Hosted DEV and eventually PROD:** separately approved migration,
    versioned contract, Azure/OIDC release, direct authenticated browser
    testing, real licensed asset provenance, source-level/media/browser tests,
    reliability investigation #249, operator cost and rollback documentation.
    User earlier removed hosted E2E from a *past sprint*, not production safety.

## Hard evidence boundaries

- No tenant-owned real approved fashion model or authorized original kurti
  was available at latest read-only DEV count. A real production try-on
  has **not** been performed. Synthetic Pillow images only prove the
  contract's logic and test data, not likeness, rights or garment fidelity.
- No live GPU job or extra provider inference was started in this sprint.
- A hosted Supabase migration exists for Feature3, but there is **no**
  authenticated approved model-review/import workflow just because
  `feature3_models` has RLS and an `APPROVED` status enum.
- Any source PR CI PASS is distinct from independent merged-main CI and
  a genuine authenticated DEV/production acceptance. Keep blockers open.

## 2026-10-28 latest no-wait checkpoint (supersedes older P0 source-only TODOs)

| Work package | Actual state | Still required before feature completion |
| --- | --- | --- |
| Signed human model approval | #532 review gate + #542 auditable SQL + #544 retailer-JWT RPC transport merged; #555 separate off-by-default HTTP routes **merged** `4642c290` after exact 4/4 [CI #40729549571](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40729549571) | Protected DEV SQL deployment, genuine active retailer/curator and rights evidence, actual signed two-shop E2E |
| Private commercial model evidence | #553 merged as `04dc5427`; exact PR and independent main four-job CI PASS. Current JWT private Storage binary + service-only one-time RPC and tests | Actual permitted commercial photos, independently verified likeness and original license, deployed hosted schemas and per-image proof |
| Offline source tests | Original garment/model/pose/first-frame contracts exist in `fashion_reference_v1.py`; suite uses constructed PNGs | Validate exact Feature2/4/5/7 consuming callers and current rights when integrated; don't call fake bytes production-quality reels |
| Model GPU controls | #544 start/stop scripts dry-run with manual start approval and no automatic create | No start until real feature readiness, quota/provider/cost envelope and protected one-job benchmark |
| Real try-on and output | Provider contract and billing/outbox skeleton exist, disabled | Genuine licensed VTON, visually reviewed kurti fidelity, private output/claim/retry/cost integration, final Reel download and signed DEV validation |
| Reliability | Azure issue #249 remains open | Fix validated 60-second original Function 503 before customer release |

**Current rule:** GPU stays OFF and public model approval is NOT active; zero
approved, rights-verified live fashion models does not satisfy production E2E.
No WineShopPOS or PROD changes.


## 2026-10-28 — Accepted MVP sequencing supersedes earlier real-person and hosted-sign-in TODOs
- **NOW:** Fictional AI-generated **adult** models only; no identifiable real-person portraits or likeness-release procurement in the Feature3 MVP. Authorized garment photographs (not a person's implied endorsement) plus generated model provenance are required. Existing genuine VTON output and garment color, pattern, neckline, sleeves, length and embroidery QA remain unfinished; don't mark synthetic composite/mock output as inferred.
- **FUTURE FINAL INTEGRATION:** Hosted DEV OWNER, EDITOR, VIEWER and independent reviewer/curator **signed-user E2E testing waits until all features (#1, #2, #3, #4, #5, #7 and dependent publishing paths) are developed and available together.** Execute authentic sign-in, uploads, approval/rejection, audit, cross-tenant denial, download and revocation only then under separate deployment approval. For now keep disposable negative SQL, RLS/JWT unit tests, browser mocks, and source verification mandatory.
- **Still protected:** Existing real-person likeness/consent checks must not be falsely satisfied or removed; any future real-person pathway requires its own approval. Seven pending hosted SQL migrations, #249 gateway reliability and costs remain independent gates; no hosted DEV/PROD change or paid inference authorized.
