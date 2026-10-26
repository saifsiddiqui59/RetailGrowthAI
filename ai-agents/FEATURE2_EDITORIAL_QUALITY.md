# Feature #2 deterministic editorial quality gate — 2026-10-26

This is a **source-only**, no-inference-cost continuation of the already-deployed Feature2 writer, not a new product or hosted release.

## Improvements
- Seven retailer/product-grounded **clothing styling exercises** in the existing English (India) deterministic mode, each with a different angle, question, CTA context and platform-specific copy. Other languages/categories retain their bounded approved template behaviour.
- LinkedIn and Instagram copy is updated in the existing **v1 canonical days** as well as the additive Feature2 sidecar. Existing tenant/campaign identifiers, immutable media IDs, provider storyboard times and v1 schema are revalidated; no automatic publishing.
- YouTube topics are shortened on **word boundaries** before appending a readable shop display name. A fictional fixture's bracketed disclaimer is still present in business metadata and source artifact disclosures, but not cut off inside a video title.
- Every 30-second sidecar scene now tells an editor how to use the **same approved/registered photo only** with contextual overlays. No implied new footage, extra assets, stock claims, product attributes, purchases, offers, rendered posters or videos.
- Added quantitative automated checks: 7 unique topics, channel variants and scene briefs; no truncated brand; no forbidden deals; exactly three ten-second scenes/day; authorized asset IDs only; DRAFT, human approval, frozen v1 contract and deterministic replay.

## Boundaries and gates
- `MockFoundryProvider` still delegates to the existing CampaignProvider/planner, no Foundry, GPUs, paid external APIs or new DB/Azure capacity.
- This test generator uses a **synthetic RSS trend** and **fictional asset UUID**; it does not prove live India clothing trends or commercial rights. Real retailer media can only be registered through the existing authorized upload/rights flow.
- Does not alter Supabase RLS, ROOT/admin approvals, tenant/role checks, subscription ledger, HTTP retries, email, Part2 social publishing, Feature3/4/5 or WineShopPOS.
- All generated content remains **DRAFT / PENDING_RETAILER**; professional quality beyond deterministic checklist requires human creative review and actual authorized product photos.
- Genuine Feature2 hosted E2E remains gated: existing protected test-account canary supports `browser-upload` and `poster`, not signed trends -> POST draft -> saved GET; migration or backdoor impersonation of original DEV retailer is forbidden.
- Verify exact source PR four-job CI, generated real-engine sample workflow and independent post-merge CI before declaring integration passed.
