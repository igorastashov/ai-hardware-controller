"""Decode valid speed command ranges for rotate/tilt axes.

This script sends only speed-setting commands and captures immediate notify
responses to identify accepted and rejected values.
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe speed command acceptance matrix.")
    parser.add_argument("--target-address", required=True)
    parser.add_argument("--axis", choices=["rotate", "tilt"], required=True)
    parser.add_argument(
        "--values",
        required=True,
        help="Comma-separated numeric values, e.g. 1,2,4,8,12",
    )
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _command(axis: str, value: str) -> str:
    if axis == "rotate":
        return f"+CT,TURNSPEED={value};"
    return f"+CR,TILTSPEED={value};"


def _decode(data: bytes) -> dict[str, Any]:
    text = data.decode("utf-8", errors="replace").strip()
    accepted = text == "+OK;"
    error_code = None
    if text.startswith("+FAIL,ERR=") and text.endswith(";"):
        error_code = text[len("+FAIL,ERR=") : -1]
    return {
        "hex": data.hex(),
        "ascii": text,
        "accepted": accepted,
        "error_code": error_code,
    }


async def _send_and_wait(
    client: BleakClient, command: str, wait_seconds: float = 0.8
) -> dict[str, Any]:
    captured: dict[str, Any] = {"frames": []}
    event = asyncio.Event()

    def _on_notify(sender: Any, data: bytearray) -> None:
        captured["frames"].append(
            {
                "at_utc": _iso_now(),
                "sender": str(sender),
                "payload": _decode(bytes(data)),
            }
        )
        event.set()

    await client.start_notify(TURNTABLE_PRIMARY_CHAR_UUID, _on_notify)
    await client.write_gatt_char(
        TURNTABLE_PRIMARY_CHAR_UUID, command.encode("ascii"), response=False
    )
    try:
        await asyncio.wait_for(event.wait(), timeout=wait_seconds)
    except TimeoutError:
        pass
    await client.stop_notify(TURNTABLE_PRIMARY_CHAR_UUID)

    first = captured["frames"][0]["payload"] if captured["frames"] else None
    return {
        "command": command,
        "first_response": first,
        "all_frames": captured["frames"],
    }


async def _main() -> int:
    args = _parse_args()
    output = Path(args.output)
    _ensure_parent(output)

    values = [item.strip() for item in args.values.split(",") if item.strip()]
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "captured_at_utc": _iso_now(),
        "tool": "scripts/turntable_speed_decode_probe.py",
        "target": {
            "address": args.target_address,
            "characteristic_uuid": TURNTABLE_PRIMARY_CHAR_UUID,
        },
        "config": {"axis": args.axis, "values": values},
        "results": [],
        "summary": {"accepted_values": [], "rejected_values": [], "timeouts": []},
        "errors": [],
    }

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
            for value in values:
                command = _command(args.axis, value)
                response = await _send_and_wait(client, command)
                report["results"].append({"value": value, **response})

                first = response["first_response"]
                if first is None:
                    report["summary"]["timeouts"].append(value)
                elif first["accepted"]:
                    report["summary"]["accepted_values"].append(value)
                else:
                    report["summary"]["rejected_values"].append(value)

                await asyncio.sleep(BLE_TIMING.command_gap_seconds)

            for stop_cmd in ("+CT,STOP;", "+CR,STOP;"):
                await client.write_gatt_char(
                    TURNTABLE_PRIMARY_CHAR_UUID, stop_cmd.encode("ascii"), response=False
                )
                await asyncio.sleep(BLE_TIMING.command_gap_seconds)
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
    print(f"Speed decode report written to: {output}")
    print(f"Accepted values: {report['summary']['accepted_values']}")
    print(f"Rejected values: {report['summary']['rejected_values']}")
    print(f"Timeout values: {report['summary']['timeouts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
