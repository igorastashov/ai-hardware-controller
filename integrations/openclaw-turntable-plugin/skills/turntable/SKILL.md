# Turntable Safety Skill

## Purpose
Safe orchestration policy for turntable tools exposed by the external OpenClaw plugin.

## Mandatory loop
1. `turntable_state`
2. If session starts and zero frame not set: `turntable_home` once
3. `turntable_move_to(rotation_deg, tilt_deg, rotate_speed_value?, tilt_speed_value?)`
4. `turntable_state`
5. On ambiguity/error: `turntable_stop`, then `turntable_state`, then decide whether to continue

## Safety requirements
- Never run motion tools in parallel.
- Respect `DEVICE_NOT_IDLE` / `DEVICE_BUSY` and re-check state before retries.
- Do not bypass plugin validation by sending out-of-range tilt/speed values.
- Do not flood side-effect tools faster than command gap policy.

## Error policy
| Error code | Action |
|---|---|
| `SIDE_EFFECT_TOOL_DISABLED` | Stop and request operator to enable allowlist for side-effect tools. |
| `DEVICE_NOT_IDLE` | Do not issue motion; call `turntable_state` and wait for `IDLE`. |
| `MOVE_FAILED` | Call `turntable_stop`, then `turntable_state`; escalate if repeated. |
| `STOP_FAILED` | Immediate human escalation; no autonomous retries loop. |
| `UPSTREAM_TIMEOUT` / `UPSTREAM_UNAVAILABLE` | Treat as transport incident; do not assume command succeeded. |

## Explicit stop-condition
Escalate to human operator and stop autonomous retries when one of:
- 2 consecutive `MOVE_FAILED` for the same target.
- Any `STOP_FAILED`.
- 3 consecutive transport failures (`UPSTREAM_TIMEOUT`/`UPSTREAM_UNAVAILABLE`).
