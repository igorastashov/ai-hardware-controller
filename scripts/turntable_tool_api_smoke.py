"""Smoke checks for FastAPI tool surface without real BLE hardware."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from fastapi.testclient import TestClient

from turntable_config import SPEED_BOUNDS
from turntable_tool_adapter import TurntableToolAdapter
from turntable_tool_api import create_app


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
            ble_connected=False,
            last_error_code=None,
            last_error_message=None,
        )
        self.calls: list[dict[str, Any]] = []

    async def connect(self) -> None:
        self.calls.append({"method": "connect"})
        self.state.ble_connected = True

    async def disconnect(self) -> None:
        self.calls.append({"method": "disconnect"})
        self.state.ble_connected = False

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
        return _Frame(raw="+OK;")

    async def move_tilt_to(self, target_deg: float) -> _Frame:
        self.calls.append({"method": "move_tilt_to", "target_deg": target_deg})
        return _Frame(raw="+OK;")

    async def return_rotate_to_power_on_zero(self) -> _Frame:
        self.calls.append({"method": "return_rotate_to_power_on_zero"})
        return _Frame(raw="+OK;")

    async def emergency_stop(self) -> list[_Frame]:
        self.calls.append({"method": "emergency_stop"})
        return [_Frame(raw="+OK;"), _Frame(raw="+OK;")]


def _run() -> dict[str, Any]:
    runtime = _FakeRuntime()
    adapter = TurntableToolAdapter(address="FAKE", runtime=runtime)
    app = create_app(address="FAKE", adapter=adapter)
    client = TestClient(app)

    home = client.post("/home")
    move = client.post(
        "/move-to",
        json={"rotation_deg": 30.0, "tilt_deg": 10.0, "rotate_speed_value": 18.0, "tilt_speed_value": 40.0},
    )
    invalid = client.post("/move-to", json={"rotation_deg": 0.0, "tilt_deg": 100.0})
    state = client.post("/state")
    ret = client.post("/return-base")
    stop = client.post("/stop")
    commissioning = client.post(
        "/commissioning/first-run",
        json={"max_capability": False, "include_busy_check": False, "include_stop_check": False},
    )
    commissioning_full = client.post("/commissioning/first-run/full")

    checks = {
        "home_200": home.status_code == 200 and home.json().get("ok") is True,
        "move_200": move.status_code == 200 and move.json().get("ok") is True,
        "invalid_422": invalid.status_code == 422 and invalid.json().get("ok") is False,
        "state_200": state.status_code == 200 and state.json().get("ok") is True,
        "return_base_200": ret.status_code == 200 and ret.json().get("ok") is True,
        "stop_200": stop.status_code == 200 and stop.json().get("ok") is True,
        "commissioning_200": commissioning.status_code == 200 and commissioning.json().get("ok") is True,
        "commissioning_full_response": commissioning_full.status_code in (200, 503)
        and "result" in commissioning_full.json(),
    }

    return {
        "checks": checks,
        "all_passed": all(checks.values()),
        "runtime_calls": runtime.calls,
    }


if __name__ == "__main__":
    result = _run()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    raise SystemExit(0 if result["all_passed"] else 1)
