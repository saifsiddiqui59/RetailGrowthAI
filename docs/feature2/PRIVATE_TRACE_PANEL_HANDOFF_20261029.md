# Feature #2 private creative workflow trace panel — coordinator handoff

**Source implemented, not mounted on hosted DEV or PROD.** This is the Feature #2-owned callback contract proposal for task #12/#32, and does not alter coordinator-owned `docs/INTERFACES_V1.md`.

## Existing source

- `ai-agents/src/ai_agents/feature2_creative_quality.py`: `append_feature2_trace` (private event write with shop/workflow CAS, event SHA and HMAC) and `read_verified_private_trace` (private readback, full HMAC/sequence/scope verification, role and data re-read).
- `frontend/src/features/voiceover/voiceover-trace-model.mjs`: response validation; refuses foreign tenant, changed source, noncanonical stage/status, invented external proof or publishing.
- `frontend/src/features/voiceover/Feature2TracePanel.jsx`: explicit user-triggered read, no HMAC secrets or raw scripts sent to browser; inserted optionally into Feature #2 `VoiceoverSelector.jsx`.
- Python source integration test uses **the real pinned Creative Director exporter** to create 15/30/60-second Feature4/Feature5 packets, records `STORYBOARD:SUCCEEDED` as SYNTHETIC_TEST_ONLY, records voice/F7/F4 as **BLOCKED**, verifies the complete HMAC chain, and tests tampering.
- Node tests at `tests/frontend/feature2-private-trace.test.mjs` deny foreign shop, stage escalation, swapped source, fake audio/publish outcome and bad event ordering.

## Trusted backend callback requested from the coordinator

The mounted `VoiceoverSelector` takes three optional properties, `traceWorkflowId`, `traceSourceSha256`, and `onFetchPrivateTrace`.

```javascript
const response = await onFetchPrivateTrace({
  shop_id: shopId,           // current authenticated shop (not browser authority)
  campaign_id: campaignId,   // current, same-shop campaign
  workflow_id: traceWorkflowId,
  source_sha256: traceSourceSha256,
})
```

The **source SHA** is the immutable workflow input digest from the authenticated trace writer. It is **not necessarily** the Creative Director plan SHA. Never substitute arbitrary client-supplied values or let another shop resolve the UUID. Use a server-side verified current JWT and membership to call the authenticated trace read function and return only the readback *projection*. Supabase must implement immutable unique event IDs, strict shop RLS, source version fencing, transactional CAS/sequence, retention and revocation.

Response schema (existing Python implementation):

```json
{
  "schema": "retailgrowth.feature2-private-trace-history.v1",
  "shop_id": "current-shop-uuid",
  "campaign_id": "current-campaign-uuid",
  "workflow_id": "current-workflow-uuid",
  "source_sha256": "64 lowercase hex",
  "events": [
    {
      "sequence": 1,
      "stage": "TREND",
      "status": "SUCCEEDED",
      "evidence_class": "SYNTHETIC_TEST_ONLY",
      "failure_code": null,
      "event_sha256": "64 lowercase hex",
      "can_publish": false
    }
  ],
  "last_event_sha256": "64 lowercase hex",
  "private": true,
  "all_steps_verified": true,
  "actual_model_inference_verified": false,
  "can_publish": false
}
```

The backend must **never return** `service_secret`, `server_mac`, source scripts, raw provider replies, audio, private media URLs, JWTs, or full internal event bodies. The client can't re-verify an HMAC because giving it the secret would defeat private audit integrity; it validates only the server-provided bounded projection. A `SIGNED_EXTERNAL` event still requires independent trusted service evidence at write time and is not automatically a commercially approved video. Source/synthetic stages must remain clearly labeled, and any absent original WAV, human approval, F3 rights, F4 render or F5 inference must remain BLOCKED.

No Azure/Supabase migration, app root mount, real model inference, event replay or hosted E2E is claimed in this Feature #2-only handoff. Coordinator `main` CI and issue [#650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) remain separate blockers.
