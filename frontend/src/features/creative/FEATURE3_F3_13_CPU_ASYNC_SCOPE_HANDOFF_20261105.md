# F3-13 — fail-closed asynchronous CPU poster export / import (2026-11-05)

## Original task and scope
- Original Feature #3 package **F3-13** (cross-tenant, rights and ambiguous-late-response regressions), supporting **F3-09** local editor.
- This is an **offline source candidate**. Do not mark the original task DONE or claim signed DEV, human licence approval, hosted private PNG route, or actual provider output.

## Observed race and fix
- Browser `canvas.toBlob` is asynchronous. The previous callback could issue a local PNG Blob URL and initiate a download after the active day/tenant editor closed, changed, became disabled or an image-rights map was replaced.
- A per-editor epoch now invalidates in-flight encodes across source edit, day/shop context, authorized map replacement, disable and unmount; callback checks before creating any PNG Blob URL.
- Only one PNG encode may be in flight per editor, even on rapid repeated clicks.
- Failed browser downloads attempt to revoke the freshly issued private Blob URL.
- Asynchronous local JSON import rejects a late `File.text()` result if the editor's current scope has changed.
- No network API, SQL migration, GPU, inference, hosted service, publish or approval paths modified.

## Deterministic regression
`frontend/e2e/campaign-journey.spec.mjs` intercepts real Chromium canvas PNG encode, holds completion while closing the CPU Poster Studio, then releases the encoded image. It verifies duplicate clicks schedule only one encode; zero PNG Blob URLs/downloads are issued after unmount; no backend upload, registration, render or signed opens are invoked. Existing F3-22 Playwright test proves normal valid 1080×1920 PNG pixels and offline-only output.

## Integration / acceptance gates
1. Verify exact-final-head **four** existing Part 1 CI jobs on the PR (including Playwright).
2. Independently review tenant/private-media lifecycle and current-main compatibility under `docs/FEATURE_SELF_MERGE_POLICY_20261031.md`; no author-only security approval.
3. Only after eligible review/integration, verify fresh four-job **main** CI before accepting the source slice.
4. Preserve F3-13 source-partial and **0/33 hosted-accepted** until real signed tenant/RLS, binary endpoint and current commercial rights are independently verified. GPU and paid models remain OFF.

No WineShopPOS, PROD, DEV SQL or paid cloud actions.

## Extra F3-13 schema negative coverage
- Found that `FEATURE3_FORMATS[raw.format]` previously accepted inherited JavaScript property names such as `constructor` and `__proto__` as a non-empty format. Later canvas dimension destructuring could crash, rather than issuing an early invalid-document denial.
- `validateFeature3Design` now requires a string format that is an **own key** of the fixed allowlist, and strictly typed hex colours; malformed prototype names, object formats, or coercible colours are denied. No valid v2 document shape changes.
- `tests/frontend/feature3-design.test.mjs` adds rejected payload negatives and a valid `story` control. This is source-only input validation, not an approved hosted poster.
