"""First-run physical commissioning checks for turntable tooling."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from typing import Any

from turntable_tool_adapter import TurntableToolAdapter


@dataclass
class CommissioningOptions:
    max_capability: bool = True
    include_busy_check: bool = True
    include_stop_check: bool = True


def _check(name: str, ok: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "ok": ok, "details": details}


def _is_ok(result: dict[str, Any]) -> bool:
    return result.get("ok", False) is True


def _error_code(result: dict[str, Any]) -> str | None:
    return result.get("error", {}).get("code")


async def run_first_start_commissioning(
    adapter: TurntableToolAdapter,
    options: CommissioningOptions | None = None,
) -> dict[str, Any]:
    opts = options if options is not None else CommissioningOptions()
    checks: list[dict[str, Any]] = []

    state = await adapter.turntable_state()
    checks.append(
        _check(
            "state_initial",
            _is_ok(state),
            {"status": state.get("result", {}).get("status"), "response": state},
        )
    )

    home = await adapter.turntable_home()
    checks.append(_check("home", _is_ok(home), {"response": home}))

    moves: list[dict[str, Any]] = [
        {
            "name": "move_nominal_small",
            "rotation_deg": 15.0,
            "tilt_deg": 5.0,
            "rotate_speed_value": 18.0,
            "tilt_speed_value": 40.0,
        },
        {
            "name": "move_nominal_cross_quadrant",
            "rotation_deg": 300.0,
            "tilt_deg": -10.0,
            "rotate_speed_value": 60.0 if opts.max_capability else 30.0,
            "tilt_speed_value": 60.0 if opts.max_capability else 40.0,
        },
    ]
    if opts.max_capability:
        moves.extend(
            [
                {
                    "name": "move_max_upper_tilt",
                    "rotation_deg": 359.0,
                    "tilt_deg": 30.0,
                    "rotate_speed_value": 90.0,
                    "tilt_speed_value": 90.0,
                },
                {
                    "name": "move_max_lower_tilt",
                    "rotation_deg": 1.0,
                    "tilt_deg": -30.0,
                    "rotate_speed_value": 90.0,
                    "tilt_speed_value": 90.0,
                },
            ]
        )

    for step in moves:
        result = await adapter.turntable_move_to(
            rotation_deg=step["rotation_deg"],
            tilt_deg=step["tilt_deg"],
            rotate_speed_value=step["rotate_speed_value"],
            tilt_speed_value=step["tilt_speed_value"],
        )
        checks.append(
            _check(
                step["name"],
                _is_ok(result),
                {
                    "target": {
                        "rotation_deg": step["rotation_deg"],
                        "tilt_deg": step["tilt_deg"],
                        "rotate_speed_value": step["rotate_speed_value"],
                        "tilt_speed_value": step["tilt_speed_value"],
                    },
                    "response": result,
                },
            )
        )

    invalid_tilt = await adapter.turntable_move_to(rotation_deg=0.0, tilt_deg=31.0)
    checks.append(
        _check(
            "validation_invalid_tilt",
            (not _is_ok(invalid_tilt)) and _error_code(invalid_tilt) == "TILT_OUT_OF_RANGE",
            {"response": invalid_tilt},
        )
    )

    invalid_speed = await adapter.turntable_move_to(
        rotation_deg=0.0,
        tilt_deg=0.0,
        rotate_speed_value=10.0,
    )
    checks.append(
        _check(
            "validation_invalid_rotate_speed",
            (not _is_ok(invalid_speed)) and _error_code(invalid_speed) == "VALIDATION_ERROR",
            {"response": invalid_speed},
        )
    )

    if opts.include_busy_check:
        first = asyncio.create_task(
            adapter.turntable_move_to(
                rotation_deg=180.0,
                tilt_deg=0.0,
                rotate_speed_value=90.0 if opts.max_capability else 30.0,
                tilt_speed_value=90.0 if opts.max_capability else 40.0,
            )
        )
        await asyncio.sleep(0.05)
        second = asyncio.create_task(adapter.turntable_move_to(rotation_deg=210.0, tilt_deg=0.0))
        first_result, second_result = await asyncio.gather(first, second)
        busy_ok = (
            (_is_ok(first_result) and (not _is_ok(second_result)) and _error_code(second_result) == "DEVICE_BUSY")
            or (_is_ok(second_result) and (not _is_ok(first_result)) and _error_code(first_result) == "DEVICE_BUSY")
        )
        checks.append(
            _check(
                "busy_parallel_move_rejected",
                busy_ok,
                {"first": first_result, "second": second_result},
            )
        )

    if opts.include_stop_check:
        move_task = asyncio.create_task(
            adapter.turntable_move_to(
                rotation_deg=270.0,
                tilt_deg=0.0,
                rotate_speed_value=90.0 if opts.max_capability else 30.0,
                tilt_speed_value=90.0 if opts.max_capability else 40.0,
            )
        )
        await asyncio.sleep(0.1)
        stop_result = await adapter.turntable_stop()
        move_result = await move_task
        checks.append(
            _check(
                "stop_during_motion",
                _is_ok(stop_result),
                {"stop_response": stop_result, "motion_response": move_result},
            )
        )

    return_base = await adapter.turntable_return_base()
    checks.append(_check("return_base", _is_ok(return_base), {"response": return_base}))

    final_state = await adapter.turntable_state()
    checks.append(
        _check(
            "state_final_idle",
            _is_ok(final_state) and final_state.get("result", {}).get("status") == "IDLE",
            {"response": final_state},
        )
    )

    passed = sum(1 for item in checks if item["ok"])
    report = {
        "ready": passed == len(checks),
        "summary": {"passed": passed, "failed": len(checks) - passed, "total": len(checks)},
        "checks": checks,
        "profile": {
            "max_capability": opts.max_capability,
            "include_busy_check": opts.include_busy_check,
            "include_stop_check": opts.include_stop_check,
        },
    }
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run first-start turntable commissioning scenario.")
    parser.add_argument("--address", required=True, help="BLE address of turntable device.")
    parser.add_argument("--safe-profile", action="store_true", help="Use conservative profile.")
    parser.add_argument("--skip-busy-check", action="store_true")
    parser.add_argument("--skip-stop-check", action="store_true")
    return parser


async def _run_cli(args: argparse.Namespace) -> dict[str, Any]:
    adapter = TurntableToolAdapter(address=args.address)
    connect = await adapter.connect()
    if not _is_ok(connect):
        return {"ready": False, "summary": {"passed": 0, "failed": 1, "total": 1}, "checks": [_check("connect", False, {"response": connect})]}
    try:
        return await run_first_start_commissioning(
            adapter,
            CommissioningOptions(
                max_capability=not args.safe_profile,
                include_busy_check=not args.skip_busy_check,
                include_stop_check=not args.skip_stop_check,
            ),
        )
    finally:
        await adapter.disconnect()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    report = asyncio.run(_run_cli(args))
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report.get("ready", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
