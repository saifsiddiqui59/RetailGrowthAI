# Coordinator review: Issue #650 — Azure Functions runtime manifest

This is a **draft coordinator-owned packaging fix**, not a merged or deployed change.

The current PR #551 merge ref combines 43 campaign API, 42 poster engine, four video engine and 35 `ai_agents` Python sources (124 Python members), plus root wrapper, requirements, host and three FFmpeg distribution files: **130 ZIP entries**. The protected **120 ZIP-member limit** in `verify_zip` rejects the archive before the rollback/poison release tests run.

The patch retains the original mandatory list, 20-minute host timeout, 25-minute DB lease, 780-second FFmpeg timeout, static ELF permissions, third-party notices, ZIP byte limits, source traversal checks and all release tests. It changes only `ai_agents` production inclusion from every `*.py` to the explicit reviewed 15-module set already shipped on main. On that combined source tree, the expected count returns to **110 entries**, leaving 10 slots of headroom.

Every packaged Python source is parsed with AST to check static and literal `ai_agents` imports against this list, including Feature2 AI routes and disabled-by-default trigger code. The new independent unit tests confirm 20 synthetic offline agent modules do not inflate the packaged ZIP, an undeclared future worker dependency fails closed, and a missing required agent fails. This **does not prove dynamic imports built from variables**; coordinator approval requires source-level audit and actual extracted-zip Functions indexing with all registered queue, timer and HTTP routes, including disabled operator flags.

**Not shipped:** Kokoro 140 MB original model, OpenPronounce 2.5 GB checkpoint, real audio/VTON or private JWT/ASR route. Those need independent reviewed deployment boundaries before activation. No GPU or Azure DEV/PROD mutation.

Review [issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) and [Feature2 draft #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) together. Do not merge either without four exact merged-head jobs green and a production import smoke; coordinator owns shared release controls.
