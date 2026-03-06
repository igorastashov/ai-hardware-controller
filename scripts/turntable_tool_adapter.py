"""Tool-level adapter for future agent integration.

This module wraps runtime primitives into stable, JSON-like tool responses:
- turntable_state
- turntable_home
- turntable_move_to
- turntable_stop
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from turntable_config import AXIS_LIMITS
from turntable_runtime_singleflight import BusyError, TurntableRuntimeSingleFlight


def _normalize_deg_360(value: float) -> float:
    normalized = value % 360.0
    return normalized if normalized >= 0 else normalized + 360.0


def _shortest_delta_deg(current: float, target: float) -> float:
    current_n = _normalize_deg_360(current)
    target_n = _normalize_deg_360(target)
    return ((target_n - current_n + 540.0) % 360.0) - 180.0


@dataclass
class VirtualPose:
    rotation_deg: float
    tilt_deg: float
    zero_calibrated: bool
    reference_frame: str


class TurntableToolAdapter:
    """High-level adapter that exposes stable tool semantics."""

    def __init__(
        self,
        address: str,
        runtime: TurntableRuntimeSingleFlight | None = None,
    ) -> None:
        self._runtime = runtime if runtime is not None else TurntableRuntimeSingleFlight(address)
        self._pose = VirtualPose(
            rotation_deg=0.0,
            tilt_deg=0.0,
            zero_calibrated=False,
            reference_frame="power_on_zero",
        )
        self._action_lock = asyncio.Lock()

    async def connect(self) -> dict[str, Any]:
        try:
            await self._runtime.connect()
            return self._ok({"connected": True})
        except Exception as exc:  # noqa: BLE001
            return self._error("BLE_CONNECT_FAILED", str(exc), 503)

    async def disconnect(self) -> dict[str, Any]:
        try:
            await self._runtime.disconnect()
            return self._ok({"connected": False})
        except Exception as exc:  # noqa: BLE001
            return self._error("BLE_DISCONNECT_FAILED", str(exc), 500)

    async def turntable_state(self) -> dict[str, Any]:
        state = self._runtime.state
        return self._ok(
            {
                "rotation_deg": _normalize_deg_360(self._pose.rotation_deg),
                "tilt_deg": self._pose.tilt_deg,
                "status": state.status.value,
                "ble_connected": state.ble_connected,
                "zero_calibrated": self._pose.zero_calibrated,
                "reference_frame": self._pose.reference_frame,
                "last_error_code": state.last_error_code,
                "last_error_message": state.last_error_message,
            }
        )

    async def turntable_home(self) -> dict[str, Any]:
        if self._action_lock.locked():
            return self._error("DEVICE_BUSY", "Device is busy.", 409)

        async with self._action_lock:
            self._pose = VirtualPose(
                rotation_deg=0.0,
                tilt_deg=0.0,
                zero_calibrated=True,
                reference_frame="software_zero",
            )
            return self._ok(
                {
                    "rotation_deg": 0.0,
                    "tilt_deg": 0.0,
                    "zero_calibrated": True,
                    "reference_frame": self._pose.reference_frame,
                }
            )

    async def turntable_move_to(
        self,
        rotation_deg: float,
        tilt_deg: float,
        rotate_speed_value: float | None = None,
        tilt_speed_value: float | None = None,
    ) -> dict[str, Any]:
        if self._action_lock.locked():
            return self._error("DEVICE_BUSY", "Device is busy.", 409)

        if tilt_deg < AXIS_LIMITS.tilt_min_deg or tilt_deg > AXIS_LIMITS.tilt_max_deg:
            return self._error(
                "TILT_OUT_OF_RANGE",
                f"Tilt must be within [{AXIS_LIMITS.tilt_min_deg}, {AXIS_LIMITS.tilt_max_deg}].",
                422,
            )

        async with self._action_lock:
            executed: list[dict[str, Any]] = []
            try:
                if rotate_speed_value is not None:
                    frame = await self._runtime.set_rotate_speed(rotate_speed_value)
                    executed.append(
                        {
                            "axis": "rotate_speed",
                            "value": rotate_speed_value,
                            "ack": frame.raw,
                        }
                    )

                rotate_delta = _shortest_delta_deg(self._pose.rotation_deg, rotation_deg)
                if abs(rotate_delta) > 0.001:
                    frame = await self._runtime.move_rotate_by(rotate_delta)
                    executed.append({"axis": "rotate", "delta_deg": rotate_delta, "ack": frame.raw})
                    self._pose.rotation_deg = _normalize_deg_360(self._pose.rotation_deg + rotate_delta)

                if tilt_speed_value is not None:
                    frame = await self._runtime.set_tilt_speed(tilt_speed_value)
                    executed.append(
                        {
                            "axis": "tilt_speed",
                            "value": tilt_speed_value,
                            "ack": frame.raw,
                        }
                    )

                if abs(tilt_deg - self._pose.tilt_deg) > 0.001:
                    frame = await self._runtime.move_tilt_to(tilt_deg)
                    executed.append({"axis": "tilt", "target_deg": tilt_deg, "ack": frame.raw})
                    self._pose.tilt_deg = tilt_deg

                return self._ok(
                    {
                        "executed": executed,
                        "rotation_deg": _normalize_deg_360(self._pose.rotation_deg),
                        "tilt_deg": self._pose.tilt_deg,
                        "zero_calibrated": self._pose.zero_calibrated,
                        "reference_frame": self._pose.reference_frame,
                    }
                )
            except BusyError:
                return self._error("DEVICE_BUSY", "Device is busy.", 409)
            except ValueError as exc:
                return self._error("VALIDATION_ERROR", str(exc), 422)
            except Exception as exc:  # noqa: BLE001
                return self._error("MOVE_FAILED", str(exc), 500)

    async def turntable_stop(self) -> dict[str, Any]:
        try:
            frames = await self._runtime.emergency_stop()
            return self._ok(
                {
                    "ack": [item.raw for item in frames],
                    "status": self._runtime.state.status.value,
                }
            )
        except Exception as exc:  # noqa: BLE001
            return self._error("STOP_FAILED", str(exc), 500)

    async def turntable_return_base(self) -> dict[str, Any]:
        """Return table to base 0 depending on available reference frame."""
        if self._action_lock.locked():
            return self._error("DEVICE_BUSY", "Device is busy.", 409)

        async with self._action_lock:
            executed: list[dict[str, Any]] = []
            try:
                if self._pose.zero_calibrated:
                    # Software zero is trusted for this session.
                    rotate_delta = _shortest_delta_deg(self._pose.rotation_deg, 0.0)
                    if abs(rotate_delta) > 0.001:
                        frame = await self._runtime.move_rotate_by(rotate_delta)
                        executed.append(
                            {"axis": "rotate", "delta_deg": rotate_delta, "ack": frame.raw}
                        )
                        self._pose.rotation_deg = _normalize_deg_360(
                            self._pose.rotation_deg + rotate_delta
                        )

                    if abs(self._pose.tilt_deg) > 0.001:
                        frame = await self._runtime.move_tilt_to(0.0)
                        executed.append({"axis": "tilt", "target_deg": 0.0, "ack": frame.raw})
                        self._pose.tilt_deg = 0.0

                    return self._ok(
                        {
                            "mode": "software_zero",
                            "executed": executed,
                            "rotation_deg": _normalize_deg_360(self._pose.rotation_deg),
                            "tilt_deg": self._pose.tilt_deg,
                            "zero_calibrated": self._pose.zero_calibrated,
                            "reference_frame": self._pose.reference_frame,
                        }
                    )

                # Fallback: hardware power-on base for rotate + explicit tilt 0.
                frame_rotate = await self._runtime.return_rotate_to_power_on_zero()
                executed.append({"axis": "rotate", "command": "+CT,TOZERO;", "ack": frame_rotate.raw})
                self._pose.rotation_deg = 0.0

                frame_tilt = await self._runtime.move_tilt_to(0.0)
                executed.append({"axis": "tilt", "command": "+CR,TILTVALUE=0;", "ack": frame_tilt.raw})
                self._pose.tilt_deg = 0.0
                self._pose.reference_frame = "power_on_zero"

                return self._ok(
                    {
                        "mode": "power_on_zero",
                        "executed": executed,
                        "rotation_deg": self._pose.rotation_deg,
                        "tilt_deg": self._pose.tilt_deg,
                        "zero_calibrated": self._pose.zero_calibrated,
                        "reference_frame": self._pose.reference_frame,
                    }
                )
            except BusyError:
                return self._error("DEVICE_BUSY", "Device is busy.", 409)
            except Exception as exc:  # noqa: BLE001
                return self._error("RETURN_BASE_FAILED", str(exc), 500)

    @staticmethod
    def _ok(result: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "result": result}

    @staticmethod
    def _error(code: str, message: str, http_status: int) -> dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "http_status": http_status,
            },
        }
