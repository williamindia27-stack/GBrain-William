# setup-scheduled-tasks.ps1
# Run this once as Administrator to register all GBrain scheduled tasks.
# Usage: Right-click this file -> "Run with PowerShell" (as Administrator)

$MINIONS = "C:\brain\minions"

function Register-GBrainTask {
    param($Name, $Script, $TriggerArgs)
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -NonInteractive -WindowStyle Hidden -File `"$MINIONS\$Script`""
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd
    if (Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $Name -Confirm:$false
    }
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $TriggerArgs -Settings $settings -RunLevel Highest -Force | Out-Null
    Write-Host "Registered: $Name"
}

# ── Paper Pipeline ─────────────────────────────────────────────────────────────
Register-GBrainTask "GBrain-PapersWatcher"     "papers-watcher.ps1"            (New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date))
Register-GBrainTask "GBrain-AutoImport"        "auto-import-trigger.ps1"       (New-ScheduledTaskTrigger -Daily -At "11:20AM")
Register-GBrainTask "GBrain-FixRawDumps"       "fix-raw-dumps-trigger.ps1"     (New-ScheduledTaskTrigger -Daily -At "11:40AM")
Register-GBrainTask "GBrain-AutoEmbed"         "embed-stale-trigger.ps1"       (New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date))
Register-GBrainTask "GBrain-ResearchGraph"     "build-research-graph-trigger.ps1" (New-ScheduledTaskTrigger -Daily -At "1:45PM")
Register-GBrainTask "GBrain-EnrichResearchers" "enrich-researchers-trigger.ps1"(New-ScheduledTaskTrigger -Daily -At "2:15PM")
Register-GBrainTask "GBrain-ResearchNotes"     "research-notes-trigger.ps1"    (New-ScheduledTaskTrigger -Daily -At "2:30PM")

# ── Intelligence ───────────────────────────────────────────────────────────────
Register-GBrainTask "GBrain-DailyBrief"        "daily-brief.bat"               (New-ScheduledTaskTrigger -Daily -At "9:30AM")
Register-GBrainTask "GBrain-WeeklyDigest"      "weekly-digest.bat"             (New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Friday -At "3:00PM")
Register-GBrainTask "GBrain-DailySynthesis"    "subagent-daily-synthesis.bat"  (New-ScheduledTaskTrigger -Daily -At "3:00PM")

# ── Maintenance ────────────────────────────────────────────────────────────────
Register-GBrainTask "GBrain-BrainBackup"       "backup-brain.bat"              (New-ScheduledTaskTrigger -Daily -At "11:00AM")
Register-GBrainTask "GBrain-BrainBackup4PM"    "backup-brain.bat"              (New-ScheduledTaskTrigger -Daily -At "4:00PM")
Register-GBrainTask "GBrain-CleanLogs"         "clean-logs.bat"                (New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Wednesday -At "11:00AM")
Register-GBrainTask "GBrain-PruneBackups"      "prune-backups.bat"             (New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Wednesday -At "11:00AM")
Register-GBrainTask "GBrain-StreamlitPing"     "streamlit-ping.bat"            (New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 1) -Once -At (Get-Date))

Write-Host "`nAll tasks registered. Run 'Get-ScheduledTask | Where-Object TaskName -like GBrain*' to verify."
