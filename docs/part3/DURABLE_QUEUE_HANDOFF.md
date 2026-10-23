# Part 3 durable premium outbox / Azure UUID queue scaffold (OFF)

Branch `feat/p3-durable-queue-scaffold` targets `feat/part3-integration`, NOT main.

## Additive source implementation

- `premium_queue.AzurePremiumQueue` mirrors the existing Part1 Azure Storage Queue client but targets a **distinct proposed** `retail-premium-video` queue. It emits only canonical 36-character job UUIDs; no prompt, token, tenant data, signed URL, media or cost. It does NOT call `create_queue`, provision the queue or use a paid API.
- `premium_outbox.dispatch_premium_outbox` expects an **atomic, database-claimed** premium outbox event with `id, lease_token, kind='premium_video', job_id`, sends only the UUID and confirms with CAS. On ambiguous Queue send, it marks the claimed event as unconfirmed; an eventual resend is safe ONLY if the yet-to-be-implemented DB claim worker enforces at-most-one billable provider POST even on replay.
- `record_premium_poison` records an SHA-256 fingerprint + optional canonical job UUID, never arbitrary message contents or job status. It requires durable DB receipt before queue ACK.
- `reconcile_premium_and_dispatch` invokes the future SQL reconciler first. **Never** reset UNKNOWN/SUBMITTING to QUEUED or send a second paid provider request without a verified provider reconciliation.
- Every dispatcher and poison action is `enabled=False` by default and raises before touching external dependencies.

## Essential missing integration before deployment

1. A separately owner-approved new Supabase migration must provide atomic `claim_premium_outbox`, `confirm_premium_outbox`, `record_premium_poison` and `reconcile_premium` service-role RPCs (names are contracts/proposals only), database-backed idempotency, rights/credit evidence, TTL leases and bounded retries, plus correct RLS and negative concurrency tests.
2. Azure infrastructure must be explicitly approved to create the distinct premium queue + poison queue, and the owner must authorize deployment of the new **DISABLED** premium timer/queue/poison triggers.
3. The consuming premium worker must claim the actual SQL job/attempt before calling provider. All replays, poison and ambiguous vendor POSTs must be fenced and stop at UNKNOWN rather than creating another charged task.
4. No live queue, timer, Python Function registration, database changes, WAN request, hosted E2E or premium credits are made by this workstream.

CI: `tests/reliability/test_premium_outbox.py` tests UUID-only payload, malformed claims, disabled default, CAS confirmation, ambiguous queue ACK, durable poison receipts and reconciliation sequencing. Require 4/4 existing CI plus 2/2 Part3 dedicated CI before merging internally.
