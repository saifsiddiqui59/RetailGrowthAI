# Feature2: GPU-OFF professional Reel offline acceptance — 2026-10-28

**Status:** source-only test work stacked on draft PR #531 / pinned MIT Creative Director #514. GPU explicitly OFF; no paid inference, no media rendering, no DEV/PROD mutation, no WineShopPOS.

## Actual code tested

Uses the vendored Kuble-Lab Open Creative Director pinned MIT planning, cue timing and revision functions via Feature2's existing directorPrompt, compile and revise adapters. A hand-authored, entirely synthetic Thread and Loom Studio Diwali kurti scenario supplies private TEST first-frame metadata, SHA-shaped original-file evidence, exact approved five garment facts, and a fictional shop-approved 20% discount for eligible SKU KURTI-RED-01. These are **fixtures, not genuine authorized assets, offers or GPT model output**.

Runs independently for 15, 30 and 60 seconds: original cinematic copy with 3, 6 or 12 five-second shots; each has one adult model with unchanged identity, unique camera/subject action, physical garment-response timestamps, focal framing, lighting, background and detailed Wan-oriented image-to-video prompts. It compiles the actual versioned creative_direction_v1 and motion_direction_v1 contracts, including precise offer terms and original-media SHA review hashes.

The offline-acceptance helper proves the F2 storyboard and shot prompts agree byte-for-byte, the planned editor timeline has no gaps, all expenses and motion calls are skipped, every plan remains a human-review-required DRAFT, and no audio/video file is generated. This is a **mock editing/dispatch consumer**, NOT an acceptance test of the real Feature4 editor or Feature5 Wan provider. A reviewer can run the tests using:

- node ai-agents/creative-director/tests/test-diwali-offline-e2e.js
- uv run --project ai-agents pytest ai-agents/tests/test_feature2_premium_diwali_offline_e2e.py

Other original upstream tests and source/Foundry mocked tests remain in existing CI. The new readinessFromOffline helper reports offline_source_scenario PASSED but feature2_production_ready=false and ready_to_activate_gpu=false, with eight explicit unreconciled acceptance gates. Those flags are intentionally not modifiable through fixture input.

## Outstanding blockers and truthfulness

1. Integrate coordinator-reviewed draft source PRs #514, #531, #535, #522, #523 and #526, preserving current interfaces and 4/4 CI.
2. Deploy a *verified executable* compatible director runtime with actual vendored MIT source and license; current Python Azure Functions package does not contain it.
3. Wire live authenticated JWT and same-tenant RLS rights/offer evidence readers; do not use the mock retailer's image, test discount or revoked synthetic user.
4. Ratify Feature4 PR #322's mismatched direction envelope and Feature5 Wan-specific motion support; do not silently reduce rich prompt details to Hunyuan 480p or submit paid jobs.
5. Run one separately approved genuine GPT-4.1-mini Director plan and independent human blind editorial review; this test's hand-authored copy is not a real-model benchmark.
6. Verify genuine voiceover/audio timestamps, original licensed kurti and actual rendered cloth identity (color, embroidery, hem, neckline and sleeves) against private rights-verified first frame.
7. Obtain real relevant clothing-trend evidence; complete signed DRAFT POST/GET and clear independent Azure Issue #249 503 hosted reliability.
8. Obtain separate documented GPU provider, cost cap and operator approval AFTER Feature2 is objectively ready. GPU remains off here.

Coordinator owns canonical shared docs PROJECT_STATE, NEXT_TASK, DECISIONS and WORK_LOG and production merges; this Feature2 report is additive. No automatic paid calls or background tasks started.

## Additional mocked Azure GPT-4.1-mini positive-path test

The standalone director-to-editor mock now has a **second independent test** at ai-agents/tests/test_feature2_diwali_mocked_foundry_positive.py. It calls the REAL local Python AzureFeature2DirectorLLM and actual Node/mit planner from the same synthetic approved 15/30/60-second script, but replaces ONLY the HTTPS transport with a deterministic **no-network fake** returning a shaped Foundry completion and actual-usage-shaped token receipt. It verifies one per-shop budget reservation before the model request, no retry, real local JSON compile, precise same-shop media and sale proof hashes, and a nonpublishable DRAFT for 3/6/12 shots. This is **not** a genuine Azure model answer, billed token record, external video or claim of artistic quality. No model keys or GPU usage occur.

An initial test caught a shared-object alias issue: changing a motion prompt changed the nested storyboard in memory simultaneously. The offline handoff now recomputes the ORIGINAL Creative Director plan fingerprint over its editor scenes and Feature3 garment lineage; any such post-review mutation is rejected before a mock editor timeline can be built. The first failing CI was **not bypassed**; the protected hash invariant was added and the negative test retained.
