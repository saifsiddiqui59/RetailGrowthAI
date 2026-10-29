# Feature #3 Azure Queue peek GPU-OFF status fence — 2026-10-29

## Source-only safety correction (existing F3-04/F3-05 partial work)
- An *empty* Azure Queue peek had previously returned `gpu_enabled: false` without consulting the current provider. The queue intake's status check happened only per visible message, so zero messages did not prove the provider was OFF.
- `Feature3GPUOffQueueIntake.require_gpu_off()` now fails closed on ON, missing, invalid or unavailable authoritative provider state. The non-destructive queue peek checks this before one SDK peek and again after the read, even for zero visible jobs. Existing per-message current rights checks remain unchanged.
- Offline Python tests cover empty paid/unknown modes, state flipping during empty/non-empty peek, and no receive/ACK/delete/send. No Azure account accessed; this is not a remotely verified queue or paid-job acceptance.

## Handoff
- Branch: `feat/feature3-gpuoff-empty-queue-status-fence-20261029`. Coordinator review, exact-head CI 4/4 and postmerge main CI required before any source-integration claim.
- Preserve 0/33 fully hosted DONE; F3-04/F3-05 remain partial/blocked pending F5-GPU-AUTHORIZATION, PART3-WAN22-CONTRACT, actual one-shot runtime/unknown-ACK reconciliation and signed current rights. GPU OFF; no hosted migrations, provider invocation, PROD or WineShopPOS.
