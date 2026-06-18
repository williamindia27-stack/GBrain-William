@echo off
setlocal enabledelayedexpansion
set MINIONS=C:\brain
set LOG=%MINIONS%\clean-logs.log
set KEEP=200

echo [%date% %time%] Cleaning logs (keeping last %KEEP% lines each)...

for %%f in (
    "%MINIONS%\streamlit-status.log"
    "%MINIONS%\new-papers-alert.log"
    "%MINIONS%\embed.log"
    "%MINIONS%\backups\backup.log"
) do (
    if exist %%f (
        :: Count lines
        for /f %%c in ('find /c /v "" %%f 2^>nul') do set COUNT=%%c
        if !COUNT! GTR %KEEP% (
            set /a SKIP=!COUNT!-%KEEP%
            set TMPF=%TEMP%\log_trim.tmp
            more +!SKIP! %%f > "!TMPF!" 2>nul
            copy /y "!TMPF!" %%f > nul
            echo [%date% %time%] Trimmed %%f (!COUNT! ^→ %KEEP% lines) >> "%LOG%"
        ) else (
            echo [%date% %time%] OK %%f (!COUNT! lines, under limit) >> "%LOG%"
        )
    )
)

echo [%date% %time%] Log cleanup done >> "%LOG%"
endlocal
