@echo off
setlocal enabledelayedexpansion
set SRC=%USERPROFILE%\.gbrain
set BACKUP_ROOT=C:\brain\backups

:: Build dated folder name e.g. 2026-05-20_11AM or 2026-05-20_4PM
:: %date% on this system is DD-MM-YYYY
for /f "tokens=1-3 delims=-" %%a in ("%date%") do (
    set DAY=%%a
    set MONTH=%%b
    set YEAR=%%c
)
:: Extract hour from %time% (format HH:MM:SS.ss)
for /f "tokens=1 delims=:" %%h in ("%time%") do set HOUR=%%h
set HOUR=!HOUR: =!
if !HOUR! LSS 12 (
    set AMPM=!HOUR!AM
) else if !HOUR!==12 (
    set AMPM=12PM
) else (
    set /a H12=!HOUR!-12
    set AMPM=!H12!PM
)
set DEST=%BACKUP_ROOT%\%YEAR%-%MONTH%-%DAY%_!AMPM!

echo [%date% %time%] Starting brain backup...
echo [%date% %time%] Source: %SRC%
echo [%date% %time%] Dest:   %DEST%

if not exist "%BACKUP_ROOT%" mkdir "%BACKUP_ROOT%"

robocopy "%SRC%" "%DEST%" /E /NP /NFL /NDL /NJH /NJS > nul 2>&1
if %errorlevel% LEQ 3 (
    echo [%date% %time%] Backup complete: %DEST%
) else (
    echo [%date% %time%] Backup FAILED with code %errorlevel%
    exit /b 1
)

:: Append to log
echo %date% %time% - Backup OK: %DEST% >> "%BACKUP_ROOT%\backup.log"
