# Coordinator review: Issue #650 — Azure Functions runtime manifest

This is a **draft coordinator-owned packaging fix**, not a merged or deployed change.

The current PR #551 merge ref combines 43 campaign API, 42 poster engine, four video engine and 35 `ai_agents` Python sources (124 Python members), plus root wrapper, requirements, host and three FFmpeg distribution files: **130 ZIP entries**. The protected **120 ZIP-member limit** in `verify_zip` rejects the archive before the rollback/poison release tests run.

The patch retains the original mandatory list, 20-minute host timeout, 25-minute DB lease, 780-second FFmpeg timeout, static ELF permissions, third-party notices, ZIP byte limits, source traversal checks and all release tests. It changes only `ai_agents` production inclusion from every `*.py` to the explicit reviewed 15-module set already shipped on main. On that combined source tree, the expected count returns to **110 entries**, leaving 10 slots of headroom.

Every packaged Python source is parsed with AST to check static and literal `ai_agents` imports against this list, including Feature2 AI routes and disabled-by-default trigger code. The new independent unit tests confirm 20 synthetic offline agent modules do not inflate the packaged ZIP, an undeclared future worker dependency fails closed, and a missing required agent fails. This **does not prove dynamic imports built from variables**; coordinator approval requires source-level audit and actual extracted-zip Functions indexing with all registered queue, timer and HTTP routes, including disabled operator flags.

**Not shipped:** Kokoro 140 MB original model, OpenPronounce 2.5 GB checkpoint, real audio/VTON or private JWT/ASR route. Those need independent reviewed deployment boundaries before activation. No GPU or Azure DEV/PROD mutation.

Review [issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) and [Feature2 draft #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) together. Do not merge either without four exact merged-head jobs green and a production import smoke; coordinator owns shared release controls.


## 2026-10-31 coordinator integration gate: package-form import closure

- **PR:** #665, branch `chore/issue650-functions-runtime-closure-20261029`, base `main`. Parent code/test commits `b2fc618a2267bd03c8fca7261027d9c1d72a57a2` and `ea2715cf4a0db06fd7fc0cd6c2cc5977bd0fb183`. This checkpoint is a subsequent commit; inspect the PR head for its exact SHA.
- **Review finding fixed:** `verify_runtime_agent_imports` previously ignored `from ai_agents import excluded_module` and `from . import excluded_module` because it only checked names already allowlisted. The runtime source inventory now identifies excluded source modules, while preserving ordinary exported symbols; literal `__import__('ai_agents.excluded_module')` is also checked.
- **Changed files:** `scripts/deploy/package.py`, `tests/infra/test_functions_runtime_manifest.py`. Offline synthetic regression tests cover three excluded import forms plus legitimate symbol imports. **These new tests have not yet been verified by exact-head CI.**
- **Prior baseline:** #665 run [40936307548](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40936307548) completed 4/4 on the previous head `9ac121811e32896f3606c9314728d7be71fdc047`; it is **not** evidence for this new head.
- **Remaining blockers:** inspect actual extracted Functions ZIP import/indexing and optional route imports on the combined Feature2 #551 tree, then obtain fresh 4/4 exact-head CI and review/security approval. No merge or deployment until these gates pass. Runtime dynamic imports assembled from variables are still not proven by AST.
- **NEXT:** verify exact-head CI for #665; audit extracted-ZIP Functions indexing against #551; independently review #513 (115 files, no submitted review) for safe main integration. Feature5 #781 remains stacked on #465 and is not main-ready.
- **Environment:** GPU OFF; no paid inference, PROD, Azure write, SQL migration, or WineShopPOS changes.
