# Issue #249: legacy protected workflow #887 patch archive (2026-11-19)

Old [PR #887](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/887), exact original head `cbb0a8b1fcb93608b5a15e5f6737b1ba73e8e171`, was an independently unreviewed manual-only protected DEV Azure incident diagnostics workflow. The original executable workflow is NOT added to current-main; its patch is archived here as nonexecuting text. Current more recent diagnostics exist in Issue #249 / #921/#939/#965/#968/#995, subject to their own independent ops/security review.

Do not dispatch the old workflow, infer protected Auth, bypass manual approvals, claim original 503 fixed, or cause Azure/GPU/paid/PROD/WineShopPOS changes.

## Exact original GitHub changed-file patch

File: `.github/workflows/p0-249-incident-platform-readonly-manual.yml`

~~~~diff
@@ -0,0 +1,56 @@
+name: RetailGrowthAI #249 incident-window host/DrainMode audit (read-only)
+# Manual, DEV-scoped, Azure OIDC. No HTTP tests, Azure writes, log-content export,
+# configuration changes, paid always-ready, user/shop data or GPU invocation.
+on:
+  workflow_dispatch:
+permissions:
+  contents: read
+concurrency:
+  group: rgai-249-incident-platform-readonly
+  cancel-in-progress: false
+jobs:
+  diagnose:
+    if: github.repository == 'saifsiddiqui59/RetailGrowthAI' && github.ref == 'refs/heads/main'
+    environment: dev
+    runs-on: ubuntu-24.04
+    timeout-minutes: 20
+    permissions:
+      contents: read
+      id-token: write
+    env:
+      RGAI_DEV_EXPECTED_SUBSCRIPTION: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
+    steps:
+      - uses: actions/checkout@v7
+        with:
+          persist-credentials: false
+      - name: Compile and validate immutable incident scope before Azure sign-in
+        shell: bash
+        run: |
+          set -euo pipefail
+          python3 -m py_compile ops/p0_249_recent_http_platform_readonly.py
+          python3 - <<'PY'
+          import sys
+          sys.path.insert(0,"ops")
+          from p0_249_recent_http_platform_readonly import WINDOWS,KINDS,build_query
+          assert len(WINDOWS)==4 and set(KINDS)=={"host","requests","activity"}
+          for label,start,end in WINDOWS:
+              for kind in KINDS:
+                  q=build_query(label,kind)
+                  assert start in q and end in q
+                  assert "rgai-dev-functions-d4e5ddbd" in q
+                  assert q.endswith(" | take 80")
+          print("P0249_IMMUTABLE_INCIDENT_SCOPE=PASS")
+          PY
+      - uses: azure/login@v3
+        with:
+          client-id: ${{ secrets.AZURE_CLIENT_ID }}
+          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
+          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
+      - name: Inspect exact known HTTP timeout windows only
+        shell: bash
+        run: |
+          set -euo pipefail
+          python3 -u ops/p0_249_recent_http_platform_readonly.py
+      - name: End DEV read-only Azure session
+        if: always()
+        run: az logout >/dev/null 2>&1 || true
~~~~

## Outstanding
Original #249 gateway 503 and Y1 ZIP issue #650, tenant JWT/RLS tests, approved operator workflow and private rights remain OPEN. This is source archival and PR-hygiene only, not feature/code DONE.