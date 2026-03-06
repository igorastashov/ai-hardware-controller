"""Probe controller behavior for rapid consecutive motion commands.

This script helps answer:
- Does the device reject a second command while first is in progress?
- Are quick cross-axis commands accepted?
- Do we receive explicit FAIL/BUSY responses or only OK acknowledgements?
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


def _decode(data: bytes) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "hex": data.hex(),
        "ascii": None,
        "utf8": None,
        "errors": [],
    }
    for codec in ("ascii", "utf-8"):
        try:
            payload[codec.replace("-", "")] = data.decode(codec)
        except Exception as exc:  # noqa: BLE001
            payload["errors"].append(
                {
                    "codec": codec,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Characterize busy/queue behavior for rapid commands."
    )
    parser.add_argument("--target-address", required=True)
    parser.add_argument("--command-1", required=True)
    parser.add_argument("--command-2", required=True)
    parser.add_argument("--gap-seconds", type=float, default=0.1)
    parser.add_argument("--listen-seconds", type=float, default=8.0)
    parser.add_argument(
        "--output",
        required=True,
        help="Output artifact path.",
    )
    return parser.parse_args()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


async def _main() -> int:
    args = _parse_args()
    output = Path(args.output)
    _ensure_parent(output)

    notifications: list[dict[str, Any]] = []
    sent_events: list[dict[str, Any]] = []

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "captured_at_utc": _iso_now(),
        "tool": "scripts/turntable_busy_characterize.py",
        "target": {
            "address": args.target_address,
            "characteristic_uuid": TURNTABLE_PRIMARY_CHAR_UUID,
        },
        "config": {
            "command_1": args.command_1,
            "command_2": args.command_2,
            "gap_seconds": args.gap_seconds,
            "listen_seconds": args.listen_seconds,
        },
        "result": {
            "connected": False,
            "sent_events": [],
            "notifications": [],
            "errors": [],
        },
    }

    def _on_notify(sender: Any, data: bytearray) -> None:
        notifications.append(
            {
                "received_at_utc": _iso_now(),
                "sender": str(sender),
                "payload": _decode(bytes(data)),
            }
        )

    try:
        async with BleakClient(
            args.target_address, timeout=BLE_TIMING.connect_timeout_seconds
        ) as client:
            report["result"]["connected"] = client.is_connected
            await client.start_notify(TURNTABLE_PRIMARY_CHAR_UUID, _on_notify)

            cmd1 = args.command_1.encode("ascii")
            await client.write_gatt_char(TURNTABLE_PRIMARY_CHAR_UUID, cmd1, response=False)
            sent_events.append(
                {"at_utc": _iso_now(), "command": args.command_1, "hex": cmd1.hex()}
            )

            await asyncio.sleep(args.gap_seconds)

            cmd2 = args.command_2.encode("ascii")
            await client.write_gatt_char(TURNTABLE_PRIMARY_CHAR_UUID, cmd2, response=False)
            sent_events.append(
                {"at_utc": _iso_now(), "command": args.command_2, "hex": cmd2.hex()}
            )

            await asyncio.sleep(args.listen_seconds)

            for stop_cmd in ("+CT,STOP;", "+CR,STOP;"):
                encoded = stop_cmd.encode("ascii")
                await client.write_gatt_char(
                    TURNTABLE_PRIMARY_CHAR_UUID, encoded, response=False
                )
                sent_events.append(
                    {"at_utc": _iso_now(), "command": stop_cmd, "hex": encoded.hex()}
                )
                await asyncio.sleep(BLE_TIMING.command_gap_seconds)

            await asyncio.sleep(1.0)
            await client.stop_notify(TURNTABLE_PRIMARY_CHAR_UUID)
    except Exception as exc:  # noqa: BLE001
        report["result"]["errors"].append(
            {
                "stage": "run",
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
        )

    report["result"]["sent_events"] = sent_events
    report["result"]["notifications"] = notifications

    output.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Busy characterization report written to: {output}")
    print(f"Notifications captured: {len(notifications)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
