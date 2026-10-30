# Feature3 F3-10 — Private model Blob revocation failure fence (source-only)

## Scope

The browser private model-preview cleanup helper previously removed an owned local `blob:` URL from its tracking array *before* invoking the revocation callback. If that callback threw, the caller could no longer retry cleanup using its own URL registry. This is an in-memory privacy and lifecycle defect, not a remote Storage revocation.

The helper now revokes first and removes the tracked URL only after the callback returns successfully. A deterministic Node regression injects a throwing revocation callback and proves the URL remains tracked for a subsequent successful retry. Existing cross-origin/unowned URL denial is unchanged.

## Evidence and remaining gates

- Original task: **F3-10**, private Blob/cache/revocation lifecycle. This closes only the isolated local cleanup failure case, **not** F3-10 hosted acceptance.
- Proposed together with the independent F3-13 state-envelope guard in draft PR #812; branch `feat/feature3-f3-13-history-envelope-20261030`.
- Exact-head four-job CI and coordinator review/merge + fresh main 4/4 required; no task-progress DONE event until accepted.
- Current approved model/media rights, actual mounted no-URL binary route, expired signed-link semantics and signed DEV tests remain separate dependencies. No GPU, paid model, Azure/SQL/PROD writes, commercial media or WineShopPOS changes.
