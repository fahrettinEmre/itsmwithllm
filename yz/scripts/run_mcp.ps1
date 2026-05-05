# Repo kokune gecip MCP sunucusunu baslatir (Windows).
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Bulunamadi: $py — once proje kokunde 'python -m venv .venv' ve 'pip install -r requirements.txt' calistirin."
}
& $py -m mcp_server
