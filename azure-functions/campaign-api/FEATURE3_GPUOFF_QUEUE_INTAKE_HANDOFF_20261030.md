# Feature #3 — GPU-OFF queue intake second-gate handoff (2026-10-30)

Task IDs: F3-04 (source-only inspection), F3-13 (negative race regression).
Base: main a75f9df62451dbc701633782a9baf1b16e32c8c8.
Scope: read-only Feature3GPUOffQueueIntake; no queue delete/ACK, SQL writes, provider invocation, GPU start or hosted deployment.

A trusted provider status may change from OFF to ON while the current source-rights plan is being read. A single initial status check can return a stale GPU-OFF receipt. The inspector now requires an authoritative OFF snapshot before decoding/SQL and again after validating the plan, immediately before returning a receipt. Second-check provider outages or unknown state fail closed. This narrows a time-of-check/time-of-use window but cannot guarantee atomic provider state across independently operated services.

Tests added: deterministic state transition, second-read failure/unknown state, and two-read success; no real media or paid provider. CI results must be inspected at exact PR head. No fixture may be labeled genuine generated output.

Still BLOCKED: F3-04 approved one-shot Azure runtime, queue ACK/poison, current licensed source grants, durable provider/lease controls (owner: Feature3/coordinator); F3-13 signed hosted negative tests and actual queue/provider failure injection (owner: Feature3/coordinator and Azure reliability #249). Acceptance requires coordinator review, main integration and fresh four-job CI plus independently approved hosted gates. This PR alone is not integrated DONE and does not change coordination/task_progress.json.
