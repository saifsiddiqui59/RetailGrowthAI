# Feature #2 — offline editorial audit of genuine seven-day Azure copy (2026-10-28)

## Verified scope
Reviewed **all seven day objects** from the originally recorded, private, successfully generated Azure GPT-4.1-mini text-only run [#40489632633](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40489632633), artifact ID `12728895512` (unexpired at review; artifact SHA256 `f66f5b2059b6fbdae04cf9197a39db8d92f9d7f88944cc43526e407f0e5dc37a`). This audit did **not** trigger Azure inference, change Supabase, transmit media, publish material, or inspect an actual retailer's private inventory. The ZIP contains the 7-day text and prior provider usage/status; it does **not** contain the raw failed Prompt Improver completion for independent editorial reconstruction.

The artifact represents fictional **Thread & Loom Studio (Nagpur)**; its `trend_source` explicitly states **no current trend claim**, `media` is **NONE_TEXT_ONLY_NOT_REGISTERED_OR_PUBLISHED**, `review_status` is DRAFT, and `can_publish` is false. Each day contains topic/hook, LinkedIn/Instagram/Facebook/YouTube copy, poster text and 3 × 10-second **text scene directions**. These are instructions, **not generated videos or licensed photographs**.

## Per-day human editorial findings (no copy auto-approved)

| Day | Angle | Main issue to resolve before retailer use |
|---|---|---|
| 1 | Kurti layering | Instagram assumes a **cotton** kurti in available inventory, and Facebook assumes specific Nagpur climate suitability. Model/shrug video scenes are unproduced and rights-unverified. |
| 2 | Straight vs A-line | Generic comparison is viable as educational copy, but personalised **body-type** recommendations and invitations to visit/get expert guidance must reflect retailer-approved services and stock. |
| 3 | Office styling | Blanket assurance that kurtis meet **office dress codes** cannot apply to every workplace; soften to employer-policy-dependent guidance. Depicted office/model scene has no licensed asset. |
| 4 | Choosing fabric | Claims that cotton/blends provide specified **breathability, durability or wrinkle resistance** are material-dependent, not supported by supplied SKU/fabric data; Nagpur-weather suitability needs human review. |
| 5 | Beyond festive use | General styling idea is usable as a DRAFT; offering first-party styling support and depicted wardrobe pieces requires retailer confirmation and owned/cleared media. |
| 6 | Shopping checklist | Generic fabric/fit/care checklist is useful, but **expert advice** claims and an illustrated try-on require verified service capability, permission and actual media. |
| 7 | Local fashion discussion | Low factual-risk invitation, but scene direction to show **people in Nagpur outdoor settings** cannot be treated as existing licensed footage; demographic/individual imagery requires media review. |

**Cross-cutting:** seven angles are distinguishable but templated, often end with the same brand-consultation CTA; localisation repeats the fictional city; no real inventory SKU, pricing, discount, fabric composition, customer review, location or service permission is proven. Scenes are exactly three textual 10-second beats, not proof of video generation. Publishing readiness = **NEEDS HUMAN REVIEW** for all seven days.

## Safe next steps
1. Retain original unmodified private provider artifact for audit; no copying full completion into this public repo.
2. With a genuine active signed retailer, collect approved shop identity, actual product/fabric facts, permitted service/visit CTA, brand tone, media rights and legal constraints before adapting copy. Do not edit the real retailer profile just to pass tests.
3. In offline deterministic editorial mode, remove unverified inventory/fabric/performance/climate claims and conditionalize office policy and service promises; obtain a person's approval before publishing. This does **not** validate the previously rejected paid Prompt Improver response.
4. Keep zero-new-paid-AI controls. The prompt's **billing** is already settled from original provider usage (377/313 tokens; estimated USD0.000717); its **editorial improvement** was rejected and is not accepted.
5. Live clothing trend evidence remains absent in three source-verified India daily snapshots, and hosted source-backed DRAFT POST+GET was **not run**. Protected signed [#40665965219](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40665965219) passed original private PNG and zero-cost prompt but correctly logged `BLOCKED_NO_RELEVANT_LIVE_TREND`; two bounded real GET 503 retries preceded the successful trend response. Do not invent a signal, fabricate a product photo or replay a potentially committed POST.

## Accounting and release boundary
Real previously paid copy: 623 input + 2440 output tokens → USD0.004569 **public-rate ledger settlement**. Real rejected prompt: 377 input + 313 output → USD0.000717 **public-rate ledger settlement**. Combined USD0.005286 is **not an Azure billed invoice**. No additional model request or newly billed provider usage occurred in this review. No DEV/PROD/cloud/resource modification. WineShopPOS untouched.
