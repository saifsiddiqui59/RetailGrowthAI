# Testing Chat — signed private trusted worker evidence panel

## Source contract
A retailer Testing Chat run first stores its browser-observed per-feature
receipts and optional human quality opinions. A separate "Check verified
worker spans" control performs an **explicit read-only** per-job lookup of
the **backend-only** ledger created by the separately staged
`retail_feature_worker_spans` RPC from #622.

- The existing client uses its current signed-in user JWT and the
  publishable key. Never sends a service key, accesses private tables
  directly, or reads another shop without the DB's fresh active
  OWNER/EDITOR membership check.
- Lookup uses at most two server-known job UUIDs (F2 campaign and F4
  current Part1 FFmpeg render), a 30-row cap per call, and never enqueues
  or changes campaign state. The backend RPC derives data from
  `retail_private.feature_worker_spans` only if its source is
  `trusted_backend_persisted`.
- The client requires exactly matching `shop_id`, `job_id`, allowed
  F2/F4 feature-operation-terminal status, bounded attempts/duration,
  exact output metadata, unique event UUIDs, and an event count within
  the requested limit. On malformed, unauthorized, unavailable or
  missing RPC, it displays **unverified/unavailable**, never PASS.
- Browser-observed text and runtime HTTP marker remain separate from
  trusted backend evidence. The UI never upgrades a browser PASS or
  human 5/5 review to proof that a GPU/VTON/editor ran.
- React clears stale worker evidence when the selected shop, test run
  or active user request changes; late responses cannot populate
  another tenant's report.

## Release and remaining gaps
This is source-only. Host DEV must first receive two distinct reviewed
canonical migrations: browser trace run/event tables (#614 candidate)
and service-only worker span ledger (#622 candidate). The source worker
sink (#624) must be explicitly enabled only after its real SQL migration,
role-denial verification and protected deployment. Then release the UI
through existing RetailGrowthAI DEV Static Web App workflow and run
signed OWNER/EDITOR, VIEWER, cross-tenant and revoked-account tests.
Without that complete chain the panel intentionally shows no
verified backend result.

No Feature3, Feature5, or Feature7 execution is inferred from empty
ledger responses. Feature4 currently verifies only the existing 30s
FFmpeg Reel pipeline, not the professional video compositor. Azure
issue #249 remains open. No paid providers, PROD or WineShopPOS changes.
