# Feature #2 batch: F2-02 / F2-04 / F2-21 — 2026-10-30
All three independently actionable owner source tracks share the verified fixture and dependency policy in coordination/shared_feature_references.json. IN PROGRESS, source-only.
## Single-commit, single-CI-boundary speed improvement
1. F2-02: retail copy rejects HTTP and www links (plus existing HTTPS). Three synthetic negative tests.
2. F2-04: signed RSS ranker revalidates source grant on returned selected candidates; malformed present GUID cannot silently rekey. One signed-grant revocation and two malformed-GUID tests.
3. F2-21: private CPU reservation cannot return trusted receipt asserting paid provider, automatic Azure, commercial or motion authority. Four negative test variants.
These use previously documented retailer and RSS fixture inputs, not real customer grants or media. One Git commit creates all source, tests and documentation before the full four-job CI run, instead of a push/CI per change. All earlier tests remain enabled.
## Remaining external gates
Coordinator must reconcile draft #551, #684, #704 and sibling drafts #697/#700; verify real authenticated tenant/rights, transaction storage, #650 protected ZIP package, #249 Azure HTTP and approved integration into main plus fresh 4/4. No task accepted DONE solely because a fixture test passes. No GPU, paid model, PROD, WineShopPOS or generated public samples.
