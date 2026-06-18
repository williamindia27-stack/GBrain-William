@echo off
setlocal enabledelayedexpansion
set BACKUP_ROOT=C:\brain\backups
set LOG=C:\brain\minions\prune-backups.log
set KEEP_DAYS=7

echo [%date% %time%] Pruning backups older than %KEEP_DAYS% days... >> "%LOG%"

set DELETED=0
for /d %%d in ("%BACKUP_ROOT%\*") do (
    :: Only process folders matching YYYY-MM-DD_* pattern
    set FNAME=%%~nxd
    echo !FNAME! | findstr /r "^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_" > nul 2>&1
    if !errorlevel!==0 (
        :: Check folder age using forfiles
        forfiles /p "%BACKUP_ROOT%" /d -%KEEP_DAYS% /m "%%~nxd" /c "cmd /c echo @path" > nul 2>&1
        if !errorlevel!==0 (
            echo [%date% %time%] Deleting old backup: %%~nxd >> "%LOG%"
            rmdir /s /q "%%d"
            set /a DELETED+=1
        )
    )
)

if !DELETED!==0 (
    echo [%date% %time%] No old backups to prune >> "%LOG%"
) else (
    echo [%date% %time%] Pruned !DELETED! backup(s) >> "%LOG%"
)
endlocal
