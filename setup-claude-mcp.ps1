# setup-claude-mcp.ps1
# Connects Claude Desktop to GBrain by patching claude_desktop_config.json

$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"
$gbrainExe  = "$env:USERPROFILE\.bun\bin\gbrain.exe"

# Check gbrain is installed
if (-not (Test-Path $gbrainExe)) {
    Write-Host "ERROR: gbrain.exe not found at $gbrainExe" -ForegroundColor Red
    Write-Host "Make sure gbrain is installed (bun install -g github:garrytan/gbrain)" -ForegroundColor Yellow
    exit 1
}

# Create Claude config folder if it doesn't exist
$configDir = Split-Path $configPath
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null
}

# Load existing config or start fresh
if (Test-Path $configPath) {
    $raw    = Get-Content $configPath -Raw -Encoding UTF8
    $config = $raw | ConvertFrom-Json
} else {
    $config = [PSCustomObject]@{}
}

# Ensure mcpServers property exists
if (-not $config.PSObject.Properties['mcpServers']) {
    $config | Add-Member -MemberType NoteProperty -Name 'mcpServers' -Value ([PSCustomObject]@{})
}

# Add or overwrite gbrain entry
$gbrainEntry = [PSCustomObject]@{
    command = $gbrainExe.Replace('\', '\\')
    args    = @('serve')
    env     = [PSCustomObject]@{ NODE_TLS_REJECT_UNAUTHORIZED = '0' }
}
if ($config.mcpServers.PSObject.Properties['gbrain']) {
    $config.mcpServers.gbrain = $gbrainEntry
} else {
    $config.mcpServers | Add-Member -MemberType NoteProperty -Name 'gbrain' -Value $gbrainEntry
}

# Save
$config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8

Write-Host ""
Write-Host "Done! GBrain added to Claude Desktop." -ForegroundColor Green
Write-Host "Config saved to: $configPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "-> Restart Claude Desktop to activate." -ForegroundColor Yellow
Write-Host ""
