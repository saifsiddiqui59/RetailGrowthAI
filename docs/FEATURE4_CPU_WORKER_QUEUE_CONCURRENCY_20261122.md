# Feature4 CPU isolated queue concurrency source-only guard

The legacy v1 API's `host.json` does not cap Azure Storage Queue batches, so packaging that same host into the CPU-intensive Feature4 worker could schedule multiple full-HD FFmpeg renders concurrently on a **single** 2-GiB FC1 instance.

The separate native worker now packages only `azure-functions/feature4-cpu-worker/host.json` with a 20-minute timeout, `batchSize: 1`, `newBatchThreshold: 0`, and disabled dynamic concurrency. The packager refuses altered/absent limits and CI validates that the existing v1 API host file remains unchanged.

This is **source code only**, not proof of Azure hosted trigger execution or worker capacity. Before activating any billable render, confirm one queue message at a time under a load/poison test, test 780s renderer budget/25m claim fencing, the private MP4 SHA readback, exact tenant license/rights and the 2-shop signed JWT E2E. No Azure or Supabase mutation performed here.
