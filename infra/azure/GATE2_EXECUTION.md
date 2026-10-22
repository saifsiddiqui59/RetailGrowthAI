# Gate 2 execution — Azure DEV release package (Workstream Q)

**Status: SOURCE ONLY — NOT APPROVED.** No Azure resource was created,
configured or deployed by Q. Gate 2 is a separate explicit owner authorization.
Read the merged Workstream J packaging guidance and M RELEASE_READINESS first;
this document is the final operator sequence, not a replacement for them.
The target is only RetailGrowthAI DEV in Central India; never WineShopPOS.

## 0. Assemble an offline, immutable candidate (safe before approval)

- Pin the exact reviewed GitHub SHA and its **four passing CI jobs**.
- Keep edited DEV Bicep parameter JSON and audited Linux x86_64 static FFmpeg
  and ffprobe binaries outside the public repository. Check codec/font support
  (libx264, AAC, drawtext, xfade, fontconfig/DejaVu where required),
  licensing and third-party notices. An ELF header check and license notice
  do **not** constitute commercial-rights or runtime approval.
- Run the existing offline preparation and ZIP validator:

      bash scripts/deploy/check.sh
      python3 scripts/deploy/package.py --check
      python3 scripts/deploy/package.py --ffmpeg-dir /private/approved-linux-bins --output /private/candidate.zip

- Generate a private, hash-identified release manifest (always NOT_APPROVED):

      python3 scripts/deploy/release_package.py \
        --parameters /private/dev.parameters.json \
        --candidate /private/candidate.zip \
        --first-release \
        --commit-sha EXACT_FORTY_HEX_SHA \
        --monthly-budget-limit APPROVED_CEILING_IN_BILLING_CURRENCY \
        --output /private/gate2-manifest.json

  For an upgrade replace first-release with previous pointing to a separately
  retained known-good ZIP. The static guard validates DEV resource names,
  origin, immutable ZIP/rollback SHA256, packaged four queue triggers, the
  two-minute recovery timer and the four ARM queue declarations. The commit
  SHA is supplied metadata; it is NOT cryptographically tied to the ZIP.
  The JSON must never be interpreted as owner authorization. Do not commit
  private manifest, parameter values, credentials, billing recipients or binaries.

## 1. Required operator read-only evidence (Azure CLI OIDC context)

1. Confirm the **existing dedicated RG** is tagged app=RetailGrowthAI and
   environment=dev, in centralindia, and that expected OIDC service principal
   has direct Contributor at precisely its RG scope, with no inherited broader
   write roles. Use M's documented export variables and:

       bash scripts/deploy/azure-readonly-preflight.sh iam

   Authentication success alone does not prove IAM. Check PIM/group/custom
   grants and deny assignments manually. This check cannot run from the
   connected GitHub code interface and was NOT executed by Q.
2. Confirm Python 3.12 Flex Central India quota, storage SKU, subscription
   headroom, and budget approval. Cost budgets send alerts, **not hard stops**.
   A pre-existing DEV RG-scoped monthly Cost budget with 80%/100% enabled
   email notifications and amount at or below the approved ceiling is
   mandatory for runtime preflight; a subscription-wide budget does not qualify.
3. Run read-only ARM what-if using M's expected subscription and RG:

       bash scripts/deploy/plan.sh /private/dev.parameters.json

   Compare and explicitly approve the precise resource delta, including
   private deployment container, four queues, Flex plan/app, memory 2048 MiB,
   independently scaling maximum 1–2 instances per function group and CORS
   limited to the exact HTTPS frontend origin. Stop on any unexpected deletions
   or resource collisions.
4. Require independent **Gate 1** written approval and verified application of
   seven RetailGrowthAI DEV migrations before dispatching workers. M's worker
   scripts do not apply SQL. No PROD/WineShopPOS sharing.
5. Retain a known-good upgrade ZIP + SHA and DB/Storage backup or have a
   **separately approved first-release/no-previous-app plan**. Capture sanitized
   prior settings, queue/poison depths, monitoring configuration and rollback
   owner privately. Do not log secret values. Confirm service-only
   Supabase settings and RETAIL_STORAGE/AzureWebJobsStorage, false mock mode.

## 2. Gate 2 APPROVED FUTURE deployment sequence (DO NOT RUN NOW)

1. Owner explicitly approves target subscription/RG, reviewed SHA, names,
   approved ARM what-if, package hash, billing cap/notifications, change
   window, on-call operator and rollback. The existing scripts additionally
   require RETAIL_AZURE_DEPLOY_APPROVED=YES. These are post-approval
   procedures only.
2. Provision the initial DEV infrastructure with:

       bash scripts/deploy/apply-infra.sh --approve /private/dev.parameters.json

   Script rechecks offline DEV parameters and read-only IAM, and **refuses any
   existing Function App**. Never blindly reapply Bicep to an existing App:
   its declarative siteConfig.appSettings may erase protected secrets.
   Existing-infra updates need separate reviewed tooling/change request.
3. Verify ARM resources: isolated Standard_LRS StorageV2, private
   retailgrowth-functions-packages container, retail-campaign-planning,
   retail-reel-render, retail-campaign-planning-poison and
   retail-reel-render-poison queues. Ensure Azure storage keys remain
   protected; existing QueueClient uses shared-key connection strings.
4. Install protected backend-only config/Key Vault references through a
   separately reviewed operator action; never use VITE-prefixed service keys.
   Review exact frontend origin, permissions, retry policies and false mock flag.
5. Use already approved M code deploy guard with candidate ZIP and the
   first-release or rollback-zip flag:

       bash scripts/deploy/deploy-code.sh --approve /private/candidate.zip

   That command has cloud side effects and must **not** be run before Gate 2.
   Validate remote Python dependencies and Linux FFmpeg execution separately.
6. After code deployment, run M's **read-only** runtime phase to check the
   indexed plan_campaign, render_campaign_reel, planning_poison,
   render_poison and monitored recover_stale_jobs timer, all four actual ARM
   queues, exact CORS, secure TLS, Flex scale, backend **setting names**, and
   the RG-scoped monthly Cost budget. Name presence is not value correctness.

       bash scripts/deploy/azure-readonly-preflight.sh runtime

   Record sanitized pass/fail evidence; stop dispatch on any missing trigger,
   disabled timer, budget/scope mismatch, unsafe settings or app start failure.
7. Only after independently authorized **Gate 3**, run O's hosted-DEV E2E
   smoke using approved throwaway test identities: login, real rights-attested
   private uploads, campaign/draft, 30-second licensed render, signed URL,
   expired JWT and cross-shop denies, durable outbox retry/poison and cleanup.
   N's 1080x1920 synthetic measurements are NOT Flex-host benchmarks.

## 3. Abort criteria, rollback and recovery

- Abort for missing/stale IAM, wrong RG/subscription, cost alerts absent, wrong
  ARM delta, unavailable SKU, unapproved binaries/license, absent database
  migration/backup, inconsistent 20-minute host / 25-minute fenced lease /
  780-second FFmpeg cap, or any failed CI. Never touch WineShopPOS.
- Stop dispatch safely under operator change control; preserve queue messages,
  poison receipts, outbox fences, object history, error logs and metrics. Do
  not empty poison queues or delete tenant data to hide failures.
- For upgrades: restore the separately validated last-known-good ZIP
  **only after explicit incident approval**, recheck protected app settings,
  hosted trigger indexing, JWT/RLS, queue depth and attempt-fenced replay.
  A ZIP rollback cannot undo DB migrations or storage changes.
- For a first deployment without last-good code: disable traffic/dispatch,
  preserve audit and messages, and obtain a targeted rollback/cleanup decision;
  do not indiscriminately delete the DEV resource group.
- For DB failures: follow L's independently approved forward-fix or
  backup/PITR restore path. Never delete migration history or blindly reverse
  DDL. Reconcile in-flight jobs before reenabling consumers.
- Record actual spend, cold-start/CPU/RSS/temp use, FFmpeg codecs/rights, queue
  poison/timer monitoring, resource IDs, sign-off and responsible owner.

## Remaining evidence (still PENDING)

- Live, independently enumerated exact-RG Contributor IAM
- Region quota and approved ARM what-if
- Exact RG budget currency/ceiling and 80%/100% live alerts
- Hosted Gate 1 migrations/backup and recovery proof
- Approved FFmpeg binary provenance/codecs/licensing and realistic Flex render
- Protected settings, actual function/queue/timer indexing and poison handling
- Authorized Gate 2 decision and subsequently independent Gate 3 hosted E2E

**No cloud changes or Gate 2 authorization were performed in Workstream Q.**
