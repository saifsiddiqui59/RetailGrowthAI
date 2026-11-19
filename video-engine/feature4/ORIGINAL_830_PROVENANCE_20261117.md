# Feature4 F4-06 original audio gain integration checkpoint — 2026-11-17

- Original #830 head `a86884dd1d676719b9000515dec0cdfe4df06ffb` stacked on old #828 contains a narrowly bounded four-channel gain contract, renderer wiring, trusted cross-feature source lowering, and negative tests for inert, missing, unknown, NaN, float-step, string and bool controls.
- Source-backed directly into surviving #779 as **six original unchanged Git file blobs** (Python 4 source/tests and two handoffs); no whole old-parent merge, no JS UI gain control enabled.
- Audio output fixed `data-volume` limits and preexisting music ducking remain required. This source-only integration does not establish actual decoded final AAC gain parity, hosted tenant authorization, audio listening quality, music license, publication signoff, main merge or original F4-06/F4-07 task DONE.
- Follow-up: re-validate #779 exact-head source tests and selectively reconcile into newer main-targeted F4 parent #322 while preserving its footage transitions, lease and all-asset rights checks. GPU/paid/PROD/WineShopPOS OFF.
