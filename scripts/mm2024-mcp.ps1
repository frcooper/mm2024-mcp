param(
    [string]$Workspace = (Resolve-Path -Path "$PSScriptRoot/..").Path
)

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    & $uv.Path "--directory" $Workspace "run" "mm2024-mcp"
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Neither uv nor python is available on PATH. Install uv or Python 3.11+."
    exit 127
}

& $python.Path "-m" "mm2024_mcp.server"
exit $LASTEXITCODE
