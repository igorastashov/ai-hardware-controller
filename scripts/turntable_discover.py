"""BLE discovery utility for Revopoint Dual-axis Turntable.

The script collects as much non-destructive information as possible:
- scan results
- selected target device metadata
- full GATT profile (services, characteristics, descriptors)

Output is a JSON report used as a source for device documentation.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bleak import BleakClient, BleakScanner

from turntable_config import BLE_TIMING, TURNTABLE_DEVICE_NAME_HINT


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover BLE capabilities of a turntable device."
    )
    parser.add_argument(
        "--target-name",
        default=TURNTABLE_DEVICE_NAME_HINT,
        help="Substring for BLE device name matching.",
    )
    parser.add_argument(
        "--target-address",
        default="",
        help="Exact BLE address. If set, has priority over --target-name.",
    )
    parser.add_argument(
        "--output",
        default="docs/references/artifacts/revopoint-dual-axis-discovery.json",
        help="Output JSON report path.",
    )
    parser.add_argument(
        "--scan-seconds",
        type=float,
        default=BLE_TIMING.discovery_scan_seconds,
        help="BLE scan duration in seconds.",
    )
    return parser.parse_args()


async def _scan(scan_seconds: float) -> list[dict[str, Any]]:
    devices = await BleakScanner.discover(timeout=scan_seconds)
    result: list[dict[str, Any]] = []
    for item in devices:
        metadata = getattr(item, "metadata", {})
        if metadata is None:
            metadata = {}
        result.append(
            {
                "address": item.address,
                "name": item.name,
                "rssi": getattr(item, "rssi", None),
                "details": str(item.details) if item.details is not None else None,
                "metadata": metadata,
            }
        )
    return result


def _pick_target(
    scanned: list[dict[str, Any]], target_name: str, target_address: str
) -> dict[str, Any] | None:
    if target_address:
        for item in scanned:
            if item["address"].lower() == target_address.lower():
                return item
        return None

    for item in scanned:
        if item["name"] and target_name.lower() in item["name"].lower():
            return item
    return None


async def _read_gatt(address: str) -> dict[str, Any]:
    async with BleakClient(
        address, timeout=BLE_TIMING.connect_timeout_seconds
    ) as client:
        services_payload: list[dict[str, Any]] = []
        for service in client.services:
            characteristics_payload: list[dict[str, Any]] = []
            for characteristic in service.characteristics:
                descriptors_payload = []
                for descriptor in characteristic.descriptors:
                    descriptors_payload.append(
                        {
                            "handle": descriptor.handle,
                            "uuid": descriptor.uuid,
                            "description": str(descriptor.description),
                        }
                    )
                characteristics_payload.append(
                    {
                        "handle": characteristic.handle,
                        "uuid": characteristic.uuid,
                        "description": str(characteristic.description),
                        "properties": sorted(characteristic.properties),
                        "descriptors": descriptors_payload,
                    }
                )
            services_payload.append(
                {
                    "handle": service.handle,
                    "uuid": service.uuid,
                    "description": str(service.description),
                    "characteristics": characteristics_payload,
                }
            )

        return {
            "connected": client.is_connected,
            "services": services_payload,
        }


def _ensure_output_dir(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)


async def _main() -> int:
    args = _parse_args()
    start = _iso_now()
    output_path = Path(args.output)
    _ensure_output_dir(output_path)

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "captured_at_utc": start,
        "tool": "scripts/turntable_discover.py",
        "scan_seconds": args.scan_seconds,
        "config_snapshot": {
            "ble_timing": asdict(BLE_TIMING),
            "target_name_hint": args.target_name,
        },
        "result": {
            "target_found": False,
            "target": None,
            "scan": [],
            "gatt": None,
            "errors": [],
        },
    }

    try:
        scan_payload = await _scan(args.scan_seconds)
        report["result"]["scan"] = scan_payload
    except Exception as exc:  # noqa: BLE001
        report["result"]["errors"].append(
            {
                "stage": "scan",
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
        )

    target = _pick_target(report["result"]["scan"], args.target_name, args.target_address)
    if target:
        report["result"]["target_found"] = True
        report["result"]["target"] = target
        try:
            report["result"]["gatt"] = await _read_gatt(target["address"])
        except Exception as exc:  # noqa: BLE001
            report["result"]["errors"].append(
                {
                    "stage": "gatt",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
    else:
        report["result"]["errors"].append(
            {
                "stage": "select_target",
                "error_type": "TargetNotFound",
                "message": "No target device matched selection criteria.",
            }
        )

    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Discovery report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
