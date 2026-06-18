@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set PYTHON=%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PYTHON%" set PYTHON=python
set LOG=C:\brain\minions\graph-extract.log

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
set GBRAIN_POOL_SIZE=2

echo [%date% %time%] graph-extract triggered >> "%LOG%"
"%PYTHON%" "C:\brain\minions\graph-extract.py" %*
if %errorlevel%==0 (
    echo [%date% %time%] graph-extract finished OK >> "%LOG%"
) else (
    echo [%date% %time%] graph-extract FAILED (exit %errorlevel%) >> "%LOG%"
)
endlocal
