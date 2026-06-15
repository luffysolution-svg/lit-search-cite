<#
.SYNOPSIS
    Chinese academic literature search.
    - Wanfang Data API: structured results (API key from config or env var)
    - CNKI / Baidu Scholar / VIP: generates browser URLs for manual lookup
    - Sci-Hub: PDF lookup by DOI

    API keys are read from ~/.lit-search-cite/config.json
    (written by setup.ps1). Env vars are used as fallback for backward compat.

    NOTE: CNKI has bot detection that blocks all non-browser HTTP clients.
    For programmatic CNKI access use Chrome DevTools MCP — tell Claude:
    "帮我在知网搜索「关键词」". This script generates browser-ready URLs.

.PARAMETER Query
    Search query (Chinese or English)

.PARAMETER Source
    wanfang | cnki | baidu | all  (default: all)

.PARAMETER Limit
    Max results per source (default: 10)

.PARAMETER DOI
    If provided, skip search and do Sci-Hub PDF lookup for this DOI.

.EXAMPLE
    .\cnki-search.ps1 -Query "LLM code generation"
    .\cnki-search.ps1 -Query "deep learning" -Source wanfang -Limit 20
    .\cnki-search.ps1 -DOI "10.3969/j.issn.1000-1239.2023.01.001"
#>
param(
    [string]$Query = "",
    [ValidateSet("wanfang","cnki","baidu","all")][string]$Source = "all",
    [int]$Limit = 10,
    [string]$DOI = ""
)

$ErrorActionPreference = "SilentlyContinue"

# ── Load config from ~/.lit-search-cite/config.json ───────────────────────────
$ConfigFile = Join-Path $env:USERPROFILE ".lit-search-cite\config.json"
$Config = [PSCustomObject]@{ api_keys=[PSCustomObject]@{wanfang=""; unpaywall_email=""} }
if (Test-Path $ConfigFile) {
    try { $Config = Get-Content $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json }
    catch { Write-Warning "Could not parse config file: $ConfigFile" }
}

# Resolve keys: config file takes priority over env vars
function Get-Key($configVal, $envVar) {
    if ($configVal -and $configVal.Trim()) { return $configVal.Trim() }
    return [System.Environment]::GetEnvironmentVariable($envVar)
}

$WanfangKey = Get-Key $Config.api_keys.wanfang "WANFANG_API_KEY"

# ── Direct DOI -> Sci-Hub lookup ───────────────────────────────────────────────
if ($DOI) {
    Write-Host "Sci-Hub lookup for DOI: $DOI"
    $fetchScript = Join-Path $PSScriptRoot "pdf-fetch.ps1"
    if (Test-Path $fetchScript) {
        & $fetchScript -DOI $DOI
    } else {
        Write-Host "Sci-Hub URL (open in browser): https://sci-hub.st/$DOI"
        Write-Host "Note: Sci-Hub uses DDoS-Guard — scripts cannot scrape it; use a browser."
    }
    return
}

if (-not $Query) { Write-Error "Provide -Query or -DOI"; exit 1 }

$results = @()
$encoded = [System.Uri]::EscapeDataString($Query)

# ── 1. Wanfang Data API ────────────────────────────────────────────────────────
if ($Source -eq "wanfang" -or $Source -eq "all") {
    if ($WanfangKey) {
        Write-Host "[Wanfang] Searching via API..."
        try {
            $url = "https://openapiquery.wanfangdata.com.cn/periodical/search?apikey=$WanfangKey&query=$encoded&pageSize=$Limit&pageNum=1&lang=zh"
            $r = Invoke-RestMethod $url -TimeoutSec 20
            foreach ($item in $r.Records) {
                $results += [PSCustomObject]@{
                    Title   = $item.Title
                    Authors = ($item.Author -join "; ")
                    Year    = $item.Year
                    Journal = $item.PeriodicalName
                    DOI     = $item.Doi
                    Source  = "Wanfang"
                    Link    = if ($item.Doi) { "https://doi.org/$($item.Doi)" } else { "https://d.wanfangdata.com.cn/periodical/$($item.ObjectId)" }
                }
            }
            Write-Host "[Wanfang] Found $($results.Count) results"
        } catch {
            Write-Warning "[Wanfang] API call failed: $($_.Exception.Message)"
            Write-Host "[Wanfang] Get API key at: https://open.wanfangdata.com.cn/"
        }
    } else {
        Write-Host "[Wanfang] No API key configured."
        Write-Host "[Wanfang] Run .\scripts\setup.ps1 to add your Wanfang API key."
        Write-Host "[Wanfang] Register at: https://open.wanfangdata.com.cn/"
    }
}

# ── 2. CNKI — browser URLs only (bot detection blocks all non-browser access) ──
if ($Source -eq "cnki" -or $Source -eq "all") {
    $cnkiDirect = "https://kns.cnki.net/kns8/defaultresult/index?kw=$encoded&korder=td"
    Write-Host ""
    Write-Host "[CNKI] Bot detection blocks non-browser access. Open one of these manually:"
    Write-Host "  Direct: $cnkiDirect"
    Write-Host "  Tip: For programmatic CNKI search, tell Claude: '帮我在知网搜索「$Query」'"
    Write-Host "       (requires Chrome DevTools MCP — see references/chrome-devtools.md)"
}

# ── 3. Baidu Scholar ───────────────────────────────────────────────────────────
if ($Source -eq "baidu" -or $Source -eq "all") {
    $baiduUrl = "https://xueshu.baidu.com/s?wd=$encoded&rsv_bp=0&tn=SE_baiduxueshu_c1gjeupa&ie=utf-8"
    Write-Host ""
    Write-Host "[Baidu Scholar] Some papers have free PDF links:"
    Write-Host "  $baiduUrl"
}

# ── 4. VIP / Weipu ────────────────────────────────────────────────────────────
if ($Source -eq "all") {
    Write-Host ""
    Write-Host "[VIP/Weipu] https://qikan.cqvip.com/Qikan/Web/Index?from=nsfc&q=$encoded"
}

# ── Output structured results (Wanfang only when API key is set) ───────────────
if ($results.Count -gt 0) {
    Write-Host ""
    Write-Host "=== Results ($($results.Count) papers) ===" -ForegroundColor Cyan
    $i = 1
    foreach ($r in $results) {
        Write-Host ""
        Write-Host "[$i] $($r.Title)"
        Write-Host "    Authors : $($r.Authors)"
        Write-Host "    Year    : $($r.Year)  |  Journal: $($r.Journal)"
        Write-Host "    DOI     : $($r.DOI)"
        Write-Host "    Link    : $($r.Link)"
        if ($r.DOI) {
            Write-Host "    Sci-Hub : https://sci-hub.st/$($r.DOI)  (open in browser)"
        }
        $i++
    }
    return $results
} else {
    Write-Host ""
    Write-Host "No API results. Use the browser URLs above, or:"
    Write-Host "  - Add Wanfang API key: .\scripts\setup.ps1"
    Write-Host "  - Programmatic CNKI:   tell Claude '帮我在知网搜索「$Query」' (Chrome DevTools MCP)"
}
