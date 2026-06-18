# papers-watcher.ps1
# Runs every 5 minutes via scheduled task.
# Detects new PDFs in C:\brain\papers and immediately triggers:
#   1. auto-import  (Groq summary + gbrain import job)
#   2. gbrain extract all  (wire links — zero LLM calls)
# This closes the Step 2 + Step 6 gap in the Signal Lifecycle.

$ErrorActionPreference = 'Continue'
$LOG        = "C:\brain\minions\papers-watcher.log"
$PAPERS_DIR = "C:\brain\papers"
$KNOWN_FILE = "C:\brain\known-import-pdfs.txt"
$IMPORT_BAT = "C:\brain\minions\auto-import.bat"
$GBRAIN     = "$env:USERPROFILE\.bun\bin\gbrain.cmd"
$dbUrl      = (Get-ItemProperty 'HKCU:\Environment' -Name DATABASE_URL -ErrorAction SilentlyContinue).DATABASE_URL
$timestamp  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Papers folder must exist
if (-not (Test-Path $PAPERS_DIR)) { exit 0 }

# Load the set of PDFs auto-import already knows about
$known = @()
if (Test-Path $KNOWN_FILE) {
    $known = Get-Content $KNOWN_FILE -ErrorAction SilentlyContinue |
             Where-Object { $_.Trim() -ne "" }
}

# Find PDFs and images not yet in the known list
$pdfs    = Get-ChildItem -Path $PAPERS_DIR -Include "*.pdf","*.jpg","*.jpeg","*.png","*.webp" -ErrorAction SilentlyContinue
$newPdfs = @($pdfs | Where-Object { $known -notcontains $_.Name })

if ($newPdfs.Count -eq 0) { exit 0 }

"[$timestamp] ▶ $($newPdfs.Count) new PDF(s) detected: $(($newPdfs | Select-Object -ExpandProperty Name) -join ', ')" |
    Add-Content -Path $LOG

# ── Step 1: auto-import (Groq + gbrain import job) ──────────────────────────
"[$timestamp] Running auto-import..." | Add-Content -Path $LOG

$env:DATABASE_URL     = $dbUrl
$env:GBRAIN_POOL_SIZE = "2"
$env:PATH             = "$env:USERPROFILE\.bun\bin;$env:PATH"

$import_proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$IMPORT_BAT`"" `
    -Wait -PassThru -NoNewWindow

"[$timestamp] auto-import exit: $($import_proc.ExitCode)" | Add-Content -Path $LOG

# ── Step 2: gbrain extract — wire wikilinks into graph (zero LLM calls) ─────
"[$timestamp] Wiring links (gbrain extract all)..." | Add-Content -Path $LOG

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName  = $GBRAIN
$psi.Arguments = "extract all --source db"
$psi.UseShellExecute        = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError  = $true
$psi.EnvironmentVariables["PATH"]             = "$env:USERPROFILE\.bun\bin;$env:PATH"
$psi.EnvironmentVariables["DATABASE_URL"]     = $dbUrl
$psi.EnvironmentVariables["GBRAIN_POOL_SIZE"] = "2"

$ep = [System.Diagnostics.Process]::Start($psi)
$ep.WaitForExit()

"[$timestamp] gbrain extract done (exit $($ep.ExitCode))" | Add-Content -Path $LOG
"[$timestamp] ✅ Pipeline complete for $($newPdfs.Count) new paper(s)" | Add-Content -Path $LOG
