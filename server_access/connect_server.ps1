$ErrorActionPreference = "Stop"
& "$PSScriptRoot\prepare_key.ps1"
$Key=(Resolve-Path (Join-Path $PSScriptRoot "openfoam_eval_shunan.pem")).Path
ssh -i "$Key" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=60 -p 22 -t shunan@118.145.249.220 "mkdir -p '/home/shunan/workspace/Q1_Solitary_Wave_Submerged_Step'; cd '/home/shunan/workspace/Q1_Solitary_Wave_Submerged_Step'; exec bash -l"
