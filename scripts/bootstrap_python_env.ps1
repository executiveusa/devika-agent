param(
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

function Test-PythonCandidate {
    param(
        [string]$Exe,
        [string[]]$Args
    )

    try {
        $null = & $Exe @Args --version 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-PythonCommand {
    if (Test-PythonCandidate -Exe "python" -Args @()) {
        return @{ Exe = "python"; Args = @() }
    }
    if (Test-PythonCandidate -Exe "py" -Args @("-3")) {
        return @{ Exe = "py"; Args = @("-3") }
    }
    return $null
}

Write-Host "[bootstrap] Starting Python environment bootstrap..."

$pyCmd = Get-PythonCommand
if ($null -eq $pyCmd) {
    Write-Error "Python not found. Install Python 3.10+ or enable the Python launcher (py)."
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "[bootstrap] Creating virtual environment at $venvPath"
    & $pyCmd.Exe @($pyCmd.Args + @("-m", "venv", $venvPath))
} else {
    Write-Host "[bootstrap] Reusing existing virtual environment at $venvPath"
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment Python not found at $venvPython"
}

Write-Host "[bootstrap] Upgrading pip"
& $venvPython -m pip install --upgrade pip

$requirements = Join-Path $repoRoot "requirements.txt"
if (Test-Path $requirements) {
    Write-Host "[bootstrap] Installing requirements"
    & $venvPython -m pip install -r $requirements
} else {
    Write-Host "[bootstrap] requirements.txt not found; skipping dependency install"
}

if ($RunTests) {
    Write-Host "[bootstrap] Running tests"
    & $venvPython -m pytest -q
}

Write-Host "[bootstrap] Completed. Use: .venv\Scripts\python.exe"
