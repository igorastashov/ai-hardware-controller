"""CLI wrapper over TurntableToolAdapter for agent-style usage."""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from turntable_tool_adapter import TurntableToolAdapter


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Turntable tool CLI")
    parser.add_argument(
        "--address",
        default="D3:36:39:34:5D:29",
        help="BLE address of turntable device.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("state", help="Get current adapter/runtime state.")
    sub.add_parser("home", help="Set current pose as software zero.")
    sub.add_parser("stop", help="Emergency stop both axes.")
    sub.add_parser("return-base", help="Return to base zero (software or power-on frame).")

    move = sub.add_parser("move-to", help="Move to absolute rotate/tilt targets.")
    move.add_argument("--rotation-deg", type=float, required=True)
    move.add_argument("--tilt-deg", type=float, required=True)
    move.add_argument("--rotate-speed", type=float, required=False)
    move.add_argument("--tilt-speed", type=float, required=False)

    return parser


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    adapter = TurntableToolAdapter(address=args.address)
    connect_result = await adapter.connect()
    if not connect_result.get("ok", False):
        return connect_result

    try:
        if args.command == "state":
            return await adapter.turntable_state()
        if args.command == "home":
            return await adapter.turntable_home()
        if args.command == "stop":
            return await adapter.turntable_stop()
        if args.command == "return-base":
            return await adapter.turntable_return_base()
        if args.command == "move-to":
            return await adapter.turntable_move_to(
                rotation_deg=args.rotation_deg,
                tilt_deg=args.tilt_deg,
                rotate_speed_value=args.rotate_speed,
                tilt_speed_value=args.tilt_speed,
            )
        return {"ok": False, "error": {"code": "UNKNOWN_COMMAND", "message": args.command}}
    finally:
        await adapter.disconnect()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    result = asyncio.run(_run(args))
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
