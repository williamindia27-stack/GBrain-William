# backup-trigger.ps1 — runs backup-brain.bat directly (no job queue)
$ErrorActionPreference = 'Continue'
$LOG       = "C:\brain\backup.log"
$BAT       = "C:\brain\minions\backup-brain.bat"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

"[$timestamp] Starting backup" | Add-Content -Path $LOG

$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$BAT`"" `
    -Wait -PassThru -NoNewWindow

"[$timestamp] backup exit: $($proc.ExitCode)" | Add-Content -Path $LOG
