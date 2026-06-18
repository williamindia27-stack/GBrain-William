@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set LOG=C:\brain\minions\embed.log
set NODE_TLS_REJECT_UNAUTHORIZED=0

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v VOYAGE_API_KEY 2^>nul') do set VOYAGE_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v ANTHROPIC_API_KEY 2^>nul') do set ANTHROPIC_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v GROQ_API_KEY 2^>nul') do set GROQ_API_KEY=%%b

echo [%date% %time%] Checking for missing embeddings... >> "%LOG%"

:: Count missing embeddings
for /f "tokens=*" %%l in ('gbrain stats 2^>nul ^| findstr /i "Embedded"') do set STATS=%%l

:: Run embed --stale regardless — gbrain skips if nothing to do
gbrain embed --stale > "%TEMP%\embed_out.txt" 2>&1
set EXIT=%errorlevel%

for /f "tokens=*" %%l in (%TEMP%\embed_out.txt) do (
    echo [%date% %time%] %%l >> "%LOG%"
)

if !EXIT!==0 (
    echo [%date% %time%] Embed complete >> "%LOG%"
) else (
    echo [%date% %time%] Embed FAILED (exit !EXIT!) >> "%LOG%"
)
endlocal
