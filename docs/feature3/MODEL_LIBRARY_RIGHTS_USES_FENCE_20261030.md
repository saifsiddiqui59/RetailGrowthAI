# Feature #3 independent reusable-model rights grant fence — 2026-10-30

**Task IDs:** F3-03, F3-11, F3-12, F3-13. **Status:** SOURCE PROPOSED, not integrated DONE.

The offline server-side `model_library_v2.import_model_image` previously converted independently supplied rights uses to a Python set without validating member types, duplicates or unknown permissions. A nested unhashable item raised an unexpected TypeError, while a grant containing all required uses plus an unrelated scope was accepted. The proposed change requires exactly the three known reusable-image uses, each a distinct string, before private byte persistence or registration.

Verification: deterministic Python tests cover malformed/unhashable grants, duplicates, forged extra scopes, incomplete grants, and exact list/tuple/set/frozenset grants. No external media, hosted SQL, Azure queue, GPU, paid inference or PROD operations. **Do not mark this task DONE until exact-head four-job PR CI, coordinator review/merge, and fresh four-job main CI.**

**Remaining gates:** F3-LICENSED-MEDIA (Feature3 owner; independently reviewed customer original, likeness/commercial license and signed reviewer approval), #471/#325 (Feature3/coordinator; mounted authorized no-URL PNG route and signed tenant negative tests), #249 (Azure lead; signed DEV 503-free hosted response), and two real isolated DEV owner identities (Auth Admin provisioning plus RLS role tests). Fixtures never constitute commercial rights or genuine generated media.
