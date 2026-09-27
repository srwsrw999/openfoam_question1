param([string]$Destination = (Join-Path (Get-Location) "Q1_Solitary_Wave_Submerged_Step_submission"))
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\prepare_key.ps1"
$Key=(Resolve-Path (Join-Path $PSScriptRoot "openfoam_eval_shunan.pem")).Path
$Remote="/home/shunan/workspace/Q1_Solitary_Wave_Submerged_Step"
$Archive="/tmp/Q1_Solitary_Wave_Submerged_Step_submission.tar.gz"
$PackCommand=@'
set -e
cd '__REMOTE__'
for p in Allrun Allclean case scripts logs outputs; do
  if [ ! -e "$p" ]; then
    echo "Missing submission item: $p" >&2
    exit 2
  fi
done
tar -czf '__ARCHIVE__' Allrun Allclean case scripts logs outputs
'@
$PackCommand=$PackCommand.Replace('__REMOTE__',$Remote).Replace('__ARCHIVE__',$Archive)
& ssh -i "$Key" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new shunan@118.145.249.220 $PackCommand
if($LASTEXITCODE -ne 0){ throw "Remote submission verification or packaging failed." }
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
$LocalArchive=Join-Path $Destination "submission.tar.gz"
& scp -i "$Key" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new "shunan@118.145.249.220:$Archive" "$LocalArchive"
if($LASTEXITCODE -ne 0){ throw "Submission download failed." }
& tar -xzf "$LocalArchive" -C "$Destination"
if($LASTEXITCODE -ne 0){ throw "Submission extraction failed." }
Remove-Item "$LocalArchive" -Force
& ssh -i "$Key" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new shunan@118.145.249.220 "rm -f '$Archive'"
Write-Host "Submission downloaded and verified: $Destination"
