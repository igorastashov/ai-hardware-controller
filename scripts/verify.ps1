[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$verifySh = Join-Path $PSScriptRoot "verify.sh"

if (-not (Test-Path $verifySh)) {
    Write-Error "verify.sh not found at: $verifySh"
    exit 1
}

function Get-BashExecutable {
    if ($env:VERIFY_BASH -and (Test-Path $env:VERIFY_BASH)) {
        return $env:VERIFY_BASH
    }

    $candidates = @(
        "C:\Program Files\Git\bin\bash.exe",
        "C:\Program Files (x86)\Git\bin\bash.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $bashCmd = Get-Command bash -ErrorAction SilentlyContinue
    if ($bashCmd) {
        return $bashCmd.Source
    }

    return $null
}

$bashExe = Get-BashExecutable
if (-not $bashExe) {
    Write-Error "No usable bash executable found. Install Git Bash or set VERIFY_BASH."
    exit 1
}

Push-Location $repoRoot
try {
    & $bashExe "scripts/verify.sh"
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
