<#
.SYNOPSIS
    lit-search-cite: API key setup wizard.

    Stores all API keys to ~/.lit-search-cite/config.json
    for permanent reuse across sessions. All scripts read from this file
    automatically — you only need to run setup once.

.DESCRIPTION
    Run with no flags for interactive setup.
    Use -Show to view current configuration (keys are masked).
    Use -Reset to clear all keys and start fresh.

.PARAMETER Show
    Display current configuration with masked key values.

.PARAMETER Reset
    Clear all API keys. Prompts for confirmation.

.EXAMPLE
    .\setup.ps1
    .\setup.ps1 -Show
    .\setup.ps1 -Reset
#>
param(
    [switch]$Show,
    [switch]$Reset
)

$ConfigDir  = Join-Path $env:USERPROFILE ".lit-search-cite"
$ConfigFile = Join-Path $ConfigDir "config.json"

# ── Helpers ────────────────────────────────────────────────────────────────────
function Get-Config {
    if (Test-Path $ConfigFile) {
        try { return Get-Content $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json }
        catch {}
    }
    return [PSCustomObject]@{
        api_keys = [PSCustomObject]@{
            ai4scholar       = ""
            wanfang          = ""
            unpaywall_email  = ""
            onescholar       = ""
            semantic_scholar = ""
            elsevier         = ""
            springer         = ""
            wos              = ""
        }
    }
}

function Save-Config($cfg) {
    if (-not (Test-Path $ConfigDir)) {
        New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
    }
    $json = $cfg | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($ConfigFile, $json, [System.Text.UTF8Encoding]::new($false))
    Write-Host "[config] Saved to $ConfigFile" -ForegroundColor Green
}

function Mask-Key($s) {
    if (-not $s -or $s.Trim() -eq "") { return "(not set)" }
    $s = $s.Trim()
    if ($s.Length -le 8) { return "***" }
    return $s.Substring(0, 4) + ("*" * ($s.Length - 8)) + $s.Substring($s.Length - 4)
}

function Prompt-Key($label, $current, $hint) {
    $masked = Mask-Key $current
    Write-Host ""
    Write-Host "  $label" -ForegroundColor Cyan
    if ($hint) { Write-Host "  $hint" -ForegroundColor DarkGray }
    Write-Host "  Current: $masked" -ForegroundColor DarkGray
    $val = Read-Host "  New value (press Enter to keep)"
    if ($val -and $val.Trim()) { return $val.Trim() }
    return $current
}

# ── Load ───────────────────────────────────────────────────────────────────────
$cfg = Get-Config

# ── Show ───────────────────────────────────────────────────────────────────────
if ($Show) {
    Write-Host ""
    Write-Host "=== lit-search-cite Configuration ===" -ForegroundColor Cyan
    Write-Host "  File: $ConfigFile" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  API Keys:"
    Write-Host "    ai4scholar       : $(Mask-Key $cfg.api_keys.ai4scholar)"
    Write-Host "    wanfang          : $(Mask-Key $cfg.api_keys.wanfang)"
    Write-Host "    unpaywall_email  : $(Mask-Key $cfg.api_keys.unpaywall_email)"
    Write-Host "    onescholar       : $(Mask-Key $cfg.api_keys.onescholar)"
    Write-Host "    semantic_scholar : $(Mask-Key $cfg.api_keys.semantic_scholar)"
    Write-Host "    elsevier         : $(Mask-Key $cfg.api_keys.elsevier)"
    Write-Host "    springer         : $(Mask-Key $cfg.api_keys.springer)"
    Write-Host "    wos              : $(Mask-Key $cfg.api_keys.wos)"
    Write-Host ""
    Write-Host "To update: run .\setup.ps1" -ForegroundColor DarkGray
    return
}

# ── Reset ──────────────────────────────────────────────────────────────────────
if ($Reset) {
    $confirm = Read-Host "Clear all API keys? (y/n)"
    if ($confirm -ne 'y') { Write-Host "Cancelled."; return }
    $cfg.api_keys = [PSCustomObject]@{
        ai4scholar=""; wanfang=""; unpaywall_email=""; onescholar=""
        semantic_scholar=""; elsevier=""; springer=""; wos=""
    }
    Save-Config $cfg
    Write-Host "API keys cleared. Run .\setup.ps1 to re-enter them." -ForegroundColor Yellow
    return
}

# ── Interactive wizard ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  lit-search-cite: API Key Setup Wizard" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Keys are stored in: $ConfigFile" -ForegroundColor DarkGray
Write-Host "Press Enter at any prompt to keep the current value." -ForegroundColor DarkGray
Write-Host "Keys are never printed in full — they appear masked." -ForegroundColor DarkGray

$k = $cfg.api_keys

Write-Host ""
Write-Host "--- Academic Search APIs ---" -ForegroundColor Yellow

$k.ai4scholar = Prompt-Key `
    "AI4Scholar API Key  [Semantic Scholar 214M papers + Google Scholar]" `
    $k.ai4scholar `
    "Get at: https://ai4scholar.net  →  Dashboard  →  Open Platform  →  Create Key"

$k.semantic_scholar = Prompt-Key `
    "Semantic Scholar API Key  [direct fallback if AI4Scholar unavailable]" `
    $k.semantic_scholar `
    "Get at: https://www.semanticscholar.org/product/api  (free, 1-2 day approval)"

$k.wanfang = Prompt-Key `
    "Wanfang Data API Key  [structured Chinese literature search]" `
    $k.wanfang `
    "Register at: https://open.wanfangdata.com.cn/"

Write-Host ""
Write-Host "--- PDF & Journal Metadata APIs ---" -ForegroundColor Yellow

$k.unpaywall_email = Prompt-Key `
    "Unpaywall Email  [open-access PDF discovery — required by their ToS]" `
    $k.unpaywall_email `
    "Any valid email works. Unpaywall is free. Example: yourname@email.com"

$k.onescholar = Prompt-Key `
    "OneScholar API Key  [JCR/CAS journal ranking + Impact Factor]" `
    $k.onescholar `
    "Get at: https://www.scigreat.com/s/app/?t=oneapi-info"

$k.elsevier = Prompt-Key `
    "Elsevier API Key  [Scopus 78M papers, citation metrics]" `
    $k.elsevier `
    "Get at: https://dev.elsevier.com/  (requires institutional affiliation)"

$k.springer = Prompt-Key `
    "Springer Nature API Key  [Springer OA full-text metadata]" `
    $k.springer `
    "Get at: https://dev.springernature.com/"

$k.wos = Prompt-Key `
    "Web of Science API Key  [authoritative citations, paid]" `
    $k.wos `
    "Get at: https://developer.clarivate.com/"

$cfg.api_keys = $k
Save-Config $cfg

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "What's next:" -ForegroundColor Cyan
Write-Host "  View config        : .\setup.ps1 -Show"
Write-Host "  Chinese search     : .\scripts\cnki-search.ps1 -Query `"大语言模型 代码生成`""
Write-Host "  Chrome DevTools MCP: references/chrome-devtools.md (CNKI + paywall fallback)"
Write-Host ""
