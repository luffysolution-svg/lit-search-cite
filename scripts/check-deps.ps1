<#
.SYNOPSIS
    lit-search-cite: dependency and configuration checker.

    Run this after first-time setup to verify everything is installed and configured.
    Checks Python, Node.js, uv, MCP config (ai4scholar + scansci-pdf + chrome-devtools),
    API keys, Chrome DevTools reachability, and scansci-pdf cookie files.

.EXAMPLE
    .\scripts\check-deps.ps1
#>

$ConfigFile  = Join-Path $env:USERPROFILE ".lit-search-cite\config.json"
$McpFile     = Join-Path $env:USERPROFILE ".claude\mcp.json"
$ScansciDir  = Join-Path $env:USERPROFILE ".scansci-pdf"

$ok    = @()
$warn  = @()
$errors = @()

function Check($label, $pass, $msg, $fix) {
    if ($pass) {
        $script:ok += "  [OK]   $label"
    } elseif ($fix) {
        $script:warn += "  [WARN] $label --$msg`n         Fix: $fix"
    } else {
        $script:errors +="  [FAIL] $label --$msg"
    }
}

Write-Host ""
Write-Host "=== lit-search-cite: Dependency & Config Check ===" -ForegroundColor Cyan
Write-Host ""

# ── 1. Python ─────────────────────────────────────────────────────────────────
$pyVer = $null
try {
    $pyVer = (python --version 2>&1) -replace 'Python ',''
    $pyMajor = [int]($pyVer.Split('.')[0])
    $pyMinor = [int]($pyVer.Split('.')[1])
    Check "Python $pyVer" ($pyMajor -ge 3 -and $pyMinor -ge 10) `
        "Python 3.10+ required (found $pyVer)" `
        "winget install Python.Python.3.11"
} catch {
    Check "Python" $false "not found" "winget install Python.Python.3.11"
}

# ── 2. Node.js / npx ─────────────────────────────────────────────────────────
$nodeVer = $null
try {
    $nodeVer = (node --version 2>&1) -replace 'v',''
    $nodeMajor = [int]($nodeVer.Split('.')[0])
    Check "Node.js v$nodeVer" ($nodeMajor -ge 18) `
        "Node.js 18+ required (found v$nodeVer)" `
        "winget install OpenJS.NodeJS"
} catch {
    Check "Node.js" $false "not found (required for ai4scholar MCP)" `
        "winget install OpenJS.NodeJS"
}

# ── 3. uv ─────────────────────────────────────────────────────────────────────
$uvOk = $false
try { $uvOk = ((uvx --version 2>&1) -match '\d+\.\d+') } catch {}
Check "uv / uvx" $uvOk "not found (required for scansci-pdf MCP)" `
    "pip install uv  OR  winget install astral-sh.uv"

# ── 4. mcp.json ───────────────────────────────────────────────────────────────
$mcpJson = $null
$ai4scholarInMcp   = $false
$scansciInMcp      = $false
$chromeDevtoolsInMcp = $false
if (Test-Path $McpFile) {
    try {
        $mcpJson = Get-Content $McpFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $servers = $mcpJson.mcpServers
        $ai4scholarInMcp     = $null -ne $servers.ai4scholar
        $scansciInMcp        = $null -ne $servers.'scansci-pdf'
        $chromeDevtoolsInMcp = $null -ne $servers.'chrome-devtools'
    } catch {
        Check "mcp.json parse" $false "JSON parse error in $McpFile" "Fix JSON syntax errors"
    }
} else {
    Check "mcp.json" $false "not found at $McpFile" `
        "Create $McpFile --see references/mcp-template.md"
}
Check "ai4scholar MCP entry in mcp.json" $ai4scholarInMcp `
    "missing" "Add ai4scholar server block to $McpFile then restart Claude Code"
Check "scansci-pdf MCP entry in mcp.json" $scansciInMcp `
    "missing" "Add scansci-pdf server block to $McpFile then restart Claude Code"

# chrome-devtools is optional --WARN only
if ($chromeDevtoolsInMcp) {
    $ok += "  [OK]   chrome-devtools MCP entry in mcp.json (paywall fallback enabled)"
} else {
    $warn += "  [WARN] chrome-devtools MCP entry in mcp.json --not configured (optional)`n         Fix: Add chrome-devtools block to $McpFile --see references/chrome-devtools.md"
}

# ── 5. ai4scholar API key ─────────────────────────────────────────────────────
$ai4Key = ""
if ($ai4scholarInMcp -and $mcpJson.mcpServers.ai4scholar.env) {
    $ai4Key = $mcpJson.mcpServers.ai4scholar.env.AI4SCHOLAR_API_KEY
}
if (-not $ai4Key) {
    $ai4Key = [System.Environment]::GetEnvironmentVariable("AI4SCHOLAR_API_KEY")
}
if (-not $ai4Key) {
    try {
        $cfg = Get-Content $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $ai4Key = $cfg.api_keys.ai4scholar
    } catch {}
}
Check "AI4SCHOLAR_API_KEY set" ($ai4Key -and $ai4Key.StartsWith("sk-")) `
    "not set or wrong format" `
    "Get key at https://ai4scholar.net ->Dashboard ->Open Platform; add to mcp.json env block"

# ── 6. Config file ────────────────────────────────────────────────────────────
$cfgOk = Test-Path $ConfigFile
Check "Config file (~/.lit-search-cite/config.json)" $cfgOk `
    "not found" "Run: .\scripts\setup.ps1"

$cfg = $null
if ($cfgOk) {
    try { $cfg = Get-Content $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json } catch {}
}

# ── 7. Unpaywall email ────────────────────────────────────────────────────────
$upEmail = ""
if ($cfg) { $upEmail = $cfg.api_keys.unpaywall_email }
if (-not $upEmail) { $upEmail = [System.Environment]::GetEnvironmentVariable("UNPAYWALL_EMAIL") }
Check "UNPAYWALL_EMAIL set" ($upEmail -and $upEmail -match '@') `
    "not set (PDF discovery via Unpaywall disabled)" `
    "Run .\scripts\setup.ps1 and enter any valid email (required by Unpaywall ToS)"

# ── 8. Chrome DevTools reachability (optional) ────────────────────────────────
$cdpUrl = "http://localhost:9222"
if ($chromeDevtoolsInMcp -and $mcpJson.mcpServers.'chrome-devtools'.env.CDP_URL) {
    $cdpUrl = $mcpJson.mcpServers.'chrome-devtools'.env.CDP_URL
}
$chromeReachable = $false
try {
    $r = Invoke-WebRequest "$cdpUrl/json" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    $chromeReachable = $r.StatusCode -eq 200
} catch {}
if ($chromeDevtoolsInMcp) {
    Check "Chrome reachable at $cdpUrl" $chromeReachable `
        "Chrome not running with remote debugging" `
        "Start Chrome with: chrome.exe --remote-debugging-port=9222"
} else {
    if ($chromeReachable) {
        $ok += "  [OK]   Chrome detected at $cdpUrl (not in mcp.json yet)"
    }
    # else: skip --chrome-devtools not configured, no point checking
}

# ── 9. scansci-pdf data dir ───────────────────────────────────────────────────
$scansciCookies = Test-Path $ScansciDir
Check "scansci-pdf data dir (~/.scansci-pdf/)" $scansciCookies `
    "not found --publisher cookies not yet configured" `
    "Tell Claude: 'set up scansci-pdf browser cookies for ScienceDirect'"

# ── 10. Wanfang key (optional) ────────────────────────────────────────────────
$wfKey = ""
if ($cfg) { $wfKey = $cfg.api_keys.wanfang }
if (-not $wfKey) { $wfKey = [System.Environment]::GetEnvironmentVariable("WANFANG_API_KEY") }
if (-not $wfKey) {
    $warn += "  [WARN] WANFANG_API_KEY not set --Chinese Wanfang API results unavailable`n         Fix: Register at https://open.wanfangdata.com.cn/ then run .\scripts\setup.ps1"
} else {
    $ok += "  [OK]   WANFANG_API_KEY set"
}

# ── Output ────────────────────────────────────────────────────────────────────
Write-Host "PASSED ($($ok.Count)):" -ForegroundColor Green
$ok | ForEach-Object { Write-Host $_ -ForegroundColor Green }

if ($warn.Count -gt 0) {
    Write-Host ""
    Write-Host "WARNINGS ($($warn.Count)):" -ForegroundColor Yellow
    $warn | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
}

if ($errors.Count -gt 0) {
    Write-Host ""
    Write-Host "FAILED ($($errors.Count)):" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
}

Write-Host ""
if ($errors.Count -eq 0 -and $warn.Count -le 2) {
    Write-Host "Status: READY --all critical components configured." -ForegroundColor Green
} elseif ($errors.Count -eq 0) {
    Write-Host "Status: PARTIAL --some optional components not configured (see warnings)." -ForegroundColor Yellow
} else {
    Write-Host "Status: NOT READY --fix FAILED items before using this skill." -ForegroundColor Red
}
Write-Host ""
Write-Host "Full setup guide:        references/setup-guide.md" -ForegroundColor DarkGray
Write-Host "MCP config template:     references/mcp-template.md" -ForegroundColor DarkGray
Write-Host "Quick config:            .\scripts\setup.ps1" -ForegroundColor DarkGray
Write-Host "Chrome DevTools MCP:     references/chrome-devtools.md" -ForegroundColor DarkGray
Write-Host ""
