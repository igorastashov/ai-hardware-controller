[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Address,

    [string]$Host = "0.0.0.0",

    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

Write-Host "Starting host BLE API..."
Write-Host "  Address: $Address"
Write-Host "  Listen:  $Host`:$Port"
Write-Host ""
Write-Host "Use for OpenClaw:"
Write-Host "  - same Docker host: http://host.docker.internal:$Port"
Write-Host "  - another machine in LAN: http://<your-lan-ip>:$Port"
Write-Host ""

py -3 "scripts/turntable_tool_api.py" --address $Address --host $Host --port $Port
