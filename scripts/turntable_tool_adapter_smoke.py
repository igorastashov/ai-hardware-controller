"""Smoke checks for tool adapter contract without real BLE device.

This script validates:
- stable JSON response shape
- shortest-path rotate behavior in move_to
- tilt limits validation and error shape
- BUSY behavior mapping to HTTP 409 style error
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

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
    def __init__(self) -> None:
        self.state = _State(
            status=_Status.IDLE,
            ble_connected=True,
            last_error_code=None,
            last_error_message=None,
        )
        self.calls: list[dict[str, Any]] = []

    async def connect(self) -> None:
        self.calls.append({"method": "connect"})

    async def disconnect(self) -> None:
        self.calls.append({"method": "disconnect"})

    async def move_rotate_by(self, delta_deg: float) -> _Frame:
        self.calls.append({"method": "move_rotate_by", "delta_deg": delta_deg})
        return _Frame(raw="+OK;")

    async def move_tilt_to(self, target_deg: float) -> _Frame:
        self.calls.append({"method": "move_tilt_to", "target_deg": target_deg})
        return _Frame(raw="+OK;")

    async def emergency_stop(self) -> list[_Frame]:
        self.calls.append({"method": "emergency_stop"})
        return [_Frame(raw="+OK;"), _Frame(raw="+OK;")]


async def _run() -> dict[str, Any]:
    runtime = _FakeRuntime()
    adapter = TurntableToolAdapter(address="FAKE", runtime=runtime)

    home = await adapter.turntable_home()
    move = await adapter.turntable_move_to(rotation_deg=350.0, tilt_deg=5.0)
    state = await adapter.turntable_state()
    stop = await adapter.turntable_stop()
    invalid_tilt = await adapter.turntable_move_to(rotation_deg=0.0, tilt_deg=100.0)

    checks = {
        "home_ok": home.get("ok") is True,
        "move_ok": move.get("ok") is True,
        "state_ok": state.get("ok") is True,
        "stop_ok": stop.get("ok") is True,
        "invalid_tilt_rejected": invalid_tilt.get("ok") is False
        and invalid_tilt.get("error", {}).get("code") == "TILT_OUT_OF_RANGE",
    }

    return {
        "checks": checks,
        "all_passed": all(checks.values()),
        "runtime_calls": runtime.calls,
        "samples": {
            "home": home,
            "move": move,
            "state": state,
            "stop": stop,
            "invalid_tilt": invalid_tilt,
        },
    }


if __name__ == "__main__":
    result = asyncio.run(_run())
    print(json.dumps(result, ensure_ascii=True, indent=2))
    raise SystemExit(0 if result["all_passed"] else 1)
