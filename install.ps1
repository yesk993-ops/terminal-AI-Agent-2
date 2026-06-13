param()

Write-Host "=== tell - AI Agent Windows Installer ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Python not found. Install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Check venv
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    & python -m venv $venvPath
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# Install deps
$pip = Join-Path $venvPath "Scripts\pip.exe"
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
& $pip install --upgrade pip -q
& $pip install -r (Join-Path $PSScriptRoot "requirements.txt")

Write-Host ""
Write-Host "=== Installation complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Set your API key (add to profile to persist):"
Write-Host "  `$env:NVIDIA_API_KEY = `"nvapi-...`""
Write-Host ""
Write-Host "Then use:"
Write-Host "  tell.bat `"what is python?`"       # one-shot query"
Write-Host "  tell.bat `"do check disk`"          # one-shot task"
Write-Host "  python agent.py                     # interactive mode"
Write-Host ""
