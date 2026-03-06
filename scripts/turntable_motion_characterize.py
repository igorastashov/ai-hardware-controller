"""Characterize turntable telemetry around motion commands.

Flow:
1) query baseline state for both axes
2) send a small motion command
3) poll query command over a time window
4) persist all events to JSON artifact
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
    TURNTABLE_PRIMARY_CHAR_UUID,
    TURNTABLE_PROTOCOL_QUERY_ROTATE_ANGLE,
    TURNTABLE_PROTOCOL_QUERY_TILT_ANGLE,
)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Characterize telemetry behavior around motion commands."
    )
    parser.add_argument("--target-address", required=True, help="BLE MAC address.")
    parser.add_argument(
        "--move-command",
        required=True,
        help="Motion command to send, e.g. +CT,TURNANGLE=10; or +CR,TILTVALUE=5;",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=BLE_TIMING.motion_poll_interval_seconds,
    )
    parser.add_argument(
        "--poll-total-seconds",
        type=float,
        default=BLE_TIMING.motion_poll_total_seconds,
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON artifact path.",
    )
    return parser.parse_args()


def _decode_payload(data: bytes) -> dict[str, Any]:
    decoded: dict[str, Any] = {
        "hex": data.hex(),
        "ascii": None,
        "utf8": None,
        "errors": [],
    }
    for codec in ("ascii", "utf-8"):
        try:
            key = codec.replace("-", "")
            decoded[key] = data.decode(codec)
        except Exception as exc:  # noqa: BLE001
            decoded["errors"].append(
                {
                    "codec": codec,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
    return decoded


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


async def _write_and_collect(
    client: BleakClient,
    char_uuid: str,
    command: str,
    wait_seconds: float,
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    command_bytes = command.encode("ascii")
    sent_at = _iso_now()

    def _on_notify(sender: Any, data: bytearray) -> None:
        events.append(
            {
                "received_at_utc": _iso_now(),
                "sender": str(sender),
                "payload": _decode_payload(bytes(data)),
            }
        )

    await client.start_notify(char_uuid, _on_notify)
    await client.write_gatt_char(char_uuid, command_bytes, response=False)
    await asyncio.sleep(wait_seconds)
    await client.stop_notify(char_uuid)

    return {
        "sent_at_utc": sent_at,
        "collected_until_utc": _iso_now(),
        "command": command,
        "command_hex": command_bytes.hex(),
        "events": events,
    }


async def _main() -> int:
    args = _parse_args()
    output = Path(args.output)
    _ensure_parent(output)

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "captured_at_utc": _iso_now(),
        "tool": "scripts/turntable_motion_characterize.py",
        "target": {
            "address": args.target_address,
            "characteristic_uuid": TURNTABLE_PRIMARY_CHAR_UUID,
        },
        "config": {
            "move_command": args.move_command,
            "poll_interval_seconds": args.poll_interval_seconds,
            "poll_total_seconds": args.poll_total_seconds,
        },
        "result": {
            "connected": False,
            "baseline": {},
            "motion_ack": {},
            "polling": [],
            "errors": [],
        },
    }

    poll_count = max(1, int(args.poll_total_seconds / args.poll_interval_seconds))

    try:
        async with BleakClient(
            args.target_address, timeout=BLE_TIMING.connect_timeout_seconds
        ) as client:
            report["result"]["connected"] = client.is_connected
            report["result"]["baseline"]["tilt"] = await _write_and_collect(
                client,
                TURNTABLE_PRIMARY_CHAR_UUID,
                TURNTABLE_PROTOCOL_QUERY_TILT_ANGLE,
                max(0.6, args.poll_interval_seconds),
            )
            await asyncio.sleep(BLE_TIMING.command_gap_seconds)
            report["result"]["baseline"]["rotate"] = await _write_and_collect(
                client,
                TURNTABLE_PRIMARY_CHAR_UUID,
                TURNTABLE_PROTOCOL_QUERY_ROTATE_ANGLE,
                max(0.6, args.poll_interval_seconds),
            )
            await asyncio.sleep(BLE_TIMING.command_gap_seconds)

            report["result"]["motion_ack"] = await _write_and_collect(
                client,
                TURNTABLE_PRIMARY_CHAR_UUID,
                args.move_command,
                max(0.6, args.poll_interval_seconds),
            )

            for _ in range(poll_count):
                await asyncio.sleep(BLE_TIMING.command_gap_seconds)
                tilt_sample = await _write_and_collect(
                    client,
                    TURNTABLE_PRIMARY_CHAR_UUID,
                    TURNTABLE_PROTOCOL_QUERY_TILT_ANGLE,
                    max(0.6, args.poll_interval_seconds),
                )
                await asyncio.sleep(BLE_TIMING.command_gap_seconds)
                rotate_sample = await _write_and_collect(
                    client,
                    TURNTABLE_PRIMARY_CHAR_UUID,
                    TURNTABLE_PROTOCOL_QUERY_ROTATE_ANGLE,
                    max(0.6, args.poll_interval_seconds),
                )
                report["result"]["polling"].append(
                    {
                        "at_utc": _iso_now(),
                        "tilt": tilt_sample,
                        "rotate": rotate_sample,
                    }
                )
    except Exception as exc:  # noqa: BLE001
        report["result"]["errors"].append(
            {
                "stage": "run",
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
        )

    output.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Motion characterization report written to: {output}")
    print(f"Polling samples: {len(report['result']['polling'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
