# auto-import-trigger.ps1 — runs auto-import.bat directly (no job queue)
$ErrorActionPreference = 'Continue'
$LOG       = "C:\brain\minions\auto-import.log"
$BAT       = "C:\brain\minions\auto-import.bat"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

"[$timestamp] Starting auto-import" | Add-Content -Path $LOG

$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$BAT`"" `
    -Wait -PassThru -NoNewWindow

"[$timestamp] auto-import exit: $($proc.ExitCode)" | Add-Content -Path $LOG
