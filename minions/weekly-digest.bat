@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set PYTHON=%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PYTHON%" set PYTHON=python
set LOG=C:\brain\minions\weekly-digest.log
set NODE_TLS_REJECT_UNAUTHORIZED=0

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v GROQ_API_KEY 2^>nul') do set GROQ_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v VOYAGE_API_KEY 2^>nul') do set VOYAGE_API_KEY=%%b

if "%GROQ_API_KEY%"=="" (
    echo [%date% %time%] ERROR: GROQ_API_KEY not found in registry >> "%LOG%"
    exit /b 1
)

echo [%date% %time%] Launching weekly-digest.py >> "%LOG%"
"%PYTHON%" "C:\brain\minions\weekly-digest.py"
if %errorlevel%==0 (
    echo [%date% %time%] Weekly digest complete >> "%LOG%"
) else (
    echo [%date% %time%] Weekly digest FAILED (exit %errorlevel%) >> "%LOG%"
)
endlocal
