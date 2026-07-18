# OpenCode SEO Suite - Windows installer
# Copies skills/agents/commands to the global OpenCode config and scripts to
# %USERPROFILE%\.config\opencode\seo-suite\scripts.
# Run:  powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

$root     = Split-Path -Parent $MyInvocation.MyCommand.Path
$ocConfig = Join-Path $env:USERPROFILE ".config\opencode"
$suiteDir = Join-Path $ocConfig "seo-suite"

Write-Host "OpenCode SEO Suite installer" -ForegroundColor Cyan
Write-Host "============================"

# --- 1. Sanity checks -------------------------------------------------------
foreach ($dir in @(".opencode\skills", ".opencode\agents", ".opencode\commands", "scripts")) {
    if (-not (Test-Path (Join-Path $root $dir))) {
        Write-Host "ERROR: $dir not found. Run this script from the suite root." -ForegroundColor Red
        exit 1
    }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "WARNING: python not found on PATH. The data layer scripts need Python 3.10+." -ForegroundColor Yellow
} else {
    Write-Host "Python: $($python.Source)"
}

# --- 2. Copy skills, agents, commands ---------------------------------------
foreach ($pair in @(@(".opencode\skills", "skills"), @(".opencode\agents", "agents"), @(".opencode\commands", "commands"))) {
    $src = Join-Path $root $pair[0]
    $dst = Join-Path $ocConfig $pair[1]
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force
    $count = (Get-ChildItem $dst -Directory -ErrorAction SilentlyContinue).Count
    Write-Host "Installed $($pair[1]) -> $dst"
}

# --- 3. Scripts + suite home ------------------------------------------------
New-Item -ItemType Directory -Force -Path (Join-Path $suiteDir "scripts") | Out-Null
Copy-Item -Path (Join-Path $root "scripts\*") -Destination (Join-Path $suiteDir "scripts") -Recurse -Force
Write-Host "Installed scripts -> $suiteDir\scripts"

# --- 4. Python dependencies (user-level, so `python scripts/...` works) ----
if ($python) {
    python -m pip install --user --quiet pyyaml 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python deps installed (user level): pyyaml"
    } else {
        Write-Host "WARNING: could not install pyyaml; project_memory.py needs it." -ForegroundColor Yellow
        Write-Host "         Run: python -m pip install --user pyyaml"
    }
}

# --- 5. DataForSEO credentials (optional prompt) -----------------------------
$credFile = Join-Path $suiteDir "credentials.json"
if (-not (Test-Path $credFile)) {
    Write-Host ""
    $answer = Read-Host "Enter DataForSEO credentials now? [y/N]"
    if ($answer -match "^[yY]") {
        $login = Read-Host "DataForSEO login (email)"
        $pass  = Read-Host "DataForSEO API password"
        @{ DATAFORSEO_LOGIN = $login; DATAFORSEO_PASSWORD = $pass } |
            ConvertTo-Json | Set-Content -Path $credFile -Encoding UTF8
        # Restrict ACL to the current user (equivalent of chmod 600)
        icacls $credFile /inheritance:r /grant:r "$env:USERNAME:(R,W)" | Out-Null
        Write-Host "Credentials written to $credFile (user-only ACL)"
    } else {
        Write-Host "Skipped. Add credentials later via environment variables,"
        Write-Host "a project .env file, or $credFile - see docs\DATAFORSEO-SETUP.md"
    }
}

Write-Host ""
Write-Host "Done. Restart OpenCode to load the new skills, then try:" -ForegroundColor Green
Write-Host "  /site-audit https://example.com"
Write-Host "  /keyword-research best espresso beans"
Write-Host ""
Write-Host "Verify with: python scripts\seo_config.py status"
