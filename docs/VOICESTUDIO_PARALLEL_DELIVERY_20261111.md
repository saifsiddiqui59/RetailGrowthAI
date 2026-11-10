# RetailGrowthAI VoiceStudio — parallel delivery / critical path
Date: 2026-11-11. Primary objective: ship one working script → licensed voice → private reviewed WAV → signed transcript → F4 video → private signed MP4, **not** finish optional engines, studio UX polish, or GPU first.

## Independent lanes (no overlapping write ownership)
| Lane | Existing task IDs | Source and current checkpoint | Next acceptance |
| --- | --- | --- | --- |
| F2 voice/storage | F2-19, F2-20, F2-22 | upstream #907, API #900/#905, private binary #909 **main source only** | signed JWT/RLS and reviewed script + original-key SQL claim, actual pinned licensed voice, SHA readback and registered private asset |
| F4 video audio | F4-06, F4-07, F4-17 | #910 merged into parent #322 **not main** | existing mixer renders approved VoiceStudio PCM and rights-scoped music into real AAC/MP4; merge/reconcile parent |
| F7 speech QA | F7-L, F7-P, F7-I | #911 merged into parent #513 **not main** | actual licensed ASR original hashes, signed transcript/HMAC/lease and word captions; merge/reconcile parent |
| Integration | F2-23, F2-32, F7-J, F4-31 | parent #551/#848, #322, #513 remain to reconcile | one genuine authorized two-shop hosted trace and main 4/4 |
| F3 other work | existing 33 IDs, unchanged | existing hourly F3 worker | independent feature-owned source tasks, no voice implementation duplication |

## Execution rules that avoid months of idle loops
1. Keep separate feature branches/worktrees. Worker does code and targeted offline tests; for a related batch, make ONE coherent commit/push and run exact-head 4/4. Do not start 10 micro-PRs for one adapter or generate non-final CI for every small fix.
2. Merge eligible stacked feature work into its original parent, then reconcile the parent with current main. Do not split the same user-facing Feature4 or Feature7 renderer/ASR responsibilities into another competing engine.
3. The existing Integration Sprint coordinates main merges ONE AT A TIME. Verify current main and changed path overlap, review/branch requirements, exact-head four CI jobs, and a **non-cancelled** fresh main 4/4 before any further main merge. This is operational optimization, not a bypass of docs/FEATURE_SELF_MERGE_POLICY_20261031.md. Feature workers continue parallel source development while this serial gate runs.
4. Freeze upstream contract: Feature2 outputs a private WAV asset `NEEDS_REVIEW`, Feature4 only accepts independent `APPROVED_FOR_EDITING` rights and exact hash/tenant; Feature7 returns UNSIGNED review-only words until current lease and trusted HMAC validation. Never turn source success into human review or publish permission.
5. Commercial permission is independent of app features. Upstream AGPL-3.0 source obligations and a specifically commercially cleared speech model/tokenizer/component inventory are required; default OmniVoice CC-BY-NC weights are OFF. GPU, paid models, PROD, and WineShopPOS stay untouched.
6. If a provider call, SQL claim, private binary write or queue ACK is uncertain, do not auto-retry. Inspect original-key durable state first. Always log source-only vs main-integrated vs hosted-accepted separately.

## Last proven GitHub state
- F2 #909 exact head #42912765739 **4/4**, merged to main as `cead2f56bd418ef38ca56bd00c24935fe7cadaf1`. Its exact postmerge #42913518571 **cancelled** due subsequent main push. Descendant main #42913728712 **4/4**; do not represent the cancelled run as success.
- F4 #910 exact-head #42912304414 **4/4**, merged into existing parent #322 as `de0e3f9058cb72069153bde40a5e16bdee1ab170`, NOT main.
- F7 #911 exact-head #42912311623 **4/4**, merged into existing parent #513 as `9da20794678001f6d4942db450fc4e66a660da2f`, NOT main. Parent #513 itself had 4/4 #42912903250 on this head, but still needs main reconciliation/review.
- Scheduled code-first tasks: F2 VoiceStudio, F4 Voice, F7 Speech and existing F3. Existing Integration Sprint handles main reconciliation. They run at most hourly and are not evidence of continuously running agents.

## Exit criteria for product acceptance
A real licensed model is selected without violating upstream terms; one actual reviewed script synthesizes a non-fabricated private WAV under an authenticated test tenant; a second shop is denied; original and F4 render WAV readback match stored SHA; F7 emits signed source-backed words (or explicit missing-word denial); F4 creates a real authorized private 9:16 H.264/AAC MP4 with correct captions, voice/music ducking and no unlicensed content; signed download and usage/retry ledger pass; parent PR source is merged and main CI 4/4; remaining hosted DEV/auth/real user tests run separately before production. Do not claim DONE from synthetic fixtures.
