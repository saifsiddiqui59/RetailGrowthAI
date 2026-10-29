# Feature3 generated private image history — local filters and preview cleanup

## Non-GPU source-only UX
- The existing signed JWT/RLS `listGeneratedJobs` remains the sole history fetch, manually requested by the customer. The browser cannot issue a new GPU job, claim a private worker, infer customer approval or publish a generated image.
- An additive local filter lets a signed-in shop view All, Queued, Running, Generated — unreviewed and Failed statuses from the **already verified** exact `id/shop_id/status` history rows (maximum 20). Foreign rows, invalid statuses, extra URLs, fabricated `approved_model` or unreviewed publication claims remain denied by `validateFeature3GeneratedHistory`. No new history API or dependency.
- Changing the filter explicitly clears any existing private preview Blob URL and cancels acceptance of a pending authenticated `get()` result through the existing epoch fence. The visible preview must correspond to a SUCCEEDED job **within the currently visible filter**; a hidden or foreign job cannot leave its pixels on-screen.
- `tests/frontend/feature3-generated-history.test.mjs` exercises frozen filter output, four status cases, unsupported/foreign/forged row denials and frontend source-level cleanup integration. CI additionally builds the actual Vite/React frontend and executes existing mocked Chromium tests.

## Gated hosted acceptance
Real generated PNG history remains empty on hosted DEV while there are no genuine licensed/approved job outputs. A synthetic SUCCEEDED row in a Node test is NOT a real commercial poster. The separately gated no-URL private binary route and independent current source/output rights must be accepted before previews are enabled. No GPU, queue, billing, hosted migrations, deployed PROD or WineShopPOS changes are part of this source UX.
