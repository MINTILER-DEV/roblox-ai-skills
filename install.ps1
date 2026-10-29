# Install the Roblox skills and custom agents for Codex (Windows).
# Optional: -SkillsDir <path> -AgentsDir <path> for an alternate installation.
param([string]$SkillsDir, [string]$AgentsDir)
$ErrorActionPreference = "Stop"
$installer = Join-Path $PSScriptRoot "scripts/install.py"
$installArgs = @($installer)
if ($SkillsDir) { $installArgs += @("--skills-dir", $SkillsDir) }
if ($AgentsDir) { $installArgs += @("--agents-dir", $AgentsDir) }
if (Get-Command python -ErrorAction SilentlyContinue) {
    & python @installArgs
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 @installArgs
} else {
    throw "Python 3.11+ is required. Install it from https://www.python.org/downloads/."
}
if ($LASTEXITCODE -ne 0) { throw "Codex skill installation failed (exit $LASTEXITCODE)." }
