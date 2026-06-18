@echo off
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set DATABASE_URL=postgresql://neondb_owner:npg_cO9WxgPaS6fC@ep-silent-mountain-ajas5md1.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require
set ANTHROPIC_API_KEY=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
set GBRAIN_POOL_SIZE=2
set GBRAIN_ALLOW_SHELL_JOBS=1
echo [%date% %time%] Worker starting >> "C:\brain\minions\worker-test.log"
gbrain.cmd jobs work >> "C:\brain\minions\worker-test.log" 2>&1
echo [%date% %time%] Worker exited with code %errorlevel% >> "C:\brain\minions\worker-test.log"
