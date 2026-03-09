# OpenClaw Turntable Test Plan

## Scope
- Validation of tool-handle infrastructure for agent integration.
- Focus on contract correctness, safety policies, and BLE operational resilience.

## Test levels

### 1) Contract tests (no hardware)
- Script: `scripts/turntable_tool_adapter_contract_test.py`
- Coverage:
  - `state/home/move_to/return_base/stop` response schema
  - speed validation (`422`)
  - busy rejection (`409`)
  - shortest-path rotate behavior
  - return-to-base in `software_zero` frame

### 2) Smoke test (no hardware)
- Script: `scripts/turntable_tool_adapter_smoke.py`
- Coverage:
  - minimal end-to-end adapter flow
  - quick regression signal for recent edits

### 2.1) API smoke test (no hardware)
- Script: `scripts/turntable_tool_api_smoke.py`
- Coverage:
  - HTTP status codes for `state/home/move-to/return-base/stop`
  - JSON contract preservation from adapter to HTTP layer
  - automatic connect path on first request

### 3) Probe tests (hardware required)
- `scripts/turntable_protocol_probe.py`
  - command/query ACK parsing
- `scripts/turntable_speed_decode_probe.py`
  - accepted/rejected speed ranges per axis
- `scripts/turntable_timing_probe.py`
  - timing traces for move completion model
- `scripts/turntable_dual_axis_probe.py`
  - near-simultaneous dispatch behavior

### 4) Commissioning test (hardware required)
- Script: `scripts/turntable_commissioning.py`
- Coverage:
  - first-run scenario end-to-end for `state/home/move_to/validation/busy/stop/return_base`
  - readiness report (`ready`, checks passed/failed)
  - max-capability profile for initial acceptance before autonomous bot usage

## Acceptance criteria (MVP)
- All contract and smoke scripts exit `0`.
- `verify.sh` exits `0`.
- `turntable_commissioning.py --address <BLE_ADDR>` exits `0` on target hardware.
- Tool handles documented and stable:
  - `turntable_state`
  - `turntable_home`
  - `turntable_move_to`
  - `turntable_return_base`
  - `turntable_stop`
  - `turntable_commissioning_first_run`
- Safety policy documented and actionable for agent runtime.

## Manual checks (operator)
- Confirm physical movement aligns with issued `move_to`.
- Confirm `return_base` behavior in both frames:
  - with prior `home` -> `software_zero`
  - without `home` -> `power_on_zero` fallback
- Confirm stop behavior reliably interrupts active motion.
- Confirm first-run sequence validates all handles (`state/home/move_to/return_base/stop`) via HTTP API and CLI fallback.

## Future extensions
- Add reconnect stress test (multiple connect/disconnect cycles).
- Add BUSY race test with real BLE runtime (not fake runtime).
- Add automatic artifact summarizer for timing/decode probes.
