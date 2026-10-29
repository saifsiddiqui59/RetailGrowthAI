# Testing Chat — independent service-authored worker receipts (source-only)

## What this change adds
- A **release candidate** `supabase/release-candidates/20261029133000_feature_test_worker_spans.sql` outside the protected canonical migration list. It is NOT installed on DEV/PROD. The pre-existing `feature_test_runs` and `feature_test_events` browser-log candidate is also **not** deployed.
- `feature_test_worker_spans` is an append-only public-schema table solely so authenticated retailer OWNER/EDITOR can query its own job references through current Supabase PostgREST with **user JWT and RLS**, not a service key. No anon, VIEWER, foreign tenant, or revoked-editor access. Browser roles have no write/update/delete privileges.
- Only `service_role` may insert, with a SECURITY INVOKER BEFORE INSERT trigger that demands an existing tenant-scoped campaign/render job, matching claim attempt and the DB's authoritative persisted result: seven saved campaign days for `F2 planning.complete`, or a successful `F4` 30-second render with an actual private `output_asset_id`. Specific permanent/retry failure statuses require matching durable error codes. Mutating an event/status via browser is forbidden. A service-key compromise still requires normal incident response; this is defense in depth, not independent cryptographic attestation.
- `worker_span_store.py` is a backend-only writer. It accepts the existing strict `retailgrowth.worker-span.v1` payload, produces an allowlisted service POST and validates the returned row. The database trigger is the final job-state validator.
- Existing Azure Function planning/render queues connect this writer ONLY if `RETAIL_ENABLE_FEATURE_TEST_WORKER_SPANS=true`, **OFF by default**, and only after an authorized DEV schema release. The job claim, rights checks, output media and billing paths are unchanged. A storage outage never changes the worker's actual business outcome or retries mutations for telemetry.
- Testing Chat can **explicitly** read service-side rows for real job IDs already visible in its own browser events. A separate panel keeps authoritative service rows distinct from mutable user-observed receipts. No worker ID, input reference or success is invented. The run→job association is still based on browser-observed references, **not yet independently attested as a run mapping**.

## Offline verification
- Node tests reject foreign-job/shop rows and prove signed-user GET with no service credentials.
- Python tests reject forged object fields, mismatched POST response, and store outages.
- Disposable Supabase CI applies candidate SQL **only** at `127.0.0.1:54322`, proves F2/F4 verified inserts, rejects false outcomes/attempts/720p dimensions, and checks OWNER/EDITOR reads and VIEWER/foreign/revoked/anon denial. Never execute this CI file against hosted DEV or PROD.
- Four job exact-head CI and independent main after merge are mandatory. A green CI does NOT release tables or authorize cloud settings.

## Release order (remaining, outside this PR)
1. Independent operator verifies migration inventory against **real DEV project** `jeearzffnjbvghwjjjrf`, current backups/rollback, versioned migration staging and approval. Browser trace tables must release first, then worker span table. Do not send unversioned DDL to hosted DEV.
2. After reviewed DEV migration, run signed two-shop role tests and PostgREST schema discovery. Deploy matching frontend and Functions worker source via existing protected DEV workflows; avoid Azure issue #249 unsafe POST retry and unapproved SKU changes.
3. Observe a genuine Feature2 campaign and existing Part1 FFmpeg job from two distinct signed test shops; verify each browser receipt, backend span, private media, rights, usage, revocation and eventual clean-up. Only then turn the worker-span flag on in DEV and claim durable trace proof.
4. Later add a trusted run→job mapping created by the authenticated submission backend (not mutable browser metadata). Extend Feature3/VTON, Feature5/API motion, Feature4 professional compositor, Feature7 editor independently after actual worker claims and rights. No automatic publishing/paid generation.

There is **no** connection to WineShopPOS, PROD, or an unapproved paid provider.
