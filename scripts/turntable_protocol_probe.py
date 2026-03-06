"""Protocol probe for Revopoint Dual-axis Turntable.

This script performs a non-motion diagnostic:
- connect to the turntable
- subscribe to notify on selected characteristic
- send a query command (default: tilt angle query)
- capture raw notifications and decoded text variants

All probe output is persisted as a JSON artifact for later analysis.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bleak import BleakClient

from turntable_config import (
    BLE_TIMING,
    TURNTABLE_DEVICE_NAME_HINT,
    TURNTABLE_PRIMARY_CHAR_UUID,
    TURNTABLE_PROTOCOL_QUERY_TILT_ANGLE,
)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Non-motion BLE protocol probe for turntable."
    )
    parser.add_argument(
        "--target-address",
        required=True,
        help="BLE address of turntable (required for direct probe).",
    )
    parser.add_argument(
        "--char-uuid",
        default=TURNTABLE_PRIMARY_CHAR_UUID,
        help="Characteristic UUID used for write/notify probe.",
    )
    parser.add_argument(
        "--command",
        default=TURNTABLE_PROTOCOL_QUERY_TILT_ANGLE,
        help="Query command payload to send.",
    )
    parser.add_argument(
        "--encoding",
        default="ascii",
        choices=["ascii", "utf-8"],
        help="Encoding used to convert command string to bytes.",
    )
    parser.add_argument(
        "--append-crlf",
        action="store_true",
        help="Append CRLF after command to test protocol terminator behavior.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=float,
        default=BLE_TIMING.protocol_probe_wait_seconds,
        help="Seconds to wait for notifications after sending command.",
    )
    parser.add_argument(
        "--output",
        default="docs/references/artifacts/revopoint-dual-axis-protocol-probe.json",
        help="JSON artifact output path.",
    )
    return parser.parse_args()


def _decode_payload(data: bytearray) -> dict[str, Any]:
    raw_bytes = bytes(data)
    decoded: dict[str, Any] = {
        "hex": raw_bytes.hex(),
        "ascii": None,
        "utf8": None,
        "errors": [],
    }

    for codec in ("ascii", "utf-8"):
        try:
            decoded[codec.replace("-", "")] = raw_bytes.decode(codec)
        except Exception as exc:  # noqa: BLE001
            decoded["errors"].append(
                {
                    "codec": codec,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
    return decoded


def _ensure_output_dir(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)


async def _run_probe(args: argparse.Namespace) -> dict[str, Any]:
    notifications: list[dict[str, Any]] = []
    start_time = _iso_now()

    payload = args.command
    if args.append_crlf:
        payload = f"{payload}\r\n"

    command_bytes = payload.encode(args.encoding)

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "captured_at_utc": start_time,
        "tool": "scripts/turntable_protocol_probe.py",
        "target": {
            "name_hint": TURNTABLE_DEVICE_NAME_HINT,
            "address": args.target_address,
            "characteristic_uuid": args.char_uuid,
        },
        "probe_config": {
            "command_string": args.command,
            "encoding": args.encoding,
            "append_crlf": args.append_crlf,
            "wait_seconds": args.wait_seconds,
            "command_hex": command_bytes.hex(),
        },
        "result": {
            "connected": False,
            "write_sent": False,
            "notifications_count": 0,
            "notifications": [],
            "errors": [],
        },
    }

    def _on_notify(sender: Any, data: bytearray) -> None:
        notifications.append(
            {
                "received_at_utc": _iso_now(),
                "sender": str(sender),
                "payload": _decode_payload(data),
            }
        )

    try:
        async with BleakClient(
            args.target_address, timeout=BLE_TIMING.connect_timeout_seconds
        ) as client:
            report["result"]["connected"] = client.is_connected
            await client.start_notify(args.char_uuid, _on_notify)
            await client.write_gatt_char(args.char_uuid, command_bytes, response=False)
            report["result"]["write_sent"] = True
            await asyncio.sleep(args.wait_seconds)
            await client.stop_notify(args.char_uuid)
    except Exception as exc:  # noqa: BLE001
        report["result"]["errors"].append(
            {
                "stage": "probe",
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
        )

    report["result"]["notifications_count"] = len(notifications)
    report["result"]["notifications"] = notifications
    return report


async def _main() -> int:
    args = _parse_args()
    output_path = Path(args.output)
    _ensure_output_dir(output_path)
    report = await _run_probe(args)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Protocol probe report written to: {output_path}")
    print(f"Notifications captured: {report['result']['notifications_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
