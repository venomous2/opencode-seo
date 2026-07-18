# OpenCode SEO Suite - Windows uninstaller
$ErrorActionPreference = "Stop"
$ocConfig = Join-Path $env:USERPROFILE ".config\opencode"
$suiteDir = Join-Path $ocConfig "seo-suite"

# Remove only the skill/agent/command folders this suite ships (read the
# names from the local repo so we never touch the user's other skills).
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
foreach ($pair in @(@(".opencode\skills", "skills"), @(".opencode\agents", "agents"), @(".opencode\commands", "commands"))) {
    $src = Join-Path $root $pair[0]
    $dst = Join-Path $ocConfig $pair[1]
    if (-not (Test-Path $src)) { continue }
    Get-ChildItem $src | ForEach-Object {
        $target = Join-Path $dst $_.Name
        if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    }
    Write-Host "Removed suite $($pair[1]) from $dst"
}

$answer = Read-Host "Also remove scripts, venv, and credentials in $suiteDir ? [y/N]"
if ($answer -match "^[yY]") {
    Remove-Item -Recurse -Force $suiteDir -ErrorAction SilentlyContinue
    Write-Host "Removed $suiteDir"
} else {
    Write-Host "Kept $suiteDir (scripts + credentials)."
}
Write-Host "Done. Restart OpenCode."
