# RetailGrowthAI

Part 1 coordinator bootstrap for a low-cost, multi-tenant marketing SaaS. See [project state](docs/PROJECT_STATE.md), [architecture](docs/ARCHITECTURE.md), [v1 contracts](docs/INTERFACES_V1.md) and [parallel branch ownership](docs/PARALLEL_WORK.md).

## Run the frontend (Git Bash in VS Code)

```bash
cd E:/RetailGrowthAI
git pull origin main
cd frontend
npm install
npm test
npm run build
npm run dev
```

The React/Vite app serves local routes `/`, `/campaigns` and `/account`. All displayed campaign records come from `frontend/src/features/campaigns/fixtures/sample-campaign.json` and are explicitly mock data. No authentication, AI calls, rendering, database, publishing or cloud resources are configured.

## Shared contract validation

```bash
cd E:/RetailGrowthAI
python tests/contracts/test_campaign_fixture.py
cd frontend
npm test
npm run build
```

Python validation uses the standard library; frontend requires Node 22 and npm. CI executes `npm install`, both contract tests and the Vite build. A dependency lockfile is not yet checked in; the first coordinator dependency follow-up should generate/review `frontend/package-lock.json` on a machine with npm registry access before switching to `npm ci`.

Only coordinator-owned files are changed on `main`; feature teams submit PRs from branches listed in `docs/PARALLEL_WORK.md`.
