@echo off
set PATH=%USERPROFILE%\.bun\bin;%PATH%
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v NVIDIA_API_KEY 2^>nul') do set NVIDIA_API_KEY=%%b
set GBRAIN_POOL_SIZE=2
gbrain.cmd agent run --timeout-ms 120000 --detach "You are a brain analyst. Step 1: call list_pages with type=person and limit=5. Step 2: call get_page on the first slug you find. Step 3: call put_page with slug=wiki/agents/research-audit/summary, type=note, title=Research Audit Summary, and compiled_truth set to 2-3 sentences about the researcher bio you read. Stop after step 3." >> "C:\brain\minions\worker-test.log" 2>&1
