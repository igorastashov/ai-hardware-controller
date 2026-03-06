"""Timing probe for movement model calibration.

The device does not provide a reliable explicit motion-complete event yet.
This script captures command/ack timeline for speed + movement sequences and
stores a report that can be annotated with manual observations.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bleak import BleakClient

from turntable_config import BLE_TIMING, TURNTABLE_PRIMARY_CHAR_UUID


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _decode_payload(data: bytes) -> dict[str, Any]:
    return {
        "hex": data.hex(),
        "ascii": data.decode("utf-8", errors="replace"),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Timing probe for turntable motion model.")
    parser.add_argument("--target-address", required=True)
    parser.add_argument("--axis", choices=["rotate", "tilt"], required=True)
    parser.add_argument(
        "--speed-values",
        required=True,
        help="Comma separated speed command values, e.g. 8,12,20",
    )
    parser.add_argument(
        "--move-value",
        required=True,
        help="Movement value per run: rotate delta deg or tilt target deg.",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=8.0,
        help="Wait after move command to observe notifications and movement.",
    )
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _commands_for(axis: str, speed_value: str, move_value: str) -> tuple[str, str]:
    if axis == "rotate":
        return f"+CT,TURNSPEED={speed_value};", f"+CT,TURNANGLE={move_value};"
    return f"+CR,TILTSPEED={speed_value};", f"+CR,TILTVALUE={move_value};"


async def _main() -> int:
    args = _parse_args()
    output = Path(args.output)
    _ensure_parent(output)

    notifications: list[dict[str, Any]] = []
    speed_values = [item.strip() for item in args.speed_values.split(",") if item.strip()]

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "captured_at_utc": _iso_now(),
        "tool": "scripts/turntable_timing_probe.py",
        "target": {
            "address": args.target_address,
            "characteristic_uuid": TURNTABLE_PRIMARY_CHAR_UUID,
        },
        "config": {
            "axis": args.axis,
            "speed_values": speed_values,
            "move_value": args.move_value,
            "settle_seconds": args.settle_seconds,
        },
        "runs": [],
        "manual_observations_template": {
            "instruction": "Fill by human observation for each run_index",
            "fields": ["run_index", "observed_start_delay_s", "observed_end_time_s", "notes"],
            "entries": [],
        },
        "errors": [],
    }

    def _on_notify(sender: Any, data: bytearray) -> None:
        notifications.append(
            {
                "received_at_utc": _iso_now(),
                "sender": str(sender),
                "payload": _decode_payload(bytes(data)),
            }
        )

    try:
        client: BleakClient | None = None
        last_error: Exception | None = None
        for attempt in range(BLE_TIMING.connect_retry_attempts):
            try:
                candidate = BleakClient(
                    args.target_address, timeout=BLE_TIMING.connect_timeout_seconds
                )
                await candidate.connect()
                client = candidate
                last_error = None
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < BLE_TIMING.connect_retry_attempts - 1:
                    await asyncio.sleep(BLE_TIMING.connect_retry_delay_seconds)

        if client is None:
            raise last_error if last_error is not None else RuntimeError("Connect failed")

        try:
            await client.start_notify(TURNTABLE_PRIMARY_CHAR_UUID, _on_notify)

            for idx, speed in enumerate(speed_values):
                run_start = _iso_now()
                speed_cmd, move_cmd = _commands_for(args.axis, speed, args.move_value)

                speed_bytes = speed_cmd.encode("ascii")
                await client.write_gatt_char(
                    TURNTABLE_PRIMARY_CHAR_UUID, speed_bytes, response=False
                )
                await asyncio.sleep(BLE_TIMING.command_gap_seconds)

                move_bytes = move_cmd.encode("ascii")
                await client.write_gatt_char(
                    TURNTABLE_PRIMARY_CHAR_UUID, move_bytes, response=False
                )
                await asyncio.sleep(args.settle_seconds)

                run_notifications = [
                    item for item in notifications if item["received_at_utc"] >= run_start
                ]
                report["runs"].append(
                    {
                        "run_index": idx,
                        "started_at_utc": run_start,
                        "speed_command": speed_cmd,
                        "move_command": move_cmd,
                        "notifications": run_notifications,
                    }
                )

            for stop_cmd in ("+CT,STOP;", "+CR,STOP;"):
                await client.write_gatt_char(
                    TURNTABLE_PRIMARY_CHAR_UUID, stop_cmd.encode("ascii"), response=False
                )
                await asyncio.sleep(BLE_TIMING.command_gap_seconds)

            await asyncio.sleep(1.0)
            await client.stop_notify(TURNTABLE_PRIMARY_CHAR_UUID)
        finally:
            if client.is_connected:
                await client.disconnect()
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(
            {
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
        )

    output.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Timing probe report written to: {output}")
    print(f"Runs executed: {len(report['runs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
