# RetailGrowthAI — GitHub to Azure DEV connection (OIDC)

**Current status (2026-10-22): READ-ONLY GITHUB-TO-AZURE DEV OIDC LOGIN VERIFIED.** The latest attempt of [Azure DEV OIDC workflow run #39780713421](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39780713421) succeeded: the environment-secret checks, `azure/login@v3` federated authentication, and selected-subscription identity check all passed. This verifies authentication/subscription access, **not** resource-group Reader/Contributor scope, infrastructure provisioning, or deployment approval. No Azure deployment is authorized.

This setup is **only** for `saifsiddiqui59/RetailGrowthAI`. Never reference WineShopPOS subscriptions, resource groups, secrets, or production resources.

## Authentication architecture

Use passwordless Microsoft Entra workload identity federation from a *manually triggered*, main-branch-only GitHub Actions job. The workflow uses `azure/login@v3` and requests `id-token: write` only in its verification job. No client secret, certificate/private key, storage connection string, service-role secret, or Azure publishing profile is needed in GitHub. Existing continuous-integration jobs remain secret-free and do not deploy.

This GitHub repository was created after July 15, 2026, so its default GitHub OIDC `sub` uses immutable owner and repository numeric IDs. The **expected exact subject** for `environment: dev` is:

```text
repo:saifsiddiqui59@80577424/RetailGrowthAI@1429348524:environment:dev
```

If the Azure GitHub Actions template displays the old mutable subject without `@...` IDs, select **Other issuer** / a custom subject instead. Verify the actual GitHub OIDC claim before trusting a credential if the repository settings change. Never use a broad/wildcard subject.

| Federated credential property | Value |
| --- | --- |
| Issuer | `https://token.actions.githubusercontent.com` |
| Subject | `repo:saifsiddiqui59@80577424/RetailGrowthAI@1429348524:environment:dev` |
| Audience | `api://AzureADTokenExchange` |
| Suggested credential name | `retailgrowthai-github-dev-oidc` |

## Steps requiring owner action in GitHub UI

1. Open [RetailGrowthAI environments](https://github.com/saifsiddiqui59/RetailGrowthAI/settings/environments) → **New environment** → name it exactly `dev` (lowercase).
2. Restrict the environment's deployment branches to **Selected branches: `main`**. If reviewer protection is available, require approval. Do not use a shared production environment.
3. Open that environment's **Environment secrets** → add each:
   - `AZURE_CLIENT_ID`: **Application (client) ID** of the Azure app named `retailgrowthai-github-dev`
   - `AZURE_TENANT_ID`: **Directory (tenant) ID** from the app overview
   - `AZURE_SUBSCRIPTION_ID`: **Subscription ID** of the isolated RetailGrowthAI DEV subscription
4. Do **not** put `AZURE_CLIENT_SECRET` or any live backend/Supabase/Storage secrets in the repo. The three IDs are identifiers rather than passwords, but store them in protected environment secrets for consistent, least-exposure setup.

**Connector limitation:** The connected ChatGPT GitHub integration can commit workflow/docs and inspect runs, but cannot create environments or set GitHub Actions secrets through its currently available actions. Complete these GitHub UI steps yourself.

## Steps requiring owner action in Azure Portal

1. In [Azure portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → `retailgrowthai-github-dev` → **Certificates & secrets** → **Federated credentials** → **Add credential**.
2. Configure the issuer, immutable subject, and audience above, using a custom/Other-issuer option if the GitHub picker does not include numeric immutable IDs. Do **not** create a client secret.
3. In the *existing, dedicated RetailGrowthAI DEV resource group*, go to **Access control (IAM)** → **Add role assignment** → assign only the **Reader** role to the `retailgrowthai-github-dev` **enterprise application/service principal**. Subscription-wide Contributor/Owner is unnecessary and unsafe for this verification.
4. Identify the correct DEV Azure subscription ID in **Subscriptions**. Do not use WineShopPOS resource groups. If a dedicated DEV resource group does not exist, do not create one yet; ask for approval before infrastructure changes. You can complete the OIDC authentication check after assigning appropriately scoped read access.

The app registration itself does not grant Azure Resource Manager access: role assignment and federated credential are independent requirements.

## Read-only verification

After the workflow is merged onto `main` and the steps above are complete:

1. Open [GitHub Actions](https://github.com/saifsiddiqui59/RetailGrowthAI/actions).
2. Select **Azure DEV OIDC connection check (read-only)** → **Run workflow** → branch `main`.
3. Confirm **Verify federated Azure login only** succeeds. The test outputs subscription *name and enabled state* only, and performs no provisioning or deployment.
4. If a job reports missing `AZURE_*` secrets, correct the `dev` environment values. If Azure says no matching federated identity, compare the **exact** immutable OIDC `sub`, issuer and audience. If Azure says authorization denied, inspect DEV service-principal IAM and subscription selection.

Do not mistake a successful login test for permission to deploy or proof that live API, Functions, Queues, FFmpeg, Supabase migrations, or browser-to-cloud E2E work. Current application deployment is still blocked by timeout/lease discrepancies and separate owner approval. See `infra/azure/README.md` and `docs/NEXT_TASK.md`.

Sources:
- [GitHub immutable OIDC subject reference](https://docs.github.com/en/actions/reference/security/oidc)
- [Microsoft Azure OIDC from GitHub Actions](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure-openid-connect)
- [Azure/login action](https://github.com/Azure/login)

## Initial verification failure (historical; superseded) — 2026-10-22
- The [manual read-only run #39780713421](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39780713421) **failed** in `azure/login@v3` with `AADSTS70025`: Entra app `retailgrowthai-github-dev` has **no configured federated identity credentials**. The workflow passed its nonempty three-environment-secret guard, so add the **exact** issuer/immutable subject/audience credential above to the correct Entra app. Then verify narrow Reader RBAC and manually re-run from `main`.
- This describes the **initial failed attempt only**, subsequently superseded by a successful rerun. No client secret was needed; neither CI nor OIDC authentication grants deployment approval.

## Successful verification rerun — 2026-10-22
- Inspected the **latest attempt** of [Azure DEV OIDC workflow run #39780713421](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39780713421): job `Verify federated Azure login only` completed **successfully**. Its `Validate Azure environment secrets are present`, `Authenticate with Azure using GitHub OIDC`, and `Verify selected Azure subscription (no resource changes)` steps all completed successfully.
- The earlier `AADSTS70025` failure is historical; the latest observed OIDC login succeeds. Exact federated credential and resource-group IAM configuration were not independently enumerated; do not infer a write role from successful subscription lookup.
- No Functions/queues deployed, no hosted Supabase migration applied, and no WineShopPOS resource touched. Next gates: durable poison/replay/fencing, approved runtime benchmarks, scoped IAM inspection, and **explicit owner authorization** before DEV deployment.
