# OpenClaw Turntable Future Agent Work

## Mission
Finish operational integration of turntable handles into OpenClaw runtime with production-safe behavior.

## Priority backlog

1. **Integration adapter**
- Wire `turntable_tool_cli`/adapter into OpenClaw tool registry.
- Ensure strict mapping of JSON error codes to agent decision policies.

2. **Session policy**
- Auto-run `state` on session start.
- Optional policy for auto-`home` with explicit operator confirmation.

3. **Retry and recovery**
- Add standardized reconnect workflow around `BLE_CONNECT_FAILED`.
- Add escalation path for repeated `STOP_FAILED` or persistent `MOVE_FAILED`.

4. **Timing model refinement**
- Continue collecting operator timing summaries.
- Evolve from conservative fixed model to bounded model by speed bucket.

5. **Observability**
- Persist per-command telemetry in JSONL format for audits.
- Add simple post-run summarizer to detect anomalies by error code distribution.

6. **Operational safeguards**
- Add rate-limiter for motion command frequency.
- Add configurable max step size per call for safer autonomous behavior.

## Definition of done (integration phase)
- OpenClaw can call all 5 handles reliably in real sessions.
- Agent follows mandatory safety policy from instruction doc.
- Hardware probe artifacts and contract tests are green in CI/local harness.
