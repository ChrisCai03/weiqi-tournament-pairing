$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$demoDirectory = Join-Path $repoRoot "demo-data"
$demoPath = Join-Path $repoRoot "demo-data\launcher-demo.tgo.json"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Program,
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments,
        [Parameter(Mandatory = $true)]
        [string] $FailureMessage
    )

    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code $LASTEXITCODE)."
    }
}

function Find-SupportedPython {
    $versionCheck = "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"

    if (Get-Command "py" -ErrorAction SilentlyContinue) {
        & py "-3.12" "-c" $versionCheck 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Program = "py"; Prefix = @("-3.12") }
        }
    }

    if (Get-Command "python" -ErrorAction SilentlyContinue) {
        & python "-c" $versionCheck 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Program = "python"; Prefix = @() }
        }
    }

    throw "Python 3.12 or newer was not found. Install it from python.org, enable the Python launcher or PATH option, and run this file again."
}

try {
    Set-Location -LiteralPath $repoRoot

    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Host "Creating local Python environment..."
        $python = Find-SupportedPython
        $venvArguments = @($python.Prefix) + @("-m", "venv", $venvPath)
        Invoke-Checked $python.Program $venvArguments "Could not create the local Python environment"
    }

    Write-Host "Installing project dependencies..."
    Invoke-Checked $venvPython @("-m", "pip", "install", "-e", ".[dev]") "Could not install project dependencies"

    if (-not (Test-Path -LiteralPath $demoPath)) {
        Write-Host "Creating demo tournament..."
        New-Item -ItemType Directory -Path $demoDirectory -Force | Out-Null
        Invoke-Checked $venvPython @("-m", "pairing.cli.main", "demo", $demoPath) "Could not create the demo tournament"
    }
    else {
        Write-Host "Reusing demo tournament: $demoPath"
    }

    Write-Host "Starting the tournament server. Press Ctrl+C to stop it."
    Invoke-Checked $venvPython @("-m", "pairing.cli.main", "web", $demoPath, "--open-browser") "The tournament server stopped unexpectedly"
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
