# research-notes-trigger.ps1 — runs research-notes.bat directly (no job queue)
$ErrorActionPreference = 'Continue'
$LOG       = "C:\brain\minions\research-notes.log"
$BAT       = "C:\brain\minions\research-notes.bat"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

"[$timestamp] Starting research-notes" | Add-Content -Path $LOG

$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$BAT`"" `
    -Wait -PassThru -NoNewWindow

"[$timestamp] research-notes exit: $($proc.ExitCode)" | Add-Content -Path $LOG
