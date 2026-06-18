@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set PYTHON=%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PYTHON%" set PYTHON=python
set LOG=C:\brain\minions\bio-agent.log

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v ANTHROPIC_API_KEY 2^>nul') do set ANTHROPIC_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
set GBRAIN_POOL_SIZE=2

echo [%date% %time%] bio-agent triggered >> "%LOG%"
"%PYTHON%" "C:\brain\minions\bio-agent.py" %*
if %errorlevel%==0 (
    echo [%date% %time%] bio-agent finished OK >> "%LOG%"
) else (
    echo [%date% %time%] bio-agent FAILED (exit %errorlevel%) >> "%LOG%"
)
endlocal
