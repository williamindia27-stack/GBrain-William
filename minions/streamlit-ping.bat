@echo off
set LOG=C:\brain\minions\streamlit-status.log
set PORT=8501

curl -s -o nul -w "%%{http_code}" --connect-timeout 3 http://localhost:%PORT%/ > "%TEMP%\st_code.txt" 2>nul
for /f %%i in (%TEMP%\st_code.txt) do set HTTP_CODE=%%i

if "%HTTP_CODE%"=="200" (
    echo [%date% %time%] OK   http://localhost:%PORT%
    echo [%date% %time%] OK   http://localhost:%PORT% >> "%LOG%"
    goto :done
)

echo [%date% %time%] DOWN - restarting gbrain_app.py...
echo [%date% %time%] DOWN - restarting >> "%LOG%"

taskkill /f /im streamlit.exe > nul 2>&1
taskkill /f /im python.exe > nul 2>&1

wscript //nologo "C:\brain\minions\start-streamlit.vbs"

:: Wait 15 seconds using ping trick (no stdin needed)
ping -n 16 127.0.0.1 > nul

curl -s -o nul -w "%%{http_code}" --connect-timeout 5 http://localhost:%PORT%/ > "%TEMP%\st_code2.txt" 2>nul
for /f %%i in (%TEMP%\st_code2.txt) do set NEW_CODE=%%i

if "%NEW_CODE%"=="200" (
    echo [%date% %time%] RESTARTED OK - app back on port %PORT%
    echo [%date% %time%] RESTARTED OK >> "%LOG%"
) else (
    echo [%date% %time%] RESTART FAILED - manual check needed
    echo [%date% %time%] RESTART FAILED >> "%LOG%"
)

:done
