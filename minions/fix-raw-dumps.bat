@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set PYTHON=%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PYTHON%" set PYTHON=python
set LOG=C:\brain\minions\fix-raw-dumps.log

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v GROQ_API_KEY 2^>nul') do set GROQ_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
set GBRAIN_POOL_SIZE=2

echo [%date% %time%] fix-raw-dumps triggered >> "%LOG%"
"%PYTHON%" "C:\brain\minions\fix-raw-dumps.py"
if %errorlevel%==0 (
    echo [%date% %time%] fix-raw-dumps finished OK >> "%LOG%"
) else (
    echo [%date% %time%] fix-raw-dumps FAILED (exit %errorlevel%) >> "%LOG%"
)
endlocal
