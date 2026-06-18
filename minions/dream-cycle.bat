@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set LOG=C:\brain\minions\dream-cycle.log
set GBRAIN=%USERPROFILE%\.bun\bin\gbrain.cmd

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
set GBRAIN_POOL_SIZE=2

echo. >> "%LOG%"
echo [%date% %time%] ======= Dream Cycle started ======= >> "%LOG%"

echo [%date% %time%] Phase: extract (links + timeline) >> "%LOG%"
"%GBRAIN%" extract all --source db >> "%LOG%" 2>&1
if %errorlevel% neq 0 echo [%date% %time%] WARNING: extract had errors >> "%LOG%"

echo [%date% %time%] Phase: embed (stale chunks) >> "%LOG%"
"%GBRAIN%" embed --stale >> "%LOG%" 2>&1
if %errorlevel% neq 0 echo [%date% %time%] WARNING: embed had errors >> "%LOG%"

echo [%date% %time%] Phase: backlinks >> "%LOG%"
"%GBRAIN%" backlinks >> "%LOG%" 2>&1
if %errorlevel% neq 0 echo [%date% %time%] WARNING: backlinks had errors >> "%LOG%"

echo [%date% %time%] Phase: lint >> "%LOG%"
"%GBRAIN%" lint >> "%LOG%" 2>&1
if %errorlevel% neq 0 echo [%date% %time%] WARNING: lint had errors >> "%LOG%"

echo [%date% %time%] Phase: orphans >> "%LOG%"
"%GBRAIN%" orphans >> "%LOG%" 2>&1
if %errorlevel% neq 0 echo [%date% %time%] WARNING: orphans had errors >> "%LOG%"

echo [%date% %time%] ======= Dream Cycle finished OK ======= >> "%LOG%"
endlocal
