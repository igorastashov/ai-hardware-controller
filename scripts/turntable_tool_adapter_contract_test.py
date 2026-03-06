"""Contract tests for TurntableToolAdapter.

No external test framework is used to keep repository bootstrap simple.
Exit code 0 means all checks passed.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from turntable_config import SPEED_BOUNDS
from turntable_tool_adapter import TurntableToolAdapter


class _Status(str, Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"


@dataclass
class _State:
    status: _Status
    ble_connected: bool
    last_error_code: str | None
    last_error_message: str | None


@dataclass
class _Frame:
    raw: str


class _FakeRuntime:
    def __init__(self, delay_s: float = 0.0) -> None:
        self.state = _State(
            status=_Status.IDLE,
            ble_connected=True,
            last_error_code=None,
            last_error_message=None,
        )
        self.delay_s = delay_s
        self.calls: list[dict[str, Any]] = []

    async def connect(self) -> None:
        self.calls.append({"method": "connect"})

    async def disconnect(self) -> None:
        self.calls.append({"method": "disconnect"})

    async def set_rotate_speed(self, speed_value: float) -> _Frame:
        if (
            speed_value < SPEED_BOUNDS.rotate_min_observed_ok
            or speed_value > SPEED_BOUNDS.rotate_max_observed_ok
        ):
            raise ValueError("Rotate speed outside bounds")
        self.calls.append({"method": "set_rotate_speed", "value": speed_value})
        return _Frame(raw="+OK;")

    async def set_tilt_speed(self, speed_value: float) -> _Frame:
        if (
            speed_value < SPEED_BOUNDS.tilt_min_observed_ok
            or speed_value > SPEED_BOUNDS.tilt_max_observed_ok
        ):
            raise ValueError("Tilt speed outside bounds")
        self.calls.append({"method": "set_tilt_speed", "value": speed_value})
        return _Frame(raw="+OK;")

    async def move_rotate_by(self, delta_deg: float) -> _Frame:
        self.calls.append({"method": "move_rotate_by", "delta_deg": delta_deg})
        if self.delay_s > 0:
            await asyncio.sleep(self.delay_s)
        return _Frame(raw="+OK;")

    async def move_tilt_to(self, target_deg: float) -> _Frame:
        self.calls.append({"method": "move_tilt_to", "target_deg": target_deg})
        if self.delay_s > 0:
            await asyncio.sleep(self.delay_s)
        return _Frame(raw="+OK;")

    async def return_rotate_to_power_on_zero(self) -> _Frame:
        self.calls.append({"method": "return_rotate_to_power_on_zero"})
        return _Frame(raw="+OK;")

    async def emergency_stop(self) -> list[_Frame]:
        self.calls.append({"method": "emergency_stop"})
        return [_Frame(raw="+OK;"), _Frame(raw="+OK;")]


async def _run() -> dict[str, Any]:
    checks: dict[str, bool] = {}

    # Scenario 1: nominal flow with speeds + return-base in software frame.
    runtime1 = _FakeRuntime()
    adapter1 = TurntableToolAdapter(address="FAKE", runtime=runtime1)
    home = await adapter1.turntable_home()
    move = await adapter1.turntable_move_to(
        rotation_deg=350.0,
        tilt_deg=5.0,
        rotate_speed_value=18.0,
        tilt_speed_value=40.0,
    )
    ret = await adapter1.turntable_return_base()
    state = await adapter1.turntable_state()
    stop = await adapter1.turntable_stop()

    checks["home_ok"] = home.get("ok") is True
    checks["move_ok"] = move.get("ok") is True
    checks["return_base_ok"] = ret.get("ok") is True
    checks["state_zero_after_return"] = (
        state.get("ok") is True
        and state["result"]["rotation_deg"] == 0.0
        and state["result"]["tilt_deg"] == 0.0
    )
    checks["stop_ok"] = stop.get("ok") is True

    # Scenario 2: validation error for invalid speed.
    invalid_speed = await adapter1.turntable_move_to(
        rotation_deg=0.0,
        tilt_deg=0.0,
        rotate_speed_value=10.0,  # below observed rotate lower bound
    )
    checks["invalid_speed_rejected"] = (
        invalid_speed.get("ok") is False
        and invalid_speed.get("error", {}).get("http_status") == 422
    )

    # Scenario 3: busy behavior with overlapping calls.
    runtime2 = _FakeRuntime(delay_s=0.25)
    adapter2 = TurntableToolAdapter(address="FAKE", runtime=runtime2)
    await adapter2.turntable_home()

    t1 = asyncio.create_task(adapter2.turntable_move_to(rotation_deg=30.0, tilt_deg=0.0))
    await asyncio.sleep(0.05)
    t2 = asyncio.create_task(adapter2.turntable_move_to(rotation_deg=60.0, tilt_deg=0.0))
    r1, r2 = await asyncio.gather(t1, t2)

    checks["busy_second_call_rejected"] = (
        (r1.get("ok") is True and r2.get("ok") is False and r2["error"]["code"] == "DEVICE_BUSY")
        or (r2.get("ok") is True and r1.get("ok") is False and r1["error"]["code"] == "DEVICE_BUSY")
    )

    return {
        "checks": checks,
        "all_passed": all(checks.values()),
        "scenario1_calls": runtime1.calls,
        "scenario2_busy_calls": runtime2.calls,
    }


if __name__ == "__main__":
    result = asyncio.run(_run())
    print(json.dumps(result, ensure_ascii=True, indent=2))
    raise SystemExit(0 if result["all_passed"] else 1)
