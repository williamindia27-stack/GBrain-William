# arxiv-download-trigger.ps1 — runs arxiv-download.bat directly (no job queue)
# Task Scheduler calls this daily at 11:00 AM

$ErrorActionPreference = 'Continue'
$LOG       = "C:\brain\minions\arxiv-download-trigger.log"
$BAT       = "C:\brain\minions\arxiv-download.bat"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

"[$timestamp] Starting arxiv-download" | Add-Content -Path $LOG

$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$BAT`"" `
    -Wait -PassThru -NoNewWindow

"[$timestamp] arxiv-download exit: $($proc.ExitCode)" | Add-Content -Path $LOG
