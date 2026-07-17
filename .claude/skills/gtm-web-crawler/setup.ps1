param(
    [string]$Python = $env:CRAWLER_PYTHON
)

$ErrorActionPreference = "Stop"
$Dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $Dir ".venv-win"

if (-not $Python) {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command) {
        $Python = $command.Source
    } else {
        $bundled = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
        if (Test-Path -LiteralPath $bundled) {
            $Python = $bundled
        }
    }
}
if (-not $Python -or -not (Test-Path -LiteralPath $Python)) {
    throw "No encontré Python. Define CRAWLER_PYTHON con la ruta a python.exe."
}

if (-not (Test-Path -LiteralPath (Join-Path $Venv "Scripts\python.exe"))) {
    & $Python -m venv $Venv
}
$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1"
& (Join-Path $Venv "Scripts\python.exe") -m pip install --progress-bar off -r (Join-Path $Dir "requirements-crawler.txt")
& (Join-Path $Venv "Scripts\python.exe") -m pip check
Write-Output "OK: $Venv"
