# embed-stale-trigger.ps1 — runs embed-stale.bat directly (no job queue)
$ErrorActionPreference = 'Continue'
$LOG       = "C:\brain\minions\embed-stale.log"
$BAT       = "C:\brain\minions\embed-stale.bat"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

"[$timestamp] Starting embed-stale" | Add-Content -Path $LOG

$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$BAT`"" `
    -Wait -PassThru -NoNewWindow

"[$timestamp] embed-stale exit: $($proc.ExitCode)" | Add-Content -Path $LOG
