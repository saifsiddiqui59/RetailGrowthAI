# VoiceStudio → RetailGrowthAI Feature2 / Feature4 private audio handoff

## Current checkpoint (2026-11-11)
Adopts existing unmodified VoiceStudio OpenAI-style speech API; no voice engine is reimplemented or upstream source/model weights bundled. Parent integration PR #900 was merged to main as `e3afa633dfc2b0efb8aa09b449159a3e7d088efc`, with PR 4/4 and postmerge main 4/4 checks.

This increment:
1. Hardens the existing provider client against redirects, origin/status/content-type spoofing and truncated WAV frames.
2. Adds `feature2_voicestudio_feature4.fit_voiceover_to_reel`: preserve the original PCM frames and append silence to exactly 15/30/60 seconds, instead of dropping words or changing speed. Generates original/render SHA-256 proof and rejects oversized media.
3. Adds `feature2_voicestudio_private_workflow.create_private_voiceover`: trusted current-source checks before/after an original-key SQL claim and after provider/private-write callbacks; at most one upstream POST; records private original+F4-ready WAV via required trusted writer; reads back authoritative shop/campaign/request/plan/bytes receipt; returns only a **NEEDS_REVIEW** private audio asset ID with `voiceover_source=retailer` hint, never raw audio, signed URL or publish rights.
4. Includes deterministic offline injected-transport tests for source mutations, foreign receipt, duplicate claim, ambiguous writes, malformed WAV and unapproved model gating.

## What is still NOT integrated
- The `read_current_plan`, `claim_once`, `write_private_audio` and `read_private_receipt` callbacks must be bound to the EXISTING trusted JWT/RLS, reviewed private storage and durable SQL job/lease system; this PR does not add HTTP routes or hosted schema. Fixture callbacks are not an implementation of Supabase.
- Feature4's draft #322 already consumes `voiceover_asset_id`, `voiceover_source=retailer` and full-length private audio, but it is NOT on main. Final signed private-source and original spoken-audio approval must be checked independently by Feature4, and captions/ASR by Feature7.
- Live provider use stays OFF until an exact model revision, weights, tokenizer dependencies and commercial rights are actually approved. Upstream default OmniVoice pretrained weights use CC-BY-NC and cannot be treated as commercially cleared by using AGPL application code. A proprietary closed-source embedding also requires reviewing AGPL source-offer obligations or obtaining a separate commercial upstream license.
- No end-to-end hosted voice, genuine CPU inference, customer dubbing, real account/tenant negative test, or licensed model benchmark has happened. No GPU, inference charges, Azure deployment, hosted migration, PROD or WineShopPOS changes.

## Safe next work
1. Review exact-head 4/4 CI and merge this *Feature2-owned source-only change* if eligible, then verify fresh main CI.
2. Reconcile and integrate existing Feature2 #551/#848 source input/script/approval and Feature4 #322 / Feature7 #513 interfaces. Do NOT discard rights, editor, ASR, F4 or signed private-storage code as "duplicate engine work".
3. Add reviewed SQL-backed original-key claim and private WAV registration; wire an authenticated feature route only after tenant isolation negative tests. Avoid putting upstream key or URL in browser. No replay on ambiguous ACK.
4. Close only superseded stand-alone voice-engine PRs after their stronger behaviour/tests are retained; PR closure does not itself mark original task DONE.

Tests: `ai-agents/tests/test_feature2_voicestudio_adapter.py`, `test_feature2_voicestudio_feature4.py`, `test_feature2_voicestudio_private_workflow.py` under the existing Python CI job.
