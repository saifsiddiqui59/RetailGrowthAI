# Testing Chat — evidence-based improvement priorities

## Implemented source behavior
`trace-guidance.mjs` classifies each of the six current feature identifiers using only signed-retailer **browser-observed** stage events and 1–5 human quality reviews. It returns one investigation summary per feature, prioritizing the earliest reported execution FAIL, then UNKNOWN (never replay a possibly committed POST), then outputs with a completed PASS and a poor human rating of 1–2/5. PASS without a human rating triggers review advice but is **not** a failed operation or low quality assertion. Explicit NOT_RUN and completely unobserved features do not enter the failure/quality shortlist.

Suggestions are deterministic and conservative: no model calls, no fabricated model/worker invocation, no new telemetry write or provider cost. The advice links each feature to the useful next check (Feature #2 copy/offer and storyboard; Part1 F4 Reel timing/audio; Feature #3 garment fidelity; Feature #5 temporal coherence; Feature #7 editing; Feature #1 permissions) while preserving its uncertainty. A low human score does **not** change an API execution PASS into FAIL.

The existing Testing Chat shows **What to improve next**, a short prioritized investigation list, and an expandable assessment for all six features. The user-triggered JSON export now includes a clearly labeled suggestions block alongside browser receipts and separately stored private backend RPC evidence; it never upgrades a client event into a trusted worker span.

## Correctness regression
Before this change, the pure diagnostic helper could mark **Feature #2 NOT_RUN** in a prompt-only test: `prompt-improvement PASS` was followed by an optional `campaign-planning NOT_RUN`, and the last status overwrote the earlier completed prompt. Feature roll-ups and history counts now retain PASS when some actual substep completed and only optional substeps were skipped; a reported FAIL/UNKNOWN still takes precedence.

Node regression tests cover first-failure priority, UNKNOWN #249 safety, low-output-quality independent from technical success, forged low review for an unrun feature, empty traces, and completed prompt followed by skipped campaign. Mocked Chromium exercises the new guidance panel and low-quality F4 scenario. All tests are offline; this does not constitute a signed hosted RetailGrowthAI DEV run.

## Release gates unchanged
DEV browser-trace tables and private worker ledger are separate staged SQL candidates, not currently installed per earlier read-only inspection. The signed backend read RPC and worker sink remain source-only; live two-tenant permissions, real worker spans, approved assets and Azure #249 remain external dependencies. F3/F5/F7 are **NOT_RUN** until they actually execute under approved cost/rights controls. Do not deploy production, charge the provider, publish social posts, bypass the migration inventory, or modify WineShopPOS.
