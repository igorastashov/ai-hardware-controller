"""Single-flight runtime skeleton for Revopoint turntable control.

Design goals:
- enforce software-side mutex for motion commands
- keep state transitions explicit (IDLE/BUSY/ERROR)
- parse protocol frames (+OK, +FAIL, +DATA)
- use timing model for motion completion (until deterministic done-event is known)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any

from bleak import BleakClient

from turntable_config import (
    AXIS_LIMITS,
    BLE_TIMING,
    MOTION_TIMING,
    SPEED_BOUNDS,
    TURNTABLE_PRIMARY_CHAR_UUID,
    TURNTABLE_PROTOCOL_QUERY_ROTATE_ANGLE,
    TURNTABLE_PROTOCOL_QUERY_TILT_ANGLE,
)


class RuntimeStatus(str, Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"


@dataclass(frozen=True)
class RuntimeState:
    status: RuntimeStatus
    ble_connected: bool
    last_error_code: str | None
    last_error_message: str | None


class BusyError(RuntimeError):
    """Raised when motion command arrives while runtime is BUSY."""


class ProtocolError(RuntimeError):
    """Raised when device returns +FAIL or unexpected protocol frame."""


@dataclass(frozen=True)
class ProtocolFrame:
    kind: str
    raw: str
    error_code: str | None = None
    data_values: tuple[float, ...] | None = None


def _parse_frame(text: str) -> ProtocolFrame:
    payload = text.strip()
    if payload == "+OK;":
        return ProtocolFrame(kind="ok", raw=payload)
    if payload.startswith("+FAIL,ERR=") and payload.endswith(";"):
        code = payload[len("+FAIL,ERR=") : -1]
        return ProtocolFrame(kind="fail", raw=payload, error_code=code)
    if payload.startswith("+DATA=") and payload.endswith(";"):
        raw_values = payload[len("+DATA=") : -1].split(",")
        values = tuple(float(x) for x in raw_values if x != "")
        return ProtocolFrame(kind="data", raw=payload, data_values=values)
    return ProtocolFrame(kind="unknown", raw=payload)


def estimate_motion_duration_seconds(command: str) -> float:
    """Estimate command completion time using current coarse timing model."""
    if command.startswith("+CT,TURNANGLE=") and command.endswith(";"):
        delta = float(command[len("+CT,TURNANGLE=") : -1])
        seconds = (
            MOTION_TIMING.rotate_start_delay_seconds
            + (abs(delta) / MOTION_TIMING.default_rotate_deg_per_s)
        )
    elif command.startswith("+CR,TILTVALUE=") and command.endswith(";"):
        target = float(command[len("+CR,TILTVALUE=") : -1])
        # No reliable absolute live pose yet; use magnitude as conservative proxy.
        seconds = (
            MOTION_TIMING.tilt_start_delay_seconds
            + (abs(target) / MOTION_TIMING.default_tilt_deg_per_s)
        )
    else:
        seconds = 0.0

    return min(
        MOTION_TIMING.max_command_duration_seconds,
        seconds + MOTION_TIMING.completion_safety_buffer_seconds,
    )


class TurntableRuntimeSingleFlight:
    """Runtime core to be used by future agent tools."""

    def __init__(self, address: str) -> None:
        self._address = address
        self._client = BleakClient(address, timeout=BLE_TIMING.connect_timeout_seconds)
        self._motion_lock = asyncio.Lock()
        self._io_lock = asyncio.Lock()
        self._frames: list[ProtocolFrame] = []
        self._state = RuntimeState(
            status=RuntimeStatus.IDLE,
            ble_connected=False,
            last_error_code=None,
            last_error_message=None,
        )

    @property
    def state(self) -> RuntimeState:
        return self._state

    async def connect(self) -> None:
        last_error: Exception | None = None
        for attempt in range(BLE_TIMING.connect_retry_attempts):
            try:
                await self._client.connect()
                last_error = None
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < BLE_TIMING.connect_retry_attempts - 1:
                    await asyncio.sleep(BLE_TIMING.connect_retry_delay_seconds)

        if last_error is not None and not self._client.is_connected:
            raise last_error

        self._state = RuntimeState(
            status=RuntimeStatus.IDLE,
            ble_connected=self._client.is_connected,
            last_error_code=self._state.last_error_code,
            last_error_message=self._state.last_error_message,
        )

    async def disconnect(self) -> None:
        if self._client.is_connected:
            await self._client.disconnect()
        self._state = RuntimeState(
            status=self._state.status,
            ble_connected=False,
            last_error_code=self._state.last_error_code,
            last_error_message=self._state.last_error_message,
        )

    async def query_tilt(self) -> ProtocolFrame:
        return await self._send_and_wait_frame(TURNTABLE_PROTOCOL_QUERY_TILT_ANGLE, 0.8)

    async def query_rotate(self) -> ProtocolFrame:
        return await self._send_and_wait_frame(TURNTABLE_PROTOCOL_QUERY_ROTATE_ANGLE, 0.8)

    async def move_rotate_by(self, delta_deg: float) -> ProtocolFrame:
        command = f"+CT,TURNANGLE={delta_deg};"
        return await self._run_motion(command)

    async def set_rotate_speed(self, speed_value: float) -> ProtocolFrame:
        if (
            speed_value < SPEED_BOUNDS.rotate_min_observed_ok
            or speed_value > SPEED_BOUNDS.rotate_max_observed_ok
        ):
            raise ValueError(
                f"Rotate speed must be within "
                f"[{SPEED_BOUNDS.rotate_min_observed_ok}, {SPEED_BOUNDS.rotate_max_observed_ok}]."
            )
        return await self._send_and_wait_frame(f"+CT,TURNSPEED={speed_value};", 0.8)

    async def move_tilt_to(self, target_deg: float) -> ProtocolFrame:
        if target_deg < AXIS_LIMITS.tilt_min_deg or target_deg > AXIS_LIMITS.tilt_max_deg:
            raise ValueError("Tilt target is outside configured limits.")
        command = f"+CR,TILTVALUE={target_deg};"
        return await self._run_motion(command)

    async def set_tilt_speed(self, speed_value: float) -> ProtocolFrame:
        if (
            speed_value < SPEED_BOUNDS.tilt_min_observed_ok
            or speed_value > SPEED_BOUNDS.tilt_max_observed_ok
        ):
            raise ValueError(
                f"Tilt speed must be within "
                f"[{SPEED_BOUNDS.tilt_min_observed_ok}, {SPEED_BOUNDS.tilt_max_observed_ok}]."
            )
        return await self._send_and_wait_frame(f"+CR,TILTSPEED={speed_value};", 0.8)

    async def emergency_stop(self) -> list[ProtocolFrame]:
        frames: list[ProtocolFrame] = []
        for command in ("+CT,STOP;", "+CR,STOP;"):
            frame = await self._send_and_wait_frame(command, 0.8)
            frames.append(frame)

        self._state = RuntimeState(
            status=RuntimeStatus.IDLE,
            ble_connected=self._client.is_connected,
            last_error_code=self._state.last_error_code,
            last_error_message=self._state.last_error_message,
        )
        return frames

    async def return_rotate_to_power_on_zero(self) -> ProtocolFrame:
        """Return rotate axis to device power-on zero."""
        return await self._run_motion("+CT,TOZERO;")

    async def _run_motion(self, command: str) -> ProtocolFrame:
        if self._motion_lock.locked():
            raise BusyError("Device is busy with another motion command.")

        async with self._motion_lock:
            self._state = RuntimeState(
                status=RuntimeStatus.BUSY,
                ble_connected=self._client.is_connected,
                last_error_code=self._state.last_error_code,
                last_error_message=self._state.last_error_message,
            )

            try:
                frame = await self._send_and_wait_frame(command, 0.8)
                if frame.kind == "fail":
                    raise ProtocolError(f"Motion rejected with error {frame.error_code}")

                await asyncio.sleep(estimate_motion_duration_seconds(command))
                self._state = RuntimeState(
                    status=RuntimeStatus.IDLE,
                    ble_connected=self._client.is_connected,
                    last_error_code=self._state.last_error_code,
                    last_error_message=self._state.last_error_message,
                )
                return frame
            except Exception as exc:  # noqa: BLE001
                self._state = RuntimeState(
                    status=RuntimeStatus.ERROR,
                    ble_connected=self._client.is_connected,
                    last_error_code=self._state.last_error_code,
                    last_error_message=str(exc),
                )
                raise

    async def _send_and_wait_frame(self, command: str, wait_seconds: float) -> ProtocolFrame:
        if not self._client.is_connected:
            raise RuntimeError("BLE client is not connected.")

        async with self._io_lock:
            event = asyncio.Event()
            captured: dict[str, ProtocolFrame] = {}
            payload = command.encode("ascii")

            def _on_notify(_sender: Any, data: bytearray) -> None:
                text = bytes(data).decode("utf-8", errors="replace")
                frame = _parse_frame(text)
                self._frames.append(frame)
                if "frame" not in captured:
                    captured["frame"] = frame
                    event.set()

            await self._client.start_notify(TURNTABLE_PRIMARY_CHAR_UUID, _on_notify)
            await self._client.write_gatt_char(
                TURNTABLE_PRIMARY_CHAR_UUID, payload, response=False
            )

            try:
                await asyncio.wait_for(event.wait(), timeout=wait_seconds)
            except TimeoutError as exc:
                await self._client.stop_notify(TURNTABLE_PRIMARY_CHAR_UUID)
                raise ProtocolError(f"No notify response for command: {command}") from exc

            await self._client.stop_notify(TURNTABLE_PRIMARY_CHAR_UUID)
            frame = captured["frame"]
            if frame.kind == "fail":
                self._state = RuntimeState(
                    status=RuntimeStatus.ERROR,
                    ble_connected=self._client.is_connected,
                    last_error_code=frame.error_code,
                    last_error_message=frame.raw,
                )
            return frame
