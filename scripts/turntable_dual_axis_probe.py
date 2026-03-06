"""Probe near-simultaneous rotate + tilt command dispatch.

The script measures command send times and first notify response timing for:
- optional speed set commands
- rotate move command
- tilt move command
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


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dual-axis concurrent dispatch probe.")
    parser.add_argument("--target-address", required=True)
    parser.add_argument("--rotate-speed", type=float, default=18.0)
    parser.add_argument("--tilt-speed", type=float, default=40.0)
    parser.add_argument("--rotate-angle", type=float, default=120.0)
    parser.add_argument("--tilt-target", type=float, default=20.0)
    parser.add_argument("--gap-seconds", type=float, default=0.05)
    parser.add_argument("--observe-seconds", type=float, default=12.0)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _decode(data: bytes) -> dict[str, Any]:
    return {"hex": data.hex(), "ascii": data.decode("utf-8", errors="replace").strip()}


async def _main() -> int:
    args = _parse_args()
    output_path = Path(args.output)
    _ensure_parent(output_path)

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "captured_at_utc": _iso_now(),
        "tool": "scripts/turntable_dual_axis_probe.py",
        "config": {
            "rotate_speed": args.rotate_speed,
            "tilt_speed": args.tilt_speed,
            "rotate_angle": args.rotate_angle,
            "tilt_target": args.tilt_target,
            "gap_seconds": args.gap_seconds,
            "observe_seconds": args.observe_seconds,
        },
        "timeline": [],
        "notifications": [],
        "errors": [],
    }

    def _notify(sender: Any, data: bytearray) -> None:
        report["notifications"].append(
            {"at_utc": _iso_now(), "sender": str(sender), "payload": _decode(bytes(data))}
        )

    client: BleakClient | None = None
    last_error: Exception | None = None
    try:
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

        await client.start_notify(TURNTABLE_PRIMARY_CHAR_UUID, _notify)

        commands = [
            f"+CT,TURNSPEED={args.rotate_speed};",
            f"+CR,TILTSPEED={args.tilt_speed};",
            f"+CT,TURNANGLE={args.rotate_angle};",
            f"+CR,TILTVALUE={args.tilt_target};",
        ]

        for idx, command in enumerate(commands):
            await client.write_gatt_char(
                TURNTABLE_PRIMARY_CHAR_UUID, command.encode("ascii"), response=False
            )
            report["timeline"].append({"index": idx, "command": command, "sent_at_utc": _iso_now()})
            await asyncio.sleep(args.gap_seconds)

        await asyncio.sleep(args.observe_seconds)

        for stop_cmd in ("+CT,STOP;", "+CR,STOP;"):
            await client.write_gatt_char(
                TURNTABLE_PRIMARY_CHAR_UUID, stop_cmd.encode("ascii"), response=False
            )
            report["timeline"].append({"command": stop_cmd, "sent_at_utc": _iso_now()})
            await asyncio.sleep(BLE_TIMING.command_gap_seconds)

        await asyncio.sleep(1.0)
        await client.stop_notify(TURNTABLE_PRIMARY_CHAR_UUID)
    except Exception as exc:  # noqa: BLE001
        report["errors"].append({"error_type": type(exc).__name__, "message": str(exc)})
    finally:
        if client is not None and client.is_connected:
            await client.disconnect()

    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Dual-axis probe written to: {output_path}")
    print(f"Notifications captured: {len(report['notifications'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
