#!/usr/bin/env bash
set -euo pipefail

git add -A
git commit -m "$(cat <<'EOF'
step: finalize turntable discovery and tool adapter MVP [turntable-discovery-profile step16]

Capture BLE discovery/protocol artifacts, add single-flight runtime and tool adapter contract, and document Product DoD plus smoke harness to keep long-running agent work stable and verifiable.
EOF
)"
git status --short
