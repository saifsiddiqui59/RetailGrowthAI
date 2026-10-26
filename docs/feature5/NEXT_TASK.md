# Feature #5 — Next tasks / gates

1. **Coordinator interface gate (P0):** map `MotionSpec`/AssetGrant to existing signed Feature3 media/Part3 source rights, existing subscription reservation, persisted lease claims, outbox, private Storage importer, without an independent schema or queue. Design review before any shared file change.
2. **Model exactness gate (P0):** pin upstream Tencent generate.py commit + downloaded weight/checksum and allowed inference mode/version. Current runner supports 480p T2V/I2V via official CLI shape but has never executed GPU inference. Validate output dimension, FPS, 5s actual generation and expected VRAM on a real licensed GPU.
3. **GPU cost and legal gate (P0):** review Tencent territory exclusions (EU, UK, South Korea), hosted-service notices/disclosure, 100m MAU clause, third-party rights, India data residency; confirm Azure Central India T4 quota and $/GPU-second. Obtain explicit paid approval before provisioning/inference.
4. **Media integration (P0):** verify existing claim attempt-token DB generation and replay fencing, input byte-signature/pixel/decompression checking via existing Feature3 importer, exact private output media path, DB-fenced registration, and media quality approval. Do not treat machine codec check as garment QA.
5. **Operational gates (P1):** secure job image staging cleanup, GPU subprocess/child-group timeout, workload profile idle scale-zero, GPU OOM telemetry and retry policy, amount-spent reconciliation and non-billable fallback to Feature4 static animations.
6. **Cross-feature acceptance (P1):** Coordinator Feature4 assembles a branded fashion Reel; Feature6 ensures human approval before publishing.
7. **CI:** inspect exact PR-head GitHub Actions after push; no mock implies real GPU output.

## Updated 2026-10-26 progress
- **Completed offline:** official CLI T2V omission of `--image_path`; I2V source flag, bounded model args, preflight image decode, timeout and CUDA gate, immutable lease-scoped private output receipt, nonfinite quota rejection and post-upload unknown-state handling. Corresponding automated mocked tests added to the standard Python CI.
- **Still blocked:** verified licensed GPU/device and actual Hunyuan output, pinned weights+runtime digest, real 480p/frame aspect/FPS verification, actual garment quality, managed/private media adapters, transactional reservation and claim RPC wiring, Azure service and real preview.
- **Hardware:** Central India T4 has native BF16 compatibility risk (CUDA compute capability 7.5); default Hunyuan BF16 runner rejects unsuitable GPU. Coordinator should review whether a consented A100 region is permissible or keep dormant Wan vendor choice. No cross-region transfer without approval.
