# Feature5 F5-13 — reviewed offline manifest stable identity reconciliation

Date: 2026-10-31. **SOURCE ONLY / GPU OFF / F5-13 remains IN PROGRESS.**

## Actual issue and source resolution

Feature5 draft [#786](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/786) had exact-head [CI #41026927515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41026927515) all four jobs green but was based on an older feature branch. GitHub rejected a straightforward merge to consolidated [#781](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/781) with **405 merge conflicts**. No forced merge or canonical contract edits occurred.

Manually reconciled only the actual F5-13 source semantics from #786 into the current #781 tree, preserving the newer bounded JSON parse and source audit paths rather than silently overwriting them. Owned files: `feature5_motion/infra/wan22_build_context_gate.py` and `tests/ai/test_feature5_wan22_build_context_gate.py`.

The offline reviewed JSON input reader now fails closed unless the OS supplies **O_NOFOLLOW and O_NONBLOCK**. It opens a bounded regular single-link descriptor and compares **dev, inode, file mode, link count, byte size, nanosecond modification and change times** before/after read. It also checks the **original pathname's current identity** after the final descriptor read, so a same-byte replacement cannot make an orphaned-but-stable descriptor appear to be the reviewed file. JSON duplicate keys/nonfinite values still fail closed.

Added deterministic **CPU-only** negative tests for symlinks, hardlinks, a same-byte original path swap during the descriptor read, and descriptor `ctime_ns` drift while other stat fields match. Earlier positive and malicious JSON tests are retained. No vendor source/wheel file is modified; no image, CUDA build or paid inference runs.

## Acceptance and dependency

- **Review/merge boundary:** new combined #781 exact-head 4/4 required before this reconciliation is source TESTED, then coordinator owns integration of #781 into Feature5 parent #465, parent chain and main. Close #786 as superseded only when #781's actual source/CI independently confirms reconciliation.
- **Release blocker:** independently approved CUDA image digest, the complete real wheel/ComfyUI source inventory, actual OCI build + immutable digest/SBOM and required commercial/redistribution licensing review are **NOT** supplied. F5-13 remains **IN PROGRESS**, not integrated DONE or production-ready.
- **Safety:** no GPU, AI model, Docker build, Azure/hosted Postgres, PROD, customer media, or WineShopPOS changes; no cost incurred.

Original F5 ledger remains **0 integrated DONE / 3 IN PROGRESS / 19 BLOCKED (22 total)**.
