"""FastAPI surface for TurntableToolAdapter.

This module exposes the current tool contract over HTTP for agent integration.
"""

from __future__ import annotations

import argparse
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from turntable_commissioning import CommissioningOptions, run_first_start_commissioning
from turntable_tool_adapter import TurntableToolAdapter


class MoveToRequest(BaseModel):
    rotation_deg: float = Field(..., description="Absolute rotate target in degrees.")
    tilt_deg: float = Field(..., description="Absolute tilt target in degrees.")
    rotate_speed_value: float | None = Field(
        default=None,
        description="Optional rotate speed command value.",
    )
    tilt_speed_value: float | None = Field(
        default=None,
        description="Optional tilt speed command value.",
    )


class FirstRunCommissioningRequest(BaseModel):
    max_capability: bool = Field(
        default=True,
        description="Use max-capability profile (speed/limits) when true.",
    )
    include_busy_check: bool = Field(
        default=True,
        description="Include parallel move check for DEVICE_BUSY policy.",
    )
    include_stop_check: bool = Field(
        default=True,
        description="Include emergency stop check during active motion.",
    )


def create_app(address: str, adapter: TurntableToolAdapter | None = None) -> FastAPI:
    app = FastAPI(title="Turntable Tool API", version="0.1.0")
    tool_adapter = adapter if adapter is not None else TurntableToolAdapter(address=address)

    async def _invoke(result: dict[str, Any]) -> tuple[dict[str, Any], int]:
        if result.get("ok", False):
            return result, 200
        error = result.get("error", {})
        return result, int(error.get("http_status", 500))

    async def _ensure_connected() -> dict[str, Any] | None:
        state = await tool_adapter.turntable_state()
        if not state.get("ok", False):
            return state
        if state.get("result", {}).get("ble_connected", False):
            return None
        connect_result = await tool_adapter.connect()
        if connect_result.get("ok", False):
            return None
        return connect_result

    @app.get("/health")
    async def health() -> dict[str, Any]:
        state = await tool_adapter.turntable_state()
        healthy = state.get("ok", False) and state.get("result", {}).get("ble_connected", False)
        return {"ok": True, "result": {"healthy": healthy}}

    @app.post("/state")
    async def state() -> JSONResponse:
        connect_error = await _ensure_connected()
        if connect_error is not None:
            payload, status_code = await _invoke(connect_error)
            return JSONResponse(content=payload, status_code=status_code)
        result = await tool_adapter.turntable_state()
        payload, status_code = await _invoke(result)
        return JSONResponse(content=payload, status_code=status_code)

    @app.post("/home")
    async def home() -> JSONResponse:
        connect_error = await _ensure_connected()
        if connect_error is not None:
            payload, status_code = await _invoke(connect_error)
            return JSONResponse(content=payload, status_code=status_code)
        result = await tool_adapter.turntable_home()
        payload, status_code = await _invoke(result)
        return JSONResponse(content=payload, status_code=status_code)

    @app.post("/move-to")
    async def move_to(body: MoveToRequest) -> JSONResponse:
        connect_error = await _ensure_connected()
        if connect_error is not None:
            payload, status_code = await _invoke(connect_error)
            return JSONResponse(content=payload, status_code=status_code)
        result = await tool_adapter.turntable_move_to(
            rotation_deg=body.rotation_deg,
            tilt_deg=body.tilt_deg,
            rotate_speed_value=body.rotate_speed_value,
            tilt_speed_value=body.tilt_speed_value,
        )
        payload, status_code = await _invoke(result)
        return JSONResponse(content=payload, status_code=status_code)

    @app.post("/return-base")
    async def return_base() -> JSONResponse:
        connect_error = await _ensure_connected()
        if connect_error is not None:
            payload, status_code = await _invoke(connect_error)
            return JSONResponse(content=payload, status_code=status_code)
        result = await tool_adapter.turntable_return_base()
        payload, status_code = await _invoke(result)
        return JSONResponse(content=payload, status_code=status_code)

    @app.post("/stop")
    async def stop() -> JSONResponse:
        connect_error = await _ensure_connected()
        if connect_error is not None:
            payload, status_code = await _invoke(connect_error)
            return JSONResponse(content=payload, status_code=status_code)
        result = await tool_adapter.turntable_stop()
        payload, status_code = await _invoke(result)
        return JSONResponse(content=payload, status_code=status_code)

    @app.post("/commissioning/first-run")
    async def first_run_commissioning(body: FirstRunCommissioningRequest) -> JSONResponse:
        connect_error = await _ensure_connected()
        if connect_error is not None:
            payload, status_code = await _invoke(connect_error)
            return JSONResponse(content=payload, status_code=status_code)

        report = await run_first_start_commissioning(
            tool_adapter,
            CommissioningOptions(
                max_capability=body.max_capability,
                include_busy_check=body.include_busy_check,
                include_stop_check=body.include_stop_check,
            ),
        )
        status_code = 200 if report.get("ready", False) else 503
        return JSONResponse(content={"ok": report.get("ready", False), "result": report}, status_code=status_code)

    return app


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run turntable FastAPI service.")
    parser.add_argument("--address", required=True, help="BLE address of turntable device.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    app = create_app(address=args.address)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
