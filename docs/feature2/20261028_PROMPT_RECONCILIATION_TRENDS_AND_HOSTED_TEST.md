# Feature #2 follow-through — 2026-10-28

## 1. REAL prior model receipt found: previously ambiguous prompt reservation reconciled

- Only prior protected successful real run: [#40489632633](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40489632633), [artifact 12728895512](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40489632633), ZIP SHA256 **f66f5b2059b6fbdae04cf9197a39db8d92f9d7f88944cc43526e407f0e5dc37a**.
- The artifact's **second genuine Azure provider response** included `request_id=chatcmpl-EdYpLFg94Hc314cO3muUbzZlDTCGe`, `model=gpt-4.1-mini-2025-04-14`, **377 prompt + 313 completion tokens**. Thus the failure was **after a provider response**, not proof of zero billable work. The original text failed editorial acceptance; it is not an approved improved prompt.
- Public South India rates: `(377 * $0.44 + 313 * $1.76)/1,000,000 = $0.00071676`. Ledger rounds *up* to `$0.000717` for the prompt.
- Exact one-row guarded transaction updated **only** `public.shop_ai_spend_reservations.id=6dd7b508-2d39-4560-8f29-dbd96a489758`, shop `f2e20403-0000-4000-8000-000000000403`, operation prompt, prior RESERVED $0.002030, actual NULL, to **SETTLED $0.000717**, with advisory lock, fixed price/token assertion, inactive budget check and exact rowcount=1. Source account/service role security unchanged. Independent hosted SQL read confirms **both** synthetic rows `SETTLED`:
  - campaign_copy **$0.004569** (623 / 2440 tokens)
  - prompt **$0.000717** (377 / 313 tokens)
  - combined **$0.005286** at public price (not an Azure invoice).
- **No additional Azure/model request made.** Account-specific billed rates/discounts remain unverified; exact provider request IDs and original protected ZIP are retained for billing audit.
- Source bug fix: `AzureFeature2PromptLLM` now validates and captures **valid billed usage before editorial content acceptance**, so `Feature2AiActivation.improve` can settle in `finally` even when model text fails review. Invalid or absent usage remains conservative RESERVED and no network retry occurs. Added independent fake-transport no-cost tests in `tests/ai/test_feature2_rejected_prompt_settlement.py`.

## 2. Live original DEV Google Trends collection is running, but no clothing signal right now

- Read-only snapshot audit of exact `jeearzffnjbvghwjjjrf`: **3** daily IN snapshots (2026-10-26, 27, 28); 2026-10-28 observed `05:15 UTC`, expires `2026-10-29 11:15 UTC`, **10 genuine public Google RSS trend entries**, YouTube API source and festival calendar explicitly disabled. `complete=false` accurately reflects disabled sources. All current entries concern finance/other topics, **zero `category=clothing`**, none across all three snapshots.
- Because the real tenant has no source-backed clothing recommendation, no ethically valid hosted clothing draft POST should be made. Do NOT rewrite share-price or finance trends as fashion interest, plant fake rows into the shared collector, silently use the synthetic seven-day Azure sample as a trend, or claim that a generic Google blog article was a recent Google RSS rise.
- Separate independent **fashion editorial evidence**: official [Google India Team, October 1 2026, "Thrifting hits an all-time high on Google Search in India"](https://blog.google/intl/en-in/thrifting-hits-an-all-time-high-on-google-search-in-india/). This is a published background consumer-interest report, **not a fresh Trending Now item**; the current RSS-only live adapter must not ingest it under the wrong source type or bogus 30-hour timestamp. A future reviewed slow-moving source adapter would need its own published-date and expiry contracts.
- Feature #2 API already enforces relevance before a signed shop draft, and every media UUID must be authenticated for that shop.

## 3. Zero-AI-cost *real* DEV signed test (outcome requires separate run evidence)

- Protected workflow `.github/workflows/retail-dev-feature2-free-hosted-smoke.yml` executes `scripts/ops/feature2_free_signed_dev_canary.py` only on exact protected `main` one-shot special release commit (or exact manual authorization code), with secret held in protected DEV environment. It does **not** receive Azure OpenAI keys or turn on Feature2 inference flags.
- Reuses the **one** previously legitimately platform-admin-approved example.invalid synthetic user and fixed test shop; refuses any other account/tenant; checks budget already **disabled**, membership already **inactive**, and no existing test asset. Creates temporary signed user login, reactivates only *that* synthetic OWNER for test, revokes it in finally and re-verifies disabled budget.
- Uploads a first-party **64×64 original Python-generated PNG test image** to existing private `retailgrowth-media` under exact synthetic canonical path, calls genuine signed `register_uploaded_image` as `owned`, and reads it back with owner JWT. This is a rights-owned synthetic TEST FIXTURE and **not** a human/clothing product photo or proof of third-party CC0 rights.
- Invokes signed zero-cost deterministic `improve-prompt`, signed `trend-recommendations`. With no current relevant clothing trend, sends exactly **one** invalid trend POST to assert 409 denial, never makes/claims a saved content DRAFT. If a genuine clothing RSS/YouTube source arrives before the run, only then can it make exactly one signed DRAFT POST and own-JWT readback. No auto-replay after uncertain POST. No publishing/media rendering. Original registered test asset is retained for audit under a revoked test-owner membership unless separately approved cleanup.
- A legitimate **hosted DRAFT persistence PASS** can only be claimed with protected run logs proving the matching signed POST/GET, not offline unit tests or this runbook alone.

## Final handoff

- Done: genuine prompt consumption reconciliation and no-retry future-usage fix, actual hosted trend feed diagnosis, source-only media + signed E2E harness, genuine seven-day TEXT-ONLY model canary.
- Not automatically done: prompt **editorial quality** (still failed model text); relevant **live fashion trend** and real product-photo licensing; actual hosted E2E DRAFT persistence if no relevant source. Do not alter PROD or WineShopPOS. Maintain owner-approved **zero-new-paid-AI** constraint.


## 4. Actual protected signed DEV acceptance — two runs, NOT a full saved draft success

### First real hosted run [#40655976341](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40655976341)

Original tenant-only PNG object upload and `register_uploaded_image` signed RPC succeeded; confirmed a single private file registration. Genuine signed deterministic zero-paid prompt preview succeeded. First `GET /api/shops/{shop_id}/trend-recommendations` returned HTTP503 after around 60 seconds, without a corresponding Supabase `trend_snapshots` REST read. The one signed test OWNER was then revoked and AI budget verified disabled. No DRAFT POST attempted; no saved draft.

### Recovery PR and repeat [#40659456731](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40659456731)

- [PR #460](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/460) merged as `7949eefce38ab49c9c568ad72dd20fa5325f5326`; exact [PR CI #40658964322](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40658964322) **4/4 SUCCESS** and independent [main CI #40659456527](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40659456527) **4/4 SUCCESS**. Source code changes only the synthetic no-paid signed DEV test, not production API handlers: exact existing original PNG and registered metadata preflight+byte hash readback, bounded retry for **GET 503 only**, allowed error-code classification and cleanup armed before ambiguous membership PATCH. The workflow remains protected and one-time.
- Real protected DEV #40659456731: `FEATURE2_HOSTED_SIGNED_EXISTING_ORIGINAL_IMAGE_READBACK=PASS` and `FEATURE2_HOSTED_SIGNED_ZERO_PAID_PROMPT_PREVIEW=PASS`. First genuine signed **GET trends** took roughly 60 seconds and returned HTTP503. `FEATURE2_TRENDS_SAFE_GET_503_RETRY=1`, second GET succeeded, independently confirming hosted Supabase `GET /rest/v1/trend_snapshots` **HTTP200** at `2026-10-28T08:50:00Z`; no verified current clothing trend so `FEATURE2_HOSTED_REAL_FASHION_TREND=NOT_AVAILABLE_FAIL_CLOSED`.
- The test sent **one** invalid-trend signed POST to the live content-drafts API, expecting a trustworthy application `409 TREND_UNAVAILABLE_OR_STALE`. Instead Azure Functions returned **HTTP503 [GATEWAY_OR_UNKNOWN]** after roughly 60 seconds. No POST retry. Supabase edge logs during the attempt recorded no tenant membership/profile/snapshot/draft reads/writes before the cleanup PATCH. Therefore its application-level rejection **was not verified**, and a persisted DRAFT 201/GET **was not tested**.
- Independent after-run hosted Supabase SQL confirms **0** draft rows globally and for synthetic shop; **1** original rights-owned test media asset; test OWNER membership `active=false`; budget `enabled=false`; **0** unsettled AI ledger rows. Existing recorded actual public-price settlements total USD0.005286, not an Azure billing invoice. No new model charges or customer modifications.
- Cross-issue: [#403](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/403) and [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) have the exact diagnostic timings and run links. Do not paper over HTTP503 with 409, declare a hosted persisted draft without 201+signed GET, loosen tenant security, fabricate clothing trends or blindly replay a write.
