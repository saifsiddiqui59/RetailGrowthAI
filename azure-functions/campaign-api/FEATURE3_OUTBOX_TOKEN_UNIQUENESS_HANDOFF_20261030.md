# Feature #3 outbox dispatch-token uniqueness — 2026-10-30

**Original tracked packages:** F3-05 (GPU outbox dispatch) and F3-13 (negative race/security regression). **State:** SOURCE PROPOSED; not integrated DONE.

The existing read-only claim RPC adapter rejected repeated `job_id` values but accepted two different jobs carrying one identical `dispatch_token`. That makes the returned lease batch ambiguous if the privileged SQL response is corrupt. It now rejects a reused dispatch token before returning **any** claimed row to the Azure Queue publisher.

Deterministic tests cover distinct jobs with one reused token (deny) and distinct jobs with distinct tokens (allow). These are offline mocked DB tests only; targeted tests have not been run locally. Inspect exact-head four-job PR CI and obtain coordinator review/merge plus fresh main 4/4 before considering source acceptance. Real Azure queue send/ACK, hosted SQL and provider financial settlement remain unverified. No queue messages, paid GPU, inference, hosted SQL, PROD, samples or WineShopPOS changes.

**Dependencies:** F3-04 (Feature3/coordinator) requires approved one-shot queue worker, poison/ACK and real lease proof; F5-GPU-AUTHORIZATION (coordinator) requires human-approved cost/license/kill plan; F3-LICENSED-MEDIA (Feature3) requires independently reviewed commercial original rights; #249 (Azure reliability) requires stable signed DEV gateway. F3-05 and F3-13 remain IN PROGRESS in centralized status; only coordinator updates canonical task_progress.
