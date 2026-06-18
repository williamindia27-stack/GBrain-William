@echo off
setlocal enabledelayedexpansion

set DATA_DIR=C:\brain\papers
set KNOWN=C:\brain\known-papers.txt
set LOG=C:\brain\new-papers-alert.log
set NEW_COUNT=0

echo [%date% %time%] Checking for new papers...

for %%f in ("%DATA_DIR%\*.pdf") do (
    findstr /i /c:"%%~nxf" "%KNOWN%" > nul 2>&1
    if errorlevel 1 (
        echo [%date% %time%] NEW: %%~nxf
        echo [%date% %time%] NEW: %%~nxf >> "%LOG%"
        set /a NEW_COUNT+=1
    )
)

if !NEW_COUNT! EQU 0 (
    echo [%date% %time%] All papers already imported. Nothing new.
    echo [%date% %time%] Checked — 0 new papers. >> "%LOG%"
    goto :done
)
echo [%date% %time%] !NEW_COUNT! new papers found - run gbrain sync to import.
echo [%date% %time%] Found !NEW_COUNT! new paper(s). >> "%LOG%"

:done
endlocal
