param([string]$KeyPath = (Join-Path $PSScriptRoot "openfoam_eval_shunan.pem"))
$ErrorActionPreference = "Stop"
$Key=(Resolve-Path $KeyPath).Path
icacls.exe $Key /inheritance:r | Out-Null
icacls.exe $Key /grant:r "${env:USERNAME}:(R)" | Out-Null
Write-Host "SSH key permissions prepared: $Key"
