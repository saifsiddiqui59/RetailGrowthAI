# Workstream R — Azure Static Web Apps frontend-only DEV preview

Source-only preparation. **No Azure Static Web App has been created or deployed, no public URL is claimed, and no hosted API or Supabase migration is authorized.**

## Keep the existing React demo
The existing BrowserRouter, overview, campaign editor and account page are unchanged. The seven-day fixture runs offline with the existing demo notice and local JSON preview. Without intended backend/auth settings, do not claim any real planning, publishing, remote saving or rendering. Set no VITE_* variables for a public mock-only DEV preview. Never include sb_secret_*, a service-role key, an Azure credential or a deployment token in Vite environment settings: VITE_* values are embedded in the public browser bundle.

## Azure Static Web Apps configuration and build
- Repository: saifsiddiqui59/RetailGrowthAI; branch: a reviewed, CI-green main commit only.
- app_location: frontend
- api_location: empty; **do not attach backend Functions**
- output_location: dist
- Command from repository root: cd frontend && npm install --no-audit --no-fund && npm test && npm run build
- The Vite build copies frontend/public/staticwebapp.config.json to frontend/dist/staticwebapp.config.json. Assert both it and frontend/dist/index.html exist before approving upload.
- navigationFallback.rewrite is /index.html; the /assets/* bundle and missing static files are excluded from HTML rewrites. React routes /, /campaigns and /account therefore support direct refresh/deep links.
- Node config/route assertions run in the current npm test; Playwright's existing CI suite discovers frontend/e2e/static-preview.spec.mjs to exercise direct URLs and the demo without remote calls. Playwright uses only a local dev server; an Azure 200 response is NOT claimed.

## Coordinator 3 deployment handoff (workflow ownership)
Only Coordinator 3 may add or edit .github/workflows/**; coordinate with the coordinator-owned manual-only SWA workflow in PR #58. The shared workflow must retain ordinary four-job non-deploy CI, never deploy on push or pull_request, require explicit **frontend-only** owner approval, a protected GitHub environment and a separately authorized SWA deployment token. Do not provision or deploy a Static Web App under Workstream R.

After separate approval, Coordinator 3 validates RetailGrowthAI DEV isolation, spending limits and manual workflow conditions, deploys only the approved main SHA, opens the **actual** HTTPS URL and directly checks /, /campaigns, /account (including browser refresh), mock badge, no private credentials in assets, and no cross-project requests. Record observed URL, deployment SHA, CI run and rollback steps; never invent a URL.

Supabase DEV migrations, Azure backend queues/Functions and real hosted E2E have their **own independent approval gates**. No WineShopPOS changes.
