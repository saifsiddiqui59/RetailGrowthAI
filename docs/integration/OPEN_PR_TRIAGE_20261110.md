# Open PR triage — 2026-11-10 (snapshot)

> Read-only classification after three verified duplicate closures; not a deployment/merge approval or task acceptance. Pull requests may change after collection.

## Snapshot

- **119 currently open PRs**: Main-targeted / non-draft: 18; Main-targeted / draft: 11; Feature-branch-targeted / non-draft: 2; Feature-branch-targeted / draft: 88.
- 29 main-targeted; 90 feature-targeted/stacked. Draft is not merge-ready merely because CI is green.
- Do not treat source completion as task DONE or hosted acceptance; GPU, paid providers, hosted SQL, PROD and WineShopPOS remain untouched.

## Source preservation and duplicate closures

| Closed PR | Canonical source keeper | Evidence |
|---|---|---|
| [#523](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/523) | Open [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) | All three paths retained; protocol Markdown blob identical; review, blind_human_comparison, content_fingerprint and all six test functions preserved; stricter safety tests added. Closed unmerged, NOT DONE. |
| [#522](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/522) | Open [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) | All three paths retained; audit_entries, audit_zip and all three tests preserved; stricter ZIP/Node assertions added. Closed unmerged, NOT DONE. |
| [#535](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/535) | Open [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) | Original director context module, seven negative tests and dedicated handoff are each identical Git blobs in #848. Two unique older explanatory handoff paragraphs preserved in #848 PR comment 6748650091. Closed unmerged, NOT DONE. |

Compared exact original source heads #523 a302ba6f, #522 75163a2a and #535 9309e1a6 to keeper #848 b18459bd. Each original PR conversation has the detailed source comparison. #848 remains open and is NOT integrated.

## Priority integration and dedup queue

1. Feature #2: #551 is the main-targeted draft parent; #848 is its feature-targeted consolidated child (80 paths). First resolve issue #650 protected packaging and independently review the real source/tenant/auth changes; require exact-head 4/4 and main compatibility. Historical #522/#523/#535 need no duplicate review.
2. Feature #3: review canonical PNG #879 ahead of dependent private-rights/route #880, then separate shared docs #873. Do not count hosted F3-08 DONE.
3. Issue #650: #885 is a draft shared Azure package manifest fix requiring independent runtime/security review. Keep the 120-entry bound and all security preflight gates.
4. Issue #249: #888 documents already merged source fixes; #887 shared workflow and #889 DEV capacity trial need separate review and operational approval. Gateway fault remains unresolved until live evidence.
5. Features #4/#5/#7: reconcile their many stacked drafts against consolidated feature branches #322/#465/#513 and previous merged feature-owned batches; preserve unique code and independent reviews.
6. Historical docs and research #312/#313/#318/#497 still have unique compared files, so are NOT proven duplicates. Part 3 #121 is currently unmergeable and needs reconciliation, not silent closure.

## Complete open PR inventory

Groups from current GitHub open/draft/base filters, including the documentation PR #891 itself. Titles are not code completion evidence.

### Main-targeted / non-draft (18)

| PR | Description |
|---|---|
| [#891](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/891) | docs(integration): triage all open PRs and record verified F2 duplicate closures |
| [#889](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/889) | ops(#249): gated 15-minute DEV-only HTTP Always Ready A/B with independent rollback |
| [#888](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/888) | docs(#249): record verified source integration and Azure diagnostic review gate |
| [#887](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/887) | ci(#249): review isolated DEV-only manual Azure incident workflow |
| [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) | Feature3 F3-08: fail-closed current output rights authority boundary and negative tests |
| [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879) | fix(feature3 F3-08): fail closed on malformed PNG transparency chunks |
| [#873](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/873) | docs(feature3): record F3-13 PR #872 verified main CI and review gap |
| [#856](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/856) | chore(scheduler): remove legacy no-executor/report-only policy keys |
| [#855](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/855) | Remove hourly task schedulers and selection instructions |
| [#823](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/823) | perf(#249): bound warm Supabase JWKS verifier reuse on Python Flex HTTP |
| [#679](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/679) | fix(p0249): protect DEV Node canary JWT from header spoofing and redirects |
| [#676](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/676) | fix(p0249): stage both disposable retailer accounts before ROOT approval window |
| [#668](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/668) | feat(p0249): add OFF-by-default same-origin Node HTTP transport candidate |
| [#639](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/639) | fix(p0249): wait for exact ROOT queue render and reject overlapping test runs |
| [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) | feat(feature2): unify pinned MIT Creative Director, trusted grants, QA, editorial handoff and GPU-off integration tests |
| [#513](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513) | feat(feature7): AutoBroll uploaded-footage semantic edit proposals with tenant fences |
| [#466](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/466) | docs(feature2): reconcile signed DEV live trend success and Azure 503 draft blocker (#403) |
| [#356](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/356) | P0 #249: merge validated private Reel SQL proposal without feature conflicts |

### Main-targeted / draft (11)

| PR | Description |
|---|---|
| [#885](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/885) | fix(issue650): keep Feature4 source-only QA out of Azure Functions ZIP |
| [#696](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/696) | feat(coordination): make feature chats read control table and continue next tasks |
| [#627](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/627) | feat(testing): signed backend-verified worker evidence in Testing Chat |
| [#514](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/514) | feat(feature2): pinned MIT creative director — 15/30/60s contracts, source CI 4/4 green |
| [#497](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/497) | docs(research): reconcile Feature2 AI Director, Feature4 editor and Feature5 Wan code reuse |
| [#323](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/323) | Feature #5: gated Hunyuan AI motion provider/worker contracts (source-only) |
| [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) | WIP Feature #4 — Timeline Studio engine (illustrated demo rejected; visual QA open) |
| [#318](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/318) | docs(architecture): professional beat-driven videos with HyperFrames + licensed music |
| [#313](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/313) | docs: evaluate top 590 GitHub OSS projects for RetailGrowthAI video, poster, media |
| [#312](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/312) | docs: compare OSS video/poster projects for RetailGrowthAI |
| [#125](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/125) | DRAFT Part 3 → main: gated Wan premium video foundations (Coordinator integration) |

### Feature-branch-targeted / non-draft (2)

| PR | Description |
|---|---|
| [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) | feat(feature2): consolidate existing Creative Director source PRs for coordinator review |
| [#121](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/121) | Part 3: secure private Wan output ingestion and media validation |

### Feature-branch-targeted / draft (88)

| PR | Description |
|---|---|
| [#892](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/892) | Feature7: consolidate three divergent source/security PRs #736 #725 #747 |
| [#852](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/852) | Feature4 F4-13: canonical same-shop storage object keys before private source download |
| [#851](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/851) | Feature4 F4-15: fence encoded-output SHA and original inode through private upload |
| [#850](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/850) | Feature4 F4-10: prevent stale shop/draft render ACKs from revealing signed previews |
| [#845](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/845) | fix(feature4 F4-07): preflight private audio proof before mastering |
| [#841](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/841) | Feature4 F4-02: fail closed on swapped 60s MP4/provenance/QA receipt paths |
| [#839](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/839) | Feature4 F4-08: synchronize timeline frame seeking with authorized video preview |
| [#838](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/838) | fix(feature4 F4-08): reject nonfinite timeline seek positions |
| [#837](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/837) | Feature4 F4-12: multilingual approved subtitle typography and anti-spoof controls |
| [#835](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/835) | Feature4 F4-11: stable original MP4 inode for encoded 60s endcard proof |
| [#832](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/832) | fix(feature2 F2-02): deny invisible Unicode commercial-claim spoofing |
| [#831](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/831) | Feature4 F4-07: fence same-content source inode swaps during AAC mastering |
| [#830](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/830) | Feature4 F4-06: bounded independent source/music/voice/SFX gain contract |
| [#828](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828) | Feature4 consolidated batch: real effect parity + motion source integrity + lease-race guards |
| [#827](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/827) | Feature4 F4-11: stable encoded motion SHA/inode and finite same-scene probes |
| [#824](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/824) | Feature4 F4-15: fence lease before private download/CPU and verify staged inode |
| [#822](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/822) | Feature4 F4-05: fix silent approved animation presets and lock renderer effect parity |
| [#821](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/821) | feat(feature2 #19/#21): authenticated original-key private voice job status backend adapter |
| [#816](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/816) | Feature4 F4-14: same-head 15/30/60 source CPU/RSS evidence envelope |
| [#815](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/815) | fix(feature4 F4-13): fail closed on malformed approved creative copy |
| [#808](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/808) | Feature4 F4-11: full encoded timeline black-hold QA, not just scene spot checks |
| [#803](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/803) | fix(feature4 F4-13): deny release with unapproved auxiliary Reel media |
| [#801](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/801) | fix(feature2): reviewer claims, RSS dedupe and prompt input validation |
| [#799](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/799) | fix(feature4 F4-02): prevent aliased/no-op 60s QA receipts |
| [#797](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/797) | fix(feature2 F2-10): reject stale local voice results after role and callback changes |
| [#796](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/796) | fix(feature2 F2-03): deny invisible Unicode prompt spoofing before signed draft review |
| [#792](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/792) | Feature4: pre-render lease/rights fence and private object-key hardening |
| [#789](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/789) | fix(feature2 F2-26): reject Unicode spoofing in private ASR word review |
| [#788](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/788) | fix(feature2 F2-27): deny stale private sentence retake after storage write |
| [#784](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/784) | fix(feature4 F4-10): clear cancelled clip drags before unrelated drops |
| [#780](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/780) | feat(feature2): batched F2-02/F2-04/F2-21 source hardening, one CI boundary |
| [#779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779) | Feature4 batched source integration: F4-03/04/10/13/14/15 with one CI boundary |
| [#777](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/777) | fix(feature2 F2-29): deny private audio success after post-write revocation |
| [#776](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/776) | fix(feature2 F2-02): reject invisible Unicode control spoofing in retailer claims |
| [#773](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/773) | Feature4 F4-04: fail-closed encoded editor cut-boundary parity checks |
| [#770](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/770) | feat(feature4 F4-12): private caption readability review hints |
| [#767](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/767) | fix(feature2 F2-12): fence stale private workflow trace responses |
| [#766](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/766) | fix(feature2 F2-31): revalidate signed editorial rights before handoff |
| [#763](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/763) | Feature5 F5-13: reject ambiguous/nonfinite Azure A100 quota snapshots (GPU OFF) |
| [#762](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/762) | fix(feature4): fence private 60s runner output ancestry (F4-01) |
| [#759](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/759) | fix(feature2 F2-10): deny stale private uploads after same-metadata File replacement |
| [#758](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/758) | fix(feature2 F2-21): recheck CPU policy after reservation and reject forged receipts |
| [#757](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/757) | fix(feature7 F7-03): handle async reviewer host refusal without false approval |
| [#754](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/754) | fix(feature4): atomic no-clobber stock QA downloads (F4-13) |
| [#753](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/753) | test(feature4): reject gapped 60s scene-visibility receipts (F4-02) |
| [#751](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/751) | fix(feature2 F2-17): validate signed ASR hash and model metadata |
| [#750](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/750) | fix(feature2 F2-09): controlled denial for missing pinned Kokoro cache |
| [#749](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/749) | fix(feature2 F2-30): deny Standard voices in verified Azure neural catalog |
| [#748](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/748) | fix(feature7): fail closed on Unicode caption spoofing in review timeline |
| [#747](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/747) | fix(feature7): reject backdated local review approvals and claims |
| [#745](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/745) | test(feature4): fail closed on frozen encoded video scenes (F4-04) |
| [#743](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/743) | fix(feature2 F2-18): reject invisible Unicode in pronunciation review evidence |
| [#742](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/742) | fix(feature2 F2-03): deny prompt draft success after post-CAS editor revocation |
| [#741](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/741) | fix(feature7): require cue-local speech alignment before review QA passes |
| [#739](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/739) | fix(feature4): truthful fixed-gain music preview and unverified source-audio guard (F4-06) |
| [#736](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/736) | fix(feature7): fail closed on malformed source caption projection |
| [#735](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/735) | Feature4 F4-04: opt-in encoded duplicate editor QA (mock only) |
| [#734](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/734) | Feature5 F5-02: fail-closed F2 shot offset and camera types in F3 handoff (GPU OFF) |
| [#733](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/733) | fix(feature4): seek muted source footage with timeline frame jog (F4-08) |
| [#732](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/732) | test(feature4): gate final AAC narration fade envelope on decoded bytes (F4-07) |
| [#731](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/731) | fix(feature4): bind encoded motion QA to immutable private MP4 bytes (F4-11) |
| [#725](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/725) | fix(feature7): harden offline CPU wheelhouse archive trust boundary |
| [#724](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/724) | Feature #5 F5-14: opt-in read-only checkpoint SHA-256 audit (GPU OFF) |
| [#723](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/723) | fix(feature4): fail-closed encoded edit QA and mid-download lease/rights fences |
| [#720](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/720) | fix(feature2 F2-29): require atomic dual-asset private MP3/WAV receipts |
| [#719](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/719) | fix(feature2 F2-02): reject Unicode-disguised unapproved discount claims |
| [#718](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/718) | fix(feature7): reject private video staging when rights change during CPU probe |
| [#717](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/717) | Feature #5: fail-closed ComfyUI loopback JSON boundary (GPU OFF) |
| [#716](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/716) | fix(feature4): no-clobber private audio QA receipts and cleanup on race |
| [#715](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/715) | fix(feature4): bind Feature7 edit commands to persisted reviewer snapshot |
| [#713](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/713) | fix(feature2 #15): require complete PCM WAV for CPU benchmark evidence |
| [#712](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/712) | Feature5 F5-02: deny recursive direct Feature2 editorial packets (GPU OFF) |
| [#711](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/711) | fix(feature4): apply reviewed transitions to actual footage track (F4-05) |
| [#710](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/710) | fix(feature4): fence stale lease and revoked rights during media staging (F4-15) |
| [#707](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/707) | fix(feature2): harden Unicode retail claims and signed RSS headline review |
| [#705](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/705) | feat(feature4): same-head 15/30/60 encoded MP4 export evidence matrix |
| [#704](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/704) | fix(feature2 #8/#12): fence private audit CAS after tenant revocation |
| [#701](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/701) | fix(feature4): cancel timeline resize on tenant, approval and pointer lifecycle changes |
| [#700](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/700) | fix(feature2 #20): block original WAV storage success after tenant revocation |
| [#697](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/697) | fix(feature2 #27): one-shot private sentence retake job/tenant binding |
| [#695](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/695) | feat(feature4): hash-bind 30s HyperFrames CPU benchmark to encoded MP4 |
| [#690](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/690) | fix(feature4): prevent staged media mutation during v2 CPU render |
| [#686](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/686) | feat(feature4): encoded duplicate timeline parity via trusted HyperFrames renderer |
| [#684](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/684) | fix(feature2 #2/#4/#29): private MP3/WAV and Unicode editorial safety |
| [#545](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/545) | test(feature2): full GPU-OFF 15/30/60s premium Diwali creative flow and readiness gate |
| [#531](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/531) | fix(feature2): lock five garment traits and forbid covert offer claims in cinematic scripts |
| [#526](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/526) | feat(feature2): review-signed editorial-only Feature4/5 director handoff (stacked on #514) |
| [#465](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/465) | Feature #5 GPU-OFF Wan2.2: real Feature3 producer integration, private imports and 4/4 CI |

## Safety and acceptance checklist

- For each duplicate: compare changed files and behavior against exact current keeper head; verify original tests plus stronger negative cases; comment old and keeper SHAs; close old without merge and do not mark DONE.
- For an integration: verify changed paths and authorizations, effective reviews, exact-head 4/4 CI, branch/parent compatibility, expected-head guarded merge, then fresh main 4/4 CI; only then update source-integrated status with an accepted task ID.
- This snapshot is submitted for review, not a basis to bypass protected approvals, alter existing deployments, or activate paid inference.


## 2026-11-10 follow-up — 50-PR bounded parallel triage and verified source integrations

This is a **new live checkpoint**, not a replacement for the earlier historical 119-open inventory. Latest GitHub searches at end of batch: **100 open PRs (81 draft, 19 non-draft)**. Counts can change independently; do not subtract raw PR counts from accepted task IDs.

- Inspected open status, source/base branch and exact head for **50 previously open PRs**; fetched their full changed-file inventories; compared all fifty historical source heads against their current intended keeper/feature parent. All 50 source histories diverged from current keeper history, so ancestry alone was *not* evidence of duplicate code. A subset of actual source/test blobs and original tests were additionally compared; unmatched safety guards and failed/outdated CI candidates were **skipped, not force-merged or discarded**.
- Feature #2 (25 reviewed): #832 #821 #801 #797 #796 #789 #788 #780 #777 #776 #767 #766 #759 #758 #751 #750 #749 #743 #742 #720 #719 #713 #707 #704 #700. Existing keeper #848 / parent #551 remains the integration target; no source PR here was declared duplicate solely due to ancestry. #749/#750/#759 source tests still have unique negatives and their historical exact-head CI was red; retain pending independent reconciliation rather than weakening tests.
- Feature #4 (21 reviewed): #852 #851 #850 #845 #841 #839 #838 #837 #835 #831 #830 #828 #827 #824 #822 #816 #815 #808 #803 #799 #792. Exact-head original source PR #838 (F4-08 bounded finite frame seek) passed [CI 4/4 #41070937220](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41070937220) and was safely squash-merged to existing Feature4 parent #322 as **`73055a0beac66cff9d7f58f1847b9e07061564ad`**; old PR is merged/closed, original task remains IN PROGRESS. Fresh parent push #42760121390 and PR merge-ref #42760128811 started; exact-head postmerge main acceptance remains unverified. #815 and #803 old source heads had separate green CI but are currently sensitive/cross-feature or rebase-dependent; no prohibited forced merge. #799/#845 final source CI failed and were skipped without repair, per batch strategy. Issue #650 ZIP limit remains unaltered.
- Feature #5 (4 reviewed): #763 #717 #724 #465. Old #763 was **closed as superseded** (not directly merged) after its unique F5-13 finite GPU quota guards, original synthetic negatives and handoff were preserved through [PR #896](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/896), source CI [#42688235824](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42688235824) **4/4**, Feature5 parent merge **`19d49acb58ef35db62c81cb01110b140d40c451e`**, and all four merged file Git blob SHA matches. Original F5-13 task still IN PROGRESS. #717/#724 still contain unintegrated source/tests, and #465 is the large cross-feature parent; retain.
- **50 triaged, 2 original PRs retired by merge/supersession (#838, #763), 48 retained pending actual tests/reconciliation/review**. This is a PR audit count, *not* 48 implementation failures or a claim that 50 parallel coding agents ran. The repository allows up to 10 independently claimed implementation tasks at once; read-only inspection was batched within connector limits.
- No actual model inference, GPU/paid providers, cloud or SQL mutations, production release, customer-asset signoff or WineShopPOS changes. Keep original task progress unchanged until exact eligible main 4/4 and independent protected approval.


### Postmerge CI follow-up (same 2026-11-10 50-PR batch)
- **Feature4 #838 merged feature-only SHA `73055a0b`**: fresh parent push [#42760121390](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42760121390) FFmpeg/media job failed with **exit 124 (timeout)**; other completed jobs had Python/Supabase success and frontend was still in progress at check. PR #322 merge-ref [#42760128811](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42760128811) also had FFmpeg exit 124 and protected release ZIP Python failure. Do not count full parent 4/4 or main acceptance. Per owner batch instruction, **defer, do not repair/retry this task within this pass**, and move to other independent work.
- **Feature5 #896 merged parent SHA `19d49acb`**, preserving original #763: fresh parent push [#42758853513](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42758853513) **failed frontend and FFmpeg**, while Python and Supabase passed. Original exact #896 source-head [#42688235824](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42688235824) remained 4/4 green; a source-only success is not accepted parent/main CI. Defer repair under this 50-PR pass.
