#!/usr/bin/env bash
set -euo pipefail

ADDRESS="${1:-}"
HOST="${2:-0.0.0.0}"
PORT="${3:-8000}"

if [[ -z "${ADDRESS}" ]]; then
  echo "Usage: bash scripts/run_turntable_host_api.sh <BLE_ADDRESS> [HOST] [PORT]"
  echo "Example: bash scripts/run_turntable_host_api.sh D3:36:39:34:5D:29 0.0.0.0 8000"
  exit 1
fi

echo "Starting host BLE API..."
echo "  Address: ${ADDRESS}"
echo "  Listen:  ${HOST}:${PORT}"
echo
echo "OpenClaw URL:"
echo "  - same Docker host: http://host.docker.internal:${PORT}"
echo "  - from LAN:         http://<your-lan-ip>:${PORT}"
echo

if command -v py >/dev/null 2>&1; then
  py -3 "scripts/turntable_tool_api.py" --address "${ADDRESS}" --host "${HOST}" --port "${PORT}"
elif command -v python3 >/dev/null 2>&1; then
  python3 "scripts/turntable_tool_api.py" --address "${ADDRESS}" --host "${HOST}" --port "${PORT}"
elif command -v python >/dev/null 2>&1; then
  python "scripts/turntable_tool_api.py" --address "${ADDRESS}" --host "${HOST}" --port "${PORT}"
else
  echo "Python interpreter not found (py/python3/python)."
  exit 1
fi
