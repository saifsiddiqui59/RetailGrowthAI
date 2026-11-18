# Feature 4 missing-source recovery — 2026-11-19

Source PR: #322 at b9525a9ea3d5e5aee351edf89a3c011c2314ed2e.
Pinned main baseline: 49609efcec0f7106d4d10337fb57c39a7a090c17.

Exactly 163 files that were absent from this main tree are copied as unchanged Git blobs, including Feature 4 video engine, visual UI, offline tests and scoped handoff files. Existing files on main are **not** overwritten, including root router, authentication, CI workflows, shared API, package manifests and cloud/tenant contracts. This is a recovery proposal, **not** proof that the files work together against newest main, an approved live route, signed retailer rights, provider quality, genuine garment quality or finished Feature 4 integration.

Required before source acceptance: final-head GitHub Part 1 4/4 CI; review tests and any dependency version drift; affected lead review for vendored OpenReel/HyperFrames license implications and F2/F3/F7 shared contracts; explicitly preserve owner-rejected visual QA status. Keep GPU, paid model, Azure/Supabase writes, PROD, WineShopPOS disabled. The remaining 25 original #322 PR diff paths were not overwritten and must be reconciled individually against current main; never auto-close #322 as feature DONE.
