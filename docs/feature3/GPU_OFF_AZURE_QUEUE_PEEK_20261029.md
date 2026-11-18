# Feature3 GPU-off Azure Queue non-destructive inspection (2026-10-29)

## Actual SDK boundary

`Feature3GPUOffAzureQueuePeek.inspect_visible(limit=1..5)` uses a supplied, already-authorized Azure Storage Queue `QueueClient.peek_messages(max_messages=limit,timeout=5)` exactly once. Microsoft documents that `peek_messages` does not alter message visibility or dequeue count. It does **not** receive or delete any message and will never start a queue-triggered Azure Function, call a provider, claim SQL, confirm delivery, retry a paid attempt or finalize charges.

The bounded peek data is passed to the existing strict v1 envelope/current-rights `Feature3GPUOffQueueIntake`, which explicitly requires provider OFF and a current backend SQL/media proof. Unknown, duplicate, foreign, invalid, expired/rights-revoked, deceptive paid flags or Queue API failure -> fail closed with no operator reply pretending that an unknown outcome means empty. Result contains only job/shop ID, source count and false claim/ACK/delete/paid permissions, never raw image bytes, billing token, pop receipt or signed URLs.

Tests `tests/api/test_feature3_gpuoff_queue_peek.py` use Azure SDK-shaped `QueueMessage.content` test doubles, assert exact once `peek_messages(max_messages=5,timeout=5)`, and assert **zero** SDK receive/delete/clear/update/send calls even on failures. Tests are CPU/offline only, not real Azure access.

**Security:** This is a peek-only diagnostics module. It must run only from an approved backend operator with already existing queue read credentials and a real service rights plan. Do not inject actual queue credentials into JS/GitHub logs, do not mount a Queue trigger, and do not delete an observed message. The actual queue worker, dead-letter policy, single-use SQL claim and paid-provider release require separate review.

Official SDK API: https://learn.microsoft.com/python/api/azure-storage-queue/azure.storage.queue.queueclient and https://learn.microsoft.com/en-us/azure/storage/queues/storage-python-how-to-use-queue-storage .
