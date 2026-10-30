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
- Invokes signed zero-cost deterministic `improve-prompt`, signed `trend-recommendations`. With no current relevant clothing trend, makes **no** draft POST and explicitly reports BLOCKED_NO_RELEVANT_LIVE_TREND; no persisted DRAFT is claimed. If a genuine clothing RSS/YouTube source arrives before the run, only then can it make exactly one signed DRAFT POST and own-JWT readback. No auto-replay after uncertain POST. No publishing/media rendering. Original registered test asset is retained for audit under a revoked test-owner membership unless separately approved cleanup.
- A legitimate **hosted DRAFT persistence PASS** can only be claimed with protected run logs proving the matching signed POST/GET, not offline unit tests or this runbook alone.

## Final handoff

- Done: genuine prompt consumption reconciliation and no-retry future-usage fix, actual hosted trend feed diagnosis, source-only media + signed E2E harness, genuine seven-day TEXT-ONLY model canary.
- Not automatically done: prompt **editorial quality** (still failed model text); relevant **live fashion trend** and real product-photo licensing; actual hosted E2E DRAFT persistence if no relevant source. Do not alter PROD or WineShopPOS. Maintain owner-approved **zero-new-paid-AI** constraint.

## 2026-10-28 — protected actual hosted signed continuation: partial acceptance PASS, persisted DRAFT blocked

- [PR #481](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/481) merged to main `83a9ac055c710b4c040de1ca2e1075852340abd3`. Exact branch [CI #40665557947](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40665557947) passed all four jobs. Stale duplicate conflict PR #477 was closed without merging.
- [Protected DEV hosted #40665965219](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40665965219) **SUCCESS** with genuine signed JWT and exact previously approved synthetic shop:
  - `FEATURE2_HOSTED_SIGNED_EXISTING_ORIGINAL_IMAGE_READBACK=PASS` and `FEATURE2_HOSTED_SIGNED_ORIGINAL_IMAGE_UPLOAD_AND_REGISTRATION=PASS` (private first-party-owned original PNG, not retailer photograph).
  - `FEATURE2_HOSTED_SIGNED_ZERO_PAID_PROMPT_PREVIEW=PASS` (deterministic preview, not another GPT call).
  - `FEATURE2_TRENDS_SAFE_GET_503_RETRY=1/2` (actual Azure HTTP 503 during bounded GET retries); later real source-backed response had no clothing item.
  - `FEATURE2_HOSTED_REAL_FASHION_TREND=NOT_AVAILABLE_FAIL_CLOSED`, `FEATURE2_HOSTED_DRAFT_SAVE=BLOCKED_NO_RELEVANT_LIVE_TREND`, `FEATURE2_HOSTED_UNVERIFIED_TREND_POST=SKIPPED_NO_FABRICATED_ID`.
  - `FEATURE2_HOSTED_TEST_MEMBERSHIP_REVOKED=PASS`, `FEATURE2_HOSTED_AI_BUDGET_NEVER_ENABLED=PASS`.
- Independently verified in exact Supabase DEV: **0 DRAFT records**, 1 rights-owned isolated synthetic media asset, 0 active test memberships, 0 enabled budgets. 2026-10-26/27/28 Google RSS daily snapshots each had 10 real trends and **zero clothing**. Neither positive hosted DRAFT save/readback nor a real commercially cleared clothing product photograph is proven. Do not represent the zero-cost workflow's SUCCESS as full hosted E2E acceptance.
- Ledger independently remains **two SETTLED rows**, campaign `$0.004569` and prompt `$0.000717` = **$0.005286 public-rate estimate**, not Azure billed invoice. No paid new call.
- Remaining next step is genuine real fashion trend + product-media evidence and a successful signed DRAFT POST/GET when API reliability permits; never fake signals or bypass tenant/ROOT gating. Main CI for the release was superseded by adjacent concurrent merges; branch 4/4 and protected hosted run separately independently verified.


## 2026-10-28 — original text artifact editorial audit
- Independently read all seven genuine provider-generated text days from artifact #12728895512 **offline**; no paid request, SQL, hosted re-run or licensed-media assumptions. Per-day unsupported claims and human-review checklist: [20261028_REAL_AZURE_EDITORIAL_REVIEW.md](20261028_REAL_AZURE_EDITORIAL_REVIEW.md).
- Provider returned 7 x 3 textual 10-second scene directions, not video footage. Fabric stock/technical properties, blanket workplace dress-code claims, retailer service/location promises and visual rights need confirmation. **All outputs remain DRAFT/NEEDS HUMAN REVIEW.** Prompt settlement complete, prompt editorial result still rejected. Live fashion trend and hosted positive signed DRAFT save/readback still blocked.
