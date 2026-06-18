# build-research-graph-trigger.ps1 — runs build-research-graph.bat directly (no job queue)
$ErrorActionPreference = 'Continue'
$LOG       = "C:\brain\minions\build-research-graph.log"
$BAT       = "C:\brain\minions\build-research-graph.bat"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

"[$timestamp] Starting build-research-graph" | Add-Content -Path $LOG

$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$BAT`"" `
    -Wait -PassThru -NoNewWindow

"[$timestamp] build-research-graph exit: $($proc.ExitCode)" | Add-Content -Path $LOG
