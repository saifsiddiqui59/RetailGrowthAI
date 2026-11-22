# Feature4 CPU DEV — isolated host infrastructure source

This is an **unapplied, source-only** infrastructure candidate. The target is the existing dedicated RetailGrowthAI DEV resource group `rg-retailgrowth-dev`, Central India, using existing StorageV2 `rgaid4e5ddbdf0d21d96`. It neither edits the original Flex app nor the #249 Y1 ingress or any v1 queues.

- Bicep: `infra/azure/feature4-cpu-worker-dev.bicep`.
- Separate Flex Consumption FC1 plan `rgai-dev-f4cpu-plan` and app `rgai-dev-f4cpu-d4e5ddbd`; max 1 CPU instance, 2048 MiB, always-ready omitted (scale-to-zero).
- New private app package container `retailgrowth-f4cpu-packages`, without public storage access.
- Both `RETAIL_FEATURE4_CPU_WORKER_ENABLED` and `RETAIL_FEATURE4_CPU_RENDER_ENABLED` are **false** on creation; no user-facing HTTP functions or Supabase service credential is included in source.

**Before applying:** independently verify the exact tagged DEV RG/tenant/storage, direct scoped IAM, a budget ceiling/alerts, that neither app nor plan already exists, protected environment rights, recovery from a failed new-resource deployment, the sealed Python3.11/Node22/FFmpeg/Chromium bundle and all six F4 migrations. Run Azure Bicep validation and what-if against the exact DEV target; do not auto-deploy on a normal PR or edit an existing site's app settings. Set service-only secrets in protected runtime config, provision dedicated queues after secure schema, and enable the worker only after the private queue is ready and all three non-HTTP functions index.

**Not completed:** No real Azure hosting resources, DEV SQL, tenant test identities, customer permissions, authorized media, billing or signed two-shop browser E2E have been deployed or verified by this source.
