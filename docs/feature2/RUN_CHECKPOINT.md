# Feature #2 durable run checkpoint — 2026-10-30 (F2-08)

- Task: **F2-08** blind A/B score revision history, source hardening **IN PROGRESS**, not integrated DONE.
- Branch: `feat/feature2-f2-08-blind-history-integrity-20261030`, stacked on Feature2 draft PR **#551**; own draft PR **#842**.
- Pre-checkpoint code/test head: `19f1c62ef7ab1e41841547218c8412f75799bf6e`.
- Source: `ai-agents/src/ai_agents/feature2_creative_quality.py` — reject boolean revision 1, identical A/B original candidate digests, and duplicate signed score receipt digests across private history revisions.
- Tests: `ai-agents/tests/test_feature2_creative_quality.py` — three hostile offline cases using independent mock receipt verifier; no real human reviewer proof.
- Verification: changes committed and PR opened in GitHub. Targeted pytest **not executed in this tool run**. Exact-head CI query for code/test head returned **no PR-triggered runs**; PR #842 exact-head CI remains **not verified**, and may start asynchronously.
- Dependencies/blockers: coordinator must reconcile source with other Feature2 sibling PRs, verify exact-head 4/4, integrate to main, and verify fresh postmerge main 4/4. Hosted signed reviewer identity and tenant-private durable CAS are separate unresolved acceptance gates. No actual model, paid inference, GPU, media or PROD actions.
- NEXT: verify PR #842 exact-head CI; while pending inspect **F2-01** Azure Functions Creative Director runtime/package validation for an independently fixable offline regression. If no owned safe change exists, inspect **F2-15** CPU benchmark fake-evidence rejection; do not repeat already source-complete tasks.
- Previous independent source branches: PR **#832** F2-02 and **#833** F2-30, both draft and not merged. Do not count these as integrated DONE.


## 2026-10-30 continuation — F2-08 mutable history alias regression

- F2-08 remains **IN PROGRESS**, not source-accepted or integrated. PR **#842** was updated on branch `feat/feature2-f2-08-blind-history-integrity-20261030`.
- Source commit `b3109b73b3603fc1c21bc8a85a1568b53f6d2593`: capture a deep copy of the first private A/B history observation before invoking signer callbacks; compare the reread and original shared list against that immutable observation. This closes a stale-object-equals-itself gap when the reader reuses mutable objects.
- Test commit `33753aee27bd38f18994b040533c9cc5dd452621`: two synthetic malicious callbacks mutate score or signed receipt after first verification; expect fail-closed history-change denial.
- Test execution: **not run locally** (connected GitHub file-edit interface; no local authenticated repository checkout). Exact-head PR CI must be inspected separately. No hosted reviewer, RLS, real voice, or commercial approval evidence.
- NEXT eligible independent task: **F2-15** offline CPU benchmark evidence verification if not already covered in another active PR; otherwise inspect F2-29 FFmpeg decoder security. Do not modify canonical shared registry; coordinator reviews and merges.
