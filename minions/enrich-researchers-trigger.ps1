# enrich-researchers-trigger.ps1 — runs enrich-researchers.bat directly (no job queue)
$ErrorActionPreference = 'Continue'
$LOG       = "C:\brain\minions\enrich-researchers.log"
$BAT       = "C:\brain\minions\enrich-researchers.bat"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

"[$timestamp] Starting enrich-researchers" | Add-Content -Path $LOG

$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$BAT`"" `
    -Wait -PassThru -NoNewWindow

"[$timestamp] enrich-researchers exit: $($proc.ExitCode)" | Add-Content -Path $LOG
