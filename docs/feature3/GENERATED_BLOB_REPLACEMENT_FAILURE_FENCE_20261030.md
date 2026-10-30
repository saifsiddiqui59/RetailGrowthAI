# Feature #3 — private generated Blob replacement failure fence (2026-10-30)

Original centralized task IDs: **F3-10** (private Blob/cache/revocation lifecycle) and **F3-13** (negative race/security regressions). Status: **SOURCE PROPOSED, NOT INTEGRATED DONE**.

## Reproduction and correction
The existing browser-memory scope allocated a fresh object URL, then called `clear()` to revoke the previous URL. If the revocation callback failed, `clear()` erased the visible scope but the newly allocated object URL was left untracked and unreleased. A nonconforming URL factory could also return the same URL twice, causing the replacement to reuse a revoked URL.

The new guard rejects URL aliasing without revoking the still-owned previous preview. If previous-URL revocation fails, the replacement URL is immediately passed to the revoker, no new URL is installed, and the scope remains empty. The original failed revocation is not misreported as successful; actual browser revocation can still fail and is not a server-side signed-URL invalidation.

## Deterministic verification
`node --test tests/frontend/feature3-generated-blob-scope.test.mjs` includes positive lifecycle tests plus duplicate factory URL and simulated revoke failure. Full four-job PR CI and coordinator postmerge main CI remain required. Tests are synthetic in-memory Blob fixtures, **not** genuine generated PNG, commercial rights, signed DEV authentication or hosted approval.

## Remaining gates
F3-10/F3-13 still require mounted authenticated no-URL private output route (#471/#325, coordinator), real rights/lease/revocation proof (F3-LICENSED-MEDIA, Feature3), actual signed tenant-isolated DEV negative tests and accepted postmerge 4/4. Existing signed Storage URLs are not retroactively revoked. No GPU, paid inference, PROD, hosted SQL or WineShopPOS changes.
