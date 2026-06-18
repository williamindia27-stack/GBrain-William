@echo off
setlocal
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set PYTHON=%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PYTHON%" set PYTHON=python

"%PYTHON%" "C:\brain\minions\eval-minions.py" --save %*
