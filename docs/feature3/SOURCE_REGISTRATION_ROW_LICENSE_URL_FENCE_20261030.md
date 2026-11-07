# Feature #3 — source registration RLS-row and license URL fail-closed guard

Scope: **F3-03** (source-rights metadata verifier) and **F3-13** (malformed/cross-tenant rights negative regression). Independent source-only security batch; no hosted release or rights approval.

- `TenantStore.feature3_source_asset` rejects non-object PostgREST rows and non-string MIME types instead of raising an unhandled exception.
- For non-owned media, license-evidence URL must parse as an HTTPS authority with a hostname, no userinfo, no whitespace/control characters and a bounded length. A bare `https://` prefix is not evidence.
- Offline `tests/api/test_feature3_source_proof.py` covers malformed rows, forged authorities and a valid HTTPS control. All responses remain **registered source metadata only**, not verified bytes, consent, commercial license or GPU permission.

**Release status:** Proposed source change only. Exact-head CI and coordinator review required; accepted integration plus fresh 4/4 main CI is required for DONE. Even after source merge, F3-03 and F3-13 remain pending actual licensed original media, signed DEV tenant tests and provider failure injection.

**Safety:** GPU OFF, no inference, no Azure queue send, no hosted Supabase SQL mutation, no PROD, no WineShopPOS. Existing PRs #693/#703/#706/#689/#699/#687/#709/#708/#683 are not modified or duplicated. Coordinator alone owns `coordination/task_progress.json` and canonical project state.
