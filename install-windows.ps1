# Windows installer script for Bytefense OS
Param(
    [switch]$Uninstall,
    [switch]$Status,
    [switch]$Start,
    [switch]$Stop
)

# Configuration
$InstallPath = "C:\Program Files\BytefenseOS"
$ServiceName = "BytefenseOS"
$ConfigPath = "$env:PROGRAMDATA\BytefenseOS"
$LogPath = "$ConfigPath\logs"
$Version = "1.0.0"

# Colors for output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-ColorOutput "Error: Este script debe ejecutarse como Administrador" "Red"
    Write-ColorOutput "Solucion: Haz clic derecho en PowerShell y selecciona 'Ejecutar como administrador'" "Yellow"
    exit 1
}

# Status function
function Show-Status {
    Write-ColorOutput "Estado de Bytefense OS v$Version" "Cyan"
    Write-ColorOutput "================================================" "Gray"
    
    if (Test-Path $InstallPath) {
        Write-ColorOutput "Instalacion: $InstallPath" "Green"
    } else {
        Write-ColorOutput "No instalado" "Red"
        return
    }
    
    if (Test-Path $ConfigPath) {
        Write-ColorOutput "Configuracion: $ConfigPath" "Green"
    } else {
        Write-ColorOutput "Configuracion: No encontrada" "Yellow"
    }
    
    # Check services
    $services = @("BytefenseOS-Dashboard", "BytefenseOS-Watch", "BytefenseOS-Intel")
    foreach ($svc in $services) {
        $service = Get-Service $svc -ErrorAction SilentlyContinue
        if ($service) {
            $status = $service.Status
            $color = if ($status -eq "Running") { "Green" } else { "Yellow" }
            Write-ColorOutput "Servicio $svc`: $status" $color
        } else {
            Write-ColorOutput "Servicio $svc`: No encontrado" "Red"
        }
    }
    
    # Check Python dependencies
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion) {
            Write-ColorOutput "Python: $pythonVersion" "Green"
        } else {
            Write-ColorOutput "Python: No instalado" "Red"
        }
    } catch {
        Write-ColorOutput "Python: No disponible" "Red"
    }
}

# Start services
function Start-BytefenseServices {
    Write-ColorOutput "Iniciando servicios de Bytefense OS..." "Green"
    $services = @("BytefenseOS-Dashboard", "BytefenseOS-Watch", "BytefenseOS-Intel")
    foreach ($svc in $services) {
        try {
            Start-Service $svc -ErrorAction Stop
            Write-ColorOutput "Servicio $svc iniciado" "Green"
        } catch {
            Write-ColorOutput "Error iniciando $svc`: $($_.Exception.Message)" "Red"
        }
    }
}

# Stop services
function Stop-BytefenseServices {
    Write-ColorOutput "Deteniendo servicios de Bytefense OS..." "Yellow"
    $services = @("BytefenseOS-Dashboard", "BytefenseOS-Watch", "BytefenseOS-Intel")
    foreach ($svc in $services) {
        try {
            Stop-Service $svc -Force -ErrorAction Stop
            Write-ColorOutput "Servicio $svc detenido" "Green"
        } catch {
            Write-ColorOutput "Error deteniendo $svc`: $($_.Exception.Message)" "Red"
        }
    }
}

# Uninstall function
function Remove-BytefenseOS {
    Write-ColorOutput "Desinstalando Bytefense OS..." "Yellow"
    
    # Stop services first
    Stop-BytefenseServices
    
    # Remove services
    $services = @("BytefenseOS-Dashboard", "BytefenseOS-Watch", "BytefenseOS-Intel")
    foreach ($svc in $services) {
        if (Get-Service $svc -ErrorAction SilentlyContinue) {
            try {
                & sc.exe delete $svc
                Write-ColorOutput "Servicio $svc eliminado" "Green"
            } catch {
                Write-ColorOutput "Error eliminando servicio $svc" "Red"
            }
        }
    }
    
    # Remove from PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $pathToRemove = ";$InstallPath\bin"
    $newPath = $currentPath.Replace($pathToRemove, "")
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
    
    # Remove installation directory
    if (Test-Path $InstallPath) {
        Remove-Item $InstallPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-ColorOutput "Archivos de instalacion eliminados" "Green"
    }
    
    # Remove configuration (optional)
    if (Test-Path $ConfigPath) {
        $response = Read-Host "Eliminar tambien la configuracion? (y/N)"
        if ($response -eq "y" -or $response -eq "Y") {
            Remove-Item $ConfigPath -Recurse -Force -ErrorAction SilentlyContinue
            Write-ColorOutput "Configuracion eliminada" "Green"
        }
    }
    
    Write-ColorOutput "Bytefense OS desinstalado exitosamente" "Green"
}

# Install function
function Install-BytefenseOS {
    Write-ColorOutput "Instalando Bytefense OS v$Version..." "Green"
    
    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        if (-not $pythonVersion) {
            Write-ColorOutput "Python no esta instalado. Por favor instale Python 3.8+ primero." "Red"
            Write-ColorOutput "Descarga desde: https://www.python.org/downloads/" "Yellow"
            return
        }
    } catch {
        Write-ColorOutput "No se pudo verificar Python. Continuando..." "Yellow"
    }
    
    # Create directories
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    New-Item -ItemType Directory -Path "$InstallPath\bin" -Force | Out-Null
    New-Item -ItemType Directory -Path "$InstallPath\system" -Force | Out-Null
    New-Item -ItemType Directory -Path "$InstallPath\web" -Force | Out-Null
    New-Item -ItemType Directory -Path $ConfigPath -Force | Out-Null
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
    
    # Copy files
    if (Test-Path ".\bin") {
        Copy-Item -Path ".\bin\*" -Destination "$InstallPath\bin\" -Recurse -Force
        Write-ColorOutput "Binarios copiados" "Green"
    }
    
    if (Test-Path ".\system") {
        Copy-Item -Path ".\system\*" -Destination "$InstallPath\system\" -Recurse -Force
        Write-ColorOutput "Archivos de sistema copiados" "Green"
    }
    
    if (Test-Path ".\bytefense_web") {
        Copy-Item -Path ".\bytefense_web\*" -Destination "$InstallPath\web\" -Recurse -Force
        Write-ColorOutput "Interfaz web copiada" "Green"
    }
    
    # Add to PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    if ($currentPath -notlike "*$InstallPath\bin*") {
        $newPath = "$currentPath;$InstallPath\bin"
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
        Write-ColorOutput "PATH actualizado" "Green"
    }
    
    # Install Python dependencies
    try {
        Write-ColorOutput "Instalando dependencias de Python..." "Cyan"
        & python -m pip install --upgrade pip
        & python -m pip install flask requests psutil netifaces
        Write-ColorOutput "Dependencias instaladas" "Green"
    } catch {
        Write-ColorOutput "Error instalando dependencias: $($_.Exception.Message)" "Yellow"
    }
    
    # Create batch files for services
    $dashboardBat = @"
@echo off
cd /d "$InstallPath\bin"
python bytefense-api.py
"@
    $dashboardBat | Out-File -FilePath "$InstallPath\bin\dashboard.bat" -Encoding ASCII
    
    $watchBat = @"
@echo off
cd /d "$InstallPath\bin"
python bytefense-watch.py
"@
    $watchBat | Out-File -FilePath "$InstallPath\bin\watch.bat" -Encoding ASCII
    
    # Create services using sc.exe
    try {
        & sc.exe create "BytefenseOS-Dashboard" binPath= "$InstallPath\bin\dashboard.bat" start= auto
        & sc.exe create "BytefenseOS-Watch" binPath= "$InstallPath\bin\watch.bat" start= auto
        Write-ColorOutput "Servicios creados" "Green"
    } catch {
        Write-ColorOutput "Error creando servicios: $($_.Exception.Message)" "Yellow"
    }
    
    Write-ColorOutput "Bytefense OS instalado exitosamente!" "Green"
    Write-ColorOutput "" 
    Write-ColorOutput "Comandos disponibles:" "Cyan"
    Write-ColorOutput "   .\install-windows.ps1 -Status    # Ver estado" "White"
    Write-ColorOutput "   .\install-windows.ps1 -Start     # Iniciar servicios" "White"
    Write-ColorOutput "   .\install-windows.ps1 -Stop      # Detener servicios" "White"
    Write-ColorOutput "   .\install-windows.ps1 -Uninstall # Desinstalar" "White"
    Write-ColorOutput "" 
    Write-ColorOutput "Dashboard web: http://localhost:5000" "Green"
}

# Main execution
switch ($true) {
    $Status { Show-Status }
    $Start { Start-BytefenseServices }
    $Stop { Stop-BytefenseServices }
    $Uninstall { Remove-BytefenseOS }
    default { Install-BytefenseOS }
}