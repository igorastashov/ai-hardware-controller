# Revopoint Dual-axis Turntable

## Version
Unknown (captured from BLE probe sessions in this repository)

## Purpose in this project
- This file is the source of truth for device capabilities and protocol behavior.
- Runtime code and future agent tools must rely on this profile.
- Any new probe session must update this file and attach the JSON artifact path.

## Hardware profile
- Device type: BLE dual-axis turntable.
- Axes:
  - `rotate`: continuous rotation axis.
  - `tilt`: constrained axis with limits from config.
- Current configured limits (from `scripts/turntable_config.py`):
  - `tilt_min_deg = -30.0`
  - `tilt_max_deg = 30.0`
  - `command_gap_seconds = 0.10` between axis commands to avoid packet overlap.

## State confidence lifecycle
- Start application -> `LOW`
- Successful `turntable_home()` -> `MEDIUM`
- BLE reconnect after disconnect -> `LOW`
- `HIGH` is allowed only if hardware telemetry is confirmed by discovery.

## Motion semantics (agreed design)
- External API for the agent is absolute (`move_to`), not relative (`move_by`).
- Internal driver may use relative BLE commands after delta calculation.
- `rotate` shortest path rule:
  - Normalize current and target angles to `[0, 360)`.
  - Compute shortest signed delta:
    - `delta = ((target - current + 540) % 360) - 180`
  - Example: current `350`, target `10` -> delta `+20`.
- `turntable_state` returns normalized rotation (`0..359.999...`), not unbounded values.

## Busy policy
- If status is `BUSY`, movement commands are rejected with conflict.
- `STOP` is always allowed.
- No hidden command queues in the driver.

## Runtime policy (current implementation draft)
- Module: `scripts/turntable_runtime_singleflight.py`
- State machine:
  - `IDLE` -> `BUSY` -> `IDLE` for accepted motion commands
  - any protocol failure/timeout -> `ERROR`
- Concurrency model:
  - software-side single-flight mutex for motion commands
  - no device-side busy assumption
- Completion model:
  - `+OK;` means command accepted
  - completion currently estimated by timing model with safety buffer
  - until deterministic done-event is known, timing model is source of completion state
- STOP behavior:
  - `emergency_stop` allowed regardless of BUSY lock status
  - sends `+CT,STOP;` and `+CR,STOP;`
- Tool contract draft:
  - Module: `scripts/turntable_tool_adapter.py`
  - methods: `turntable_state`, `turntable_home`, `turntable_move_to`, `turntable_return_base`, `turntable_stop`
  - response format: structured JSON with `ok/result` or `ok/error` (`code`, `message`, `http_status`)
  - motion API uses absolute target for external caller and shortest-path delta for rotate internally
  - optional speed inputs are validated against provisional bounds before motion command dispatch
  - return-to-base supports two frames: `software_zero` and `power_on_zero` fallback

## Discovery artifacts
- Latest artifact path:
  - `docs/references/artifacts/revopoint-dual-axis-discovery.json`
  - `docs/references/artifacts/revopoint-dual-axis-protocol-probe.json`
  - `docs/references/artifacts/revopoint-dual-axis-protocol-probe-crlf.json`
  - `docs/references/artifacts/revopoint-dual-axis-protocol-probe-turnangle.json`
  - `docs/references/artifacts/revopoint-dual-axis-protocol-probe-qt-turnangle.json`
  - `docs/references/artifacts/revopoint-dual-axis-protocol-probe-qt-turnangle-crlf.json`
  - `docs/references/artifacts/revopoint-dual-axis-protocol-probe-qr-rotateangle.json`
  - `docs/references/artifacts/revopoint-dual-axis-protocol-probe-stop-ct.json`
  - `docs/references/artifacts/revopoint-dual-axis-protocol-probe-stop-cr.json`
  - `docs/references/artifacts/revopoint-dual-axis-motion-probe-01-tilt-before.json`
  - `docs/references/artifacts/revopoint-dual-axis-motion-probe-02-rotate-before.json`
  - `docs/references/artifacts/revopoint-dual-axis-motion-probe-03-rotate-move.json`
  - `docs/references/artifacts/revopoint-dual-axis-motion-probe-04-rotate-after.json`
  - `docs/references/artifacts/revopoint-dual-axis-motion-probe-05-tilt-move.json`
  - `docs/references/artifacts/revopoint-dual-axis-motion-probe-06-tilt-after.json`
  - `docs/references/artifacts/revopoint-dual-axis-motion-probe-07-stop-ct.json`
  - `docs/references/artifacts/revopoint-dual-axis-motion-probe-08-stop-cr.json`
  - `docs/references/artifacts/revopoint-motion-char-rotate10.json`
  - `docs/references/artifacts/revopoint-motion-char-tilt5.json`
  - `docs/references/artifacts/revopoint-busy-char-cross-axis.json`
  - `docs/references/artifacts/revopoint-busy-char-same-axis.json`
  - `docs/references/artifacts/revopoint-timing-rotate-30.json`
  - `docs/references/artifacts/revopoint-timing-tilt-10.json`
  - `docs/references/artifacts/revopoint-speed-decode-rotate.json`
  - `docs/references/artifacts/revopoint-speed-decode-tilt.json`
  - `docs/references/artifacts/revopoint-speed-decode-tilt-high-range.json`
  - `docs/references/artifacts/revopoint-speed-decode-tilt-threshold.json`
  - `docs/references/artifacts/revopoint-speed-decode-rotate-threshold.json`
  - `docs/references/artifacts/revopoint-speed-query-qr-tiltspeed.json`
  - `docs/references/artifacts/revopoint-speed-query-qt-turnspeed-rerun.json`
  - `docs/references/artifacts/revopoint-speed-query-qr-turnspeed-rerun.json`
  - `docs/references/artifacts/revopoint-speed-query-qt-tiltspeed-rerun.json`
  - `docs/references/artifacts/revopoint-tilt-speed-set-6_8.json`
  - `docs/references/artifacts/revopoint-tilt-speed-set-90.json`
  - `docs/references/artifacts/revopoint-tilt-speed-alt-cr-turnspeed-20-rerun.json`
  - `docs/references/artifacts/revopoint-tilt-speed-alt-ct-tiltspeed-20-rerun.json`
  - `docs/references/artifacts/revopoint-timing-rotate-120-calibration.json`
  - `docs/references/artifacts/revopoint-timing-tilt-20-calibration-rerun.json`
  - `docs/references/artifacts/revopoint-dual-axis-concurrency-probe.json`
- Generated by:
  - `python scripts/turntable_discover.py`
  - `python scripts/turntable_protocol_probe.py --target-address <BLE_MAC>`

## Latest confirmed probe (2026-03-06)
- Target found:
  - `address = D3:36:39:34:5D:29`
  - `name = REVO_DUAL_AXIS_TABLE`
- Confirmed service/characteristic candidates:
  - Service `0000ffe0-0000-1000-8000-00805f9b34fb`
    - Characteristic `0000ffe1-0000-1000-8000-00805f9b34fb`
    - Properties: `read`, `notify`, `write-without-response`
  - Service `02f00000-0000-0000-0000-00000000fe00`
    - `...ff01` has write capability
    - `...ff02` has read + notify capability
- Probe result:
  - GATT profile successfully read.
  - Runtime command/telemetry semantics partially confirmed.

## Protocol probe findings (2026-03-06)
- Characteristic used: `0000ffe1-0000-1000-8000-00805f9b34fb`
- Query command sent: `+QR,TILTANGLE;`
- Encoding: ASCII (UTF-8 decode also valid for response bytes)
- Response received via notify:
  - `+DATA=-30.0,30.0,0.3;`
- Interpretation candidate:
  - first value: tilt minimum (`-30.0`)
  - second value: tilt maximum (`30.0`)
  - third value: current tilt angle (observed `0.3`)
- Rotate query command matrix:
  - `+QR,TURNANGLE;` -> `+FAIL,ERR=001;`
  - `+QR,ROTATEANGLE;` -> `+FAIL,ERR=001;`
  - `+QT,TURNANGLE;` -> `+DATA=0,360,1.0;`
- Rotate interpretation candidate for `+QT,TURNANGLE;`:
  - first value: rotate minimum (`0`)
  - second value: rotate maximum (`360`)
  - third value: current rotate angle (observed `1.0`)
- Command ACK sample (no motion required):
  - `+CT,STOP;` -> `+OK;`
  - `+CR,STOP;` -> `+OK;`
- Terminator behavior:
  - command with only `;` works
  - command with `;\r\n` also works
  - exact parsing priority is unknown (device appears tolerant)

## Minimal motion probe findings (2026-03-06)
- Sequence:
  - baseline queries: `+QR,TILTANGLE;`, `+QT,TURNANGLE;`
  - motion commands: `+CT,TURNANGLE=2;`, `+CR,TILTVALUE=1;`
  - post queries: same as baseline
  - safety stop: `+CT,STOP;`, `+CR,STOP;`
- Observed protocol behavior:
  - both motion commands returned immediate `+OK;`
  - both stop commands returned `+OK;`
  - post-query payload values did not change in this run:
    - tilt: `+DATA=-30.0,30.0,0.3;`
    - rotate: `+DATA=0,360,1.0;`
- Current interpretation:
  - ACK format for motion command acceptance is confirmed (`+OK;`)
  - completion semantics are still unknown (no explicit "done" event observed)
  - either movement did not materially occur in this run, or queried `+DATA` fields are not direct live pose in the expected way

## Motion characterization findings (2026-03-06)
- Scenarios:
  - `+CT,TURNANGLE=10;` with 6s polling window
  - `+CR,TILTVALUE=5;` with 6s polling window
- Observations:
  - motion command ACK remained `+OK;` in both scenarios
  - all polling samples remained stable:
    - tilt query: `+DATA=-30.0,30.0,0.3;`
    - rotate query: `+DATA=0,360,1.0;`
  - no additional completion event appeared in notify stream
- Practical conclusion:
  - protocol clearly accepts movement commands
  - available query fields likely do not expose immediate live pose in the expected way
  - runtime state model should treat queries as "capability/config + coarse state", not precise encoder-equivalent telemetry

## Busy/queue characterization findings (2026-03-06)
- Scenario A (cross-axis rapid sequence, gap 100 ms):
  - `+CT,TURNANGLE=20;` followed by `+CR,TILTVALUE=5;`
  - responses: `+OK;`, `+OK;`
- Scenario B (same-axis rapid sequence, gap 100 ms):
  - `+CT,TURNANGLE=20;` followed by `+CT,TURNANGLE=-20;`
  - responses: `+OK;`, `+OK;`
- In both scenarios stop commands also returned `+OK;`.
- Practical conclusion:
  - protocol layer does not expose busy rejection in tested scenarios
  - controller accepts rapid command streams
  - deterministic safety must be enforced in software via mutex/state machine (do not rely on device-side reject)

## Timing probe findings (2026-03-06)
- Scenarios:
  - rotate axis: speeds `8,12,20` with `+CT,TURNANGLE=30;`
  - tilt axis: speeds `3,5,7` with `+CR,TILTVALUE=10;`
- Observations:
  - each run produced mixed notify responses, commonly `+FAIL,ERR=...;` followed by `+OK;`
  - rotate speed command produced `+FAIL,ERR=004;` before move `+OK;` in tested values
  - tilt speed command produced `+FAIL,ERR=007;` before move `+OK;` in tested values
  - movement acceptance (`+OK;`) remained stable for move commands
- Practical interpretation:
  - speed-setting commands in tested forms are likely unsupported or require different ranges/units
  - timing model should not yet depend on explicit speed command acceptance
  - keep conservative fixed completion model until speed command protocol is decoded

## Speed decode matrix findings (2026-03-06)
- Rotate speed command (`+CT,TURNSPEED=<v>;`) tested values:
  - accepted: `20`, `30`
  - rejected (`ERR=004`): `1`, `2`, `4`, `8`, `12`
- Tilt speed command (`+CR,TILTSPEED=<v>;`) tested values:
  - accepted: none in tested set
  - rejected (`ERR=007`): `1`, `2`, `3`, `5`, `7`, `10`, `15`
- Practical interpretation:
  - rotate speed has a restricted accepted sub-range in current protocol usage
  - tilt speed is also range-restricted (not universally rejected)
  - completion timing in runtime should remain speed-independent until tilt speed decoding is resolved

## Speed protocol refinements (2026-03-06)
- Query commands:
  - `+QT,TURNSPEED;` -> `+DATA=17.5,90.0,2.0;` (observed)
  - `+QR,TILTSPEED;` -> `+DATA=6.8,90.0,1.0;` (observed)
  - `+QR,TURNSPEED;` -> `+FAIL,ERR=001;`
  - `+QT,TILTSPEED;` -> `+FAIL,ERR=001;`
- Set command acceptance (observed):
  - rotate `+CT,TURNSPEED=v;` accepted for `v >= 18` in tested window
  - tilt `+CR,TILTSPEED=v;` accepted for `v >= 40` in tested window
  - values below those thresholds returned axis-specific errors (`ERR=004` rotate, `ERR=007` tilt)
- Provisional bounds for runtime validation:
  - rotate speed: `[18, 90]`
  - tilt speed: `[40, 90]`
- Important:
  - these are observed bounds on current hardware/firmware and must be treated as provisional until revalidated.

## Additional targeted speed findings (2026-03-06)
- `+CR,TILTSPEED=6.8;` -> `+FAIL,ERR=007;`
- `+CR,TILTSPEED=90;` -> `+OK;`
- Alternate set commands are invalid:
  - `+CR,TURNSPEED=20;` -> `+FAIL,ERR=001;`
  - `+CT,TILTSPEED=20;` -> `+FAIL,ERR=001;`
- Confirms that speed set commands are axis-specific and use strict command families.

## Calibration run status (2026-03-06)
- Completed command/ACK calibration runs:
  - rotate: speeds `18,24,30`, move `120`
  - tilt: speeds `40,60,90`, move `20`
- All runs returned `+OK` for speed+move commands.
- Next required input:
  - manual human timing observations per run (`observed_start_delay_s`, `observed_end_time_s`) to derive `deg/s` mapping.

## Dual-axis concurrency probe (2026-03-06)
- Scenario:
  - Commands sent with `50 ms` gap: rotate speed, tilt speed, rotate move, tilt move.
- Result:
  - all four commands were accepted (`+OK`)
  - command-level ACK latency was low (roughly tens of milliseconds)
  - no protocol-side BUSY/FAIL in this near-simultaneous dispatch test
- Interpretation:
  - controller accepts overlapping multi-axis command streams at protocol level
  - software mutex is still required for deterministic agent behavior
  - for balancing-like tasks, protocol ACK speed alone is not enough; physical startup/motion times remain in seconds.

## Manual calibration summary (human-observed, 2026-03-06)
- Measurement uncertainty: about `+-0.3 .. 0.4 s`.
- Additional note: tilt moves were performed in one direction; after runs the table was manually returned to initial pose.

- Rotate (`move=120`):
  - speed 18: start `~2.5s`, finish `~8.78s`, motion-only `~6.28s`, estimated `~19.1 deg/s`
  - speed 24: start `~1.5s`, finish `~8.8s`, motion-only `~7.3s`, estimated `~16.4 deg/s`
  - speed 30: start `~1.5s`, finish `~12.0s`, motion-only `~10.5s`, estimated `~11.4 deg/s`

- Tilt (`move=20`, one direction):
  - speed 40: start `~1.5s`, finish `~3.5s`, motion-only `~2.0s`, estimated `~10.0 deg/s`
  - speed 60: start `~1.0s`, finish `~4.5s`, motion-only `~3.5s`, estimated `~5.7 deg/s`
  - speed 90: start `~1.7s`, finish `~6.3s`, motion-only `~4.6s`, estimated `~4.35 deg/s`

- Practical interpretation:
  - larger speed value => slower motion (inverse relation) on both axes in observed runs.
  - conservative runtime model should use slow-edge values + startup delay + safety buffer.
  - direct speed->deg/s function is still provisional; more repetitions recommended for confidence.

## Runtime timing calibration applied (provisional)
- `default_rotate_deg_per_s = 10.5`
- `default_tilt_deg_per_s = 3.7`
- `rotate_start_delay_seconds = 2.5`
- `tilt_start_delay_seconds = 1.8`
- `completion_safety_buffer_seconds = 1.0`

## Current status by confidence policy
- Hardware telemetry is now confirmed for both axes via query + notify on `FFE1`.
- `HIGH` can be granted when both axis queries succeed in active session.
- After reconnect, confidence should still drop to `LOW` and be upgraded only after successful re-probe of both queries.

## Open questions (must be validated by probe)
- Which write/read pair is primary for motion protocol in this hardware revision (`FFE1` vs `...FF01/FF02`)?
- Is `+DATA=min,max,current` format stable for both axes across firmware versions?
- Is ACK behavior (`+OK;` / `+FAIL,ERR=...;`) stable for real motion commands, not only query/stop?
- Does `+DATA` third field represent live physical angle, target value, or last-known software state?
- What command/response pattern indicates motion completion deterministically?
- Can movement completion be inferred only by timing model (angle/speed) plus optional safety margin?
- What exact runtime policy is safer for agent tools: strict single-flight mutex or explicit queued executor?
- How do accepted speed values map to physical deg/s on each axis?
