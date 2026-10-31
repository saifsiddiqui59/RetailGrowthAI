# Feature #2: operator-only Kokoro CPU measurement (2026-10-29)

**Status: source implementation and synthetic negative tests; real Kokoro inference is NOT yet measured.** This does not certify an Azure Functions runtime, speech quality, cost, commercial use, or an approved private audio object.

## Preconditions

- A trusted operator has downloaded immutable pinned `kokoro-v1.0.int8.onnx` (114119327 bytes, SHA256 `ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c`) and `voices-v1.0.bin` (28214398 bytes, SHA256 `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d`) to a local private cache; provisioning script: `ai-agents/test-fixtures/retailer-voice/provision-pinned-kokoro-models.sh`.
- Actual `kokoro-onnx==0.6.1`, compatible ONNX Runtime CPU and NumPy are installed in the controlled Python virtual environment. The requested operator model path is not a browser input. GPU/CUDA, remote inference and Azure Speech are not permitted for this tool.
- Enable `RETAIL_FEATURE2_KOKORO_CPU_ENABLED=true` only in the operator's trusted local environment. This does not authorize production deployment, new cloud resources, billed services, or downloading the model in a web request.

## Running a genuine sample

From the repository root, on a controlled CPU-only host:

```bash
RETAIL_FEATURE2_KOKORO_CPU_ENABLED=true \
  uv run --project ai-agents python \
  ai-agents/test-fixtures/retailer-voice/benchmark-pinned-kokoro-cpu.py \
  --cache-dir /absolute/operator-private/kokoro --voice af_heart --repeats 2
```

The absolute directory placeholder above must be replaced by an existing local cache. The CLI deliberately has no user-prompt, customer-audio, browser URL, raw transcript or arbitrary-voice option. Its first run includes trusted weight SHA validation and a cold session if the process has not loaded the model; later observations reuse the worker-local session. It prints JSON only after every actual pinned model sample has passed the audio/source digest and provenance checks. A missing model, disabled CPU flag or wrong provider exits nonzero without a positive stdout result. There is no silent Azure fallback.

## Interpreting output

The schema `retailgrowth.feature2-cpu-benchmark.v1` reports wall seconds, process CPU seconds, sample duration and real-time factor for each of at most three bounded runs. `process_high_water_rss_kib` is a *whole-process high-water mark*, **not** an isolated model's peak RSS or a container allocation. On platforms lacking the Unix `resource` API, this field is null, not estimated.

Only `real_model_inference_verified: true` together with `test_only: false` from the genuine runtime is eligible to be recorded as a real benchmark. Source-injected test runs are always marked `test_only: true` and `real_model_inference_verified: false`. No audio waveform, raw speech or private identifiers appear in the receipt.

`billable_provider_calls: 0` means **no metered third-party TTS API calls**, not zero CPU-host, VM, storage, electricity or labor costs. `cloud_vm_or_electricity_cost_estimate_usd: null` must remain unknown until an independently verified deployment rate and hardware allocation are recorded. Word pronunciation, transcript correctness and commercial publishing authorization remain separate Feature #7/editor/rights gates.

## Remaining approval tasks

1. Run on the actual intended CPU instance with verified original model and voice binary, at least two real observations and recorded CPU architecture/RAM/performance region **outside customer data**.
2. Have the coordinator bind authenticated tenant jobs, budgets, idempotency, private storage and signed assets. Do not store this test audio as a customer asset.
3. Confirm authorized license use and real speech through independent listening and original-WAV ASR. A fast benchmark does not prove word accuracy.
4. Resolve coordinator [issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) (protected Functions ZIP package) before any deployment or Feature #2 PR merge.

This is the owned Feature #2 preparation for fixed ledger **task #15** (P0), not completion of a genuine benchmark or hosted acceptance.
