# Source preservation: original F4-02 #753 — 2026-11-17

Original PR head: `eeec8c363627b1085cfff33dcc62d85a57973800`. Source was F4-02 v2 minute visibility receipts; surviving #779 currently requires *v3* full-reel continuous near-black scan. Only the missing **contiguous positive finite 12-window coverage** guard was ported, together with original four fixture tests adapted for v3 required fields. Never restore the older v2 schema over v3. Original distinct tracker/handoff text follows.

## Original tracker excerpt
> ## 2026-10-30 — F4-02 additional negative coverage (source proposal)
> A dedicated stacked branch proposes a fail-closed `feature4_minute_quality_receipt.validate_visibility_evidence` contiguous-window check and deterministic negative tests. It prevents a 60-second QA report when both provenance and visibility JSON consistently skip or overlap time, or contain nonfinite/zero-length scene windows. **F4-02 remains IN PROGRESS** until exact-head CI, the actual updated private 60s media+SHA+report chain, coordinator integration and acceptance. F4-01 and F4-12 remain unverified for the new native encoded minute; no production approval is implied. Shared blocker #650 remains with coordinator.

## Original handoff excerpt
> ## 2026-10-30 — F4-02 full-minute visibility QA integrity (proposed, not integrated)
> - Dedicated review branch `fix/feature4-visibility-contiguous-windows-20261030` based on Feature4 PR #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f`. New guard in `feature4_minute_quality_receipt.py` requires 12 finite, positive, contiguous scene windows spanning exactly 60 seconds before a technical-only receipt can pass; matching forged provenance and sample JSON may not omit or overlap time.
> - Added `tests/media/test_feature4_visibility_window_integrity.py` for contiguous positive, gapped/overlapping forged JSON, incomplete last window, NaN/infinite/nonpositive duration, and unexpected metadata. This is deterministic mocked JSON regression only, **not** a newly rendered 60s video or approved product media.
> - Integration and QA pending: targeted Python/uv and exact-head four-job CI, coordinator review into #322/main, a new private native 60s encoded render and actual human visual acceptance. The existing Python ZIP >120 failure is coordinator-owned issue #650; no guard relaxation, GPU/PROD/paid inference, hosted SQL, or WineShopPOS changes.

Still **F4-02 IN PROGRESS**. No actual approved private 60s render, complete human visual acceptance, legal rights, main merge or PROD. CPU/mock-only; GPU/paid/cloud/WineShopPOS untouched.
