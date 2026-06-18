# fix-raw-dumps-trigger.ps1 — runs fix-raw-dumps.bat directly (no job queue)
$ErrorActionPreference = 'Continue'
$LOG       = "C:\brain\minions\fix-raw-dumps.log"
$BAT       = "C:\brain\minions\fix-raw-dumps.bat"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

"[$timestamp] Starting fix-raw-dumps" | Add-Content -Path $LOG

$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$BAT`"" `
    -Wait -PassThru -NoNewWindow

"[$timestamp] fix-raw-dumps exit: $($proc.ExitCode)" | Add-Content -Path $LOG
