# Create portable directory structure
Param(
    [string]$OutputDir = "BytefenseOS-Portable"
)

Write-Host "Creating Bytefense OS Portable v1.0.0..." -ForegroundColor Green
Write-Host "Output directory: $OutputDir" -ForegroundColor Cyan

# Create portable directory structure
if (Test-Path $OutputDir) {
    Write-Host "Removing existing directory..." -ForegroundColor Yellow
    Remove-Item $OutputDir -Recurse -Force
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputDir\bin" -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputDir\config" -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputDir\web" -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputDir\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputDir\data" -Force | Out-Null

# Copy files
if (Test-Path ".\bin") {
    Copy-Item -Path ".\bin\*" -Destination "$OutputDir\bin\" -Recurse -Force
    Write-Host "Binaries copied" -ForegroundColor Green
}

if (Test-Path ".\system") {
    Copy-Item -Path ".\system\*" -Destination "$OutputDir\config\" -Recurse -Force
    Write-Host "System files copied" -ForegroundColor Green
}

if (Test-Path ".\bytefense_web") {
    Copy-Item -Path ".\bytefense_web\*" -Destination "$OutputDir\web\" -Recurse -Force
    Write-Host "Web interface copied" -ForegroundColor Green
}

if (Test-Path ".\feeds") {
    Copy-Item -Path ".\feeds\*" -Destination "$OutputDir\data\" -Recurse -Force
    Write-Host "Data feeds copied" -ForegroundColor Green
}

# Create launcher scripts
$startBat = @"
@echo off
title Bytefense OS - Dashboard
echo Starting Bytefense OS Dashboard...
cd /d "%~dp0bin"
python bytefense-api.py
pause
"@
$startBat | Out-File -FilePath "$OutputDir\start-dashboard.bat" -Encoding ASCII

$watchBat = @"
@echo off
title Bytefense OS - Monitor
echo Starting Bytefense OS Monitor...
cd /d "%~dp0bin"
python bytefense-watch.py
pause
"@
$watchBat | Out-File -FilePath "$OutputDir\start-monitor.bat" -Encoding ASCII

$statusBat = @"
@echo off
title Bytefense OS - Status
echo Bytefense OS Status Check
echo ========================
cd /d "%~dp0bin"
python -c "import psutil; print('System OK' if psutil.cpu_percent() < 100 else 'System Busy')"
echo.
echo Python version:
python --version
echo.
echo Available scripts:
dir *.py /b
pause
"@
$statusBat | Out-File -FilePath "$OutputDir\status.bat" -Encoding ASCII

# Create PowerShell launcher
$startPs1 = @"
# Bytefense OS Portable Launcher
Param(
    [switch]$Dashboard,
    [switch]$Monitor,
    [switch]$Status
)

`$scriptDir = Split-Path -Parent `$MyInvocation.MyCommand.Definition
`$binDir = Join-Path `$scriptDir "bin"

function Start-Dashboard {
    Write-Host "Starting Bytefense OS Dashboard..." -ForegroundColor Green
    Set-Location `$binDir
    python bytefense-api.py
}

function Start-Monitor {
    Write-Host "Starting Bytefense OS Monitor..." -ForegroundColor Green
    Set-Location `$binDir
    python bytefense-watch.py
}

function Show-Status {
    Write-Host "Bytefense OS Portable Status" -ForegroundColor Cyan
    Write-Host "===========================" -ForegroundColor Gray
    
    try {
        `$pythonVersion = python --version 2>`$null
        Write-Host "Python: `$pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "Python: Not available" -ForegroundColor Red
    }
    
    Write-Host "Location: `$scriptDir" -ForegroundColor White
    Write-Host "Bin Directory: `$binDir" -ForegroundColor White
    
    if (Test-Path `$binDir) {
        `$scripts = Get-ChildItem "`$binDir\*.py" | Measure-Object
        Write-Host "Python Scripts: `$(`$scripts.Count)" -ForegroundColor Green
    }
}

switch (`$true) {
    `$Dashboard { Start-Dashboard }
    `$Monitor { Start-Monitor }
    `$Status { Show-Status }
    default {
        Write-Host "Bytefense OS Portable v1.0.0" -ForegroundColor Cyan
        Write-Host "Usage:" -ForegroundColor White
        Write-Host "  .\start.ps1 -Dashboard  # Start web dashboard" -ForegroundColor White
        Write-Host "  .\start.ps1 -Monitor    # Start system monitor" -ForegroundColor White
        Write-Host "  .\start.ps1 -Status     # Show system status" -ForegroundColor White
        Write-Host "" 
        Write-Host "Or use batch files:" -ForegroundColor White
        Write-Host "  start-dashboard.bat" -ForegroundColor White
        Write-Host "  start-monitor.bat" -ForegroundColor White
        Write-Host "  status.bat" -ForegroundColor White
    }
}
"@
$startPs1 | Out-File -FilePath "$OutputDir\start.ps1" -Encoding UTF8

# Create README
$readme = @"
# Bytefense OS Portable v1.0.0

## Quick Start

### Windows Batch Files
- `start-dashboard.bat` - Start web dashboard (http://localhost:5000)
- `start-monitor.bat` - Start system monitor
- `status.bat` - Check system status

### PowerShell
```powershell
.\start.ps1 -Dashboard  # Start web dashboard
.\start.ps1 -Monitor    # Start system monitor
.\start.ps1 -Status     # Show system status
```

Write-Host "✅ Portable version created in BytefenseOS-Portable folder" -ForegroundColor Green