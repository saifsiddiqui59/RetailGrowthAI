# Feature5 GPU-OFF artifact-lock source recovery (2026-11-19)

Original draft [#323](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/323) at immutable source head `ffc464c09f719a0bfb6b15b5c34608f89d76234b` remains open and conflicted. This focused current-main branch restores four **exact original Git blob** files without importing its outdated GPU worker, cloud files, feature-shared contracts, or 13 historical feature documents:

- `feature5_motion/contracts.py` — original blob `11825c50821c38b2b4d7fffbec837b0ee2cea4a9`
- `feature5_motion/artifact_lock.py` — original blob `a526ff2f53bef9a2719931bba714ef3f74f34e89`
- `feature5_motion/seal_artifacts.py` — original blob `dec0f4f09bb57a4256839e739ab099d033659fb4`
- `tests/ai/test_feature5_artifact_lock.py` — original blob `41004b3e6c50466bb865538a54e226f62fac062e`

The only non-original code is a minimal side-effect-free `feature5_motion/__init__.py` so importing artifact tests cannot import the legacy runtime/worker. The operator may *construct an offline unsigned candidate* from synthetic or **already authorized** files; no installed model, inference, paid resource, CUDA, deployment, or Azure Files remote 34GB+ scan is run here.

CI is required before merging; `python -m unittest discover -s tests/ai -p 'test_feature5_artifact_lock.py'` is the specific offline regression. A 4/4 CI pass proves only source contracts on synthetic local bytes, **not** commercial model license, real model weight SHA, Dev/Prod operation, F5 parent completion, GPU readiness or 22 original F5 task DONE receipts. The original #323/#125 and latest #724 require independent review and separate integration with the current source-of-truth branch.
