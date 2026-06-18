@echo off
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set DATABASE_URL=postgresql://neondb_owner:npg_cO9WxgPaS6fC@ep-silent-mountain-ajas5md1.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require
set ANTHROPIC_API_KEY=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
set GBRAIN_POOL_SIZE=2
gbrain.cmd agent run --timeout-ms 120000 --detach "You are a brain analyst. Step 1: call list_pages with type=person and limit=5. Step 2: call get_page on the first slug you find. Step 3: call put_page with slug=wiki/agents/research-audit/summary, type=note, title=Research Audit Summary, and compiled_truth set to 2-3 sentences about the researcher bio you read. Stop after step 3." >> "C:\brain\minions\worker-test.log" 2>&1
