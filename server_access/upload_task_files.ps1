$ErrorActionPreference = "Stop"
& "$PSScriptRoot\prepare_key.ps1"
$Key=(Resolve-Path (Join-Path $PSScriptRoot "openfoam_eval_shunan.pem")).Path
$Root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Remote="/home/shunan/workspace/Q1_Solitary_Wave_Submerged_Step"
$SshOptions=@("-i",$Key,"-o","IdentitiesOnly=yes","-o","StrictHostKeyChecking=accept-new","-o","ServerAliveInterval=60")
Write-Host "Resetting known benchmark work directories on the server..."
$ResetCommand="set -e; find /home/shunan/workspace -mindepth 1 -maxdepth 1 -type d -name 'Q[0-9]*' -exec rm -rf -- {} +; mkdir -p '$Remote'"
& ssh @SshOptions shunan@118.145.249.220 $ResetCommand
if($LASTEXITCODE -ne 0){ throw "Unable to reset benchmark working directories." }
$Items=@("01_Prompt.md","附件0_服务器连接与运行环境.md","附件1_运行与交付要求.md","附件2_最低数据字段.md","case_parameters.csv","profile_sampling_range.csv","wave_gauge_positions.csv")
foreach($Item in $Items){
  $Path=Join-Path $Root $Item
  if(-not (Test-Path $Path)){ throw "Missing task file: $Path" }
  & scp -i "$Key" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -r "$Path" "shunan@118.145.249.220:$Remote/"
  if($LASTEXITCODE -ne 0){ throw "Upload failed: $Item" }
}
Write-Host "Task files uploaded to $Remote"
