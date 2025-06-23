# Bytefense OS - RustDesk Windows Installer
param (
    [string]$Config = "bytefense-rustdesk-config",
    [string]$Password = "Bytefense@2024"
)

$ErrorActionPreference = 'Stop'

Write-Host "🔧 Bytefense OS - Instalador RustDesk para Windows" -ForegroundColor Cyan
Write-Host "📅 $(Get-Date)" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Gray

try {
    # Obtener la última versión
    Write-Host "🔍 Obteniendo última versión de RustDesk..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/rustdesk/rustdesk/releases/latest"
    $version = $response.tag_name -replace '^v', ''
    
    Write-Host "📦 Versión detectada: $version" -ForegroundColor Green
    
    # Detectar arquitectura
    $arch = if ([Environment]::Is64BitOperatingSystem) { "x86_64" } else { "i686" }
    $fileName = "rustdesk-$version-$arch.exe"
    $downloadUrl = "https://github.com/rustdesk/rustdesk/releases/download/$($response.tag_name)/$fileName"
    
    Write-Host "⬇️ Descargando RustDesk $version para $arch..." -ForegroundColor Yellow
    
    # Crear directorio temporal
    $tempDir = Join-Path $env:TEMP "bytefense-rustdesk"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    $installerPath = Join-Path $tempDir $fileName
    
    # Descargar instalador
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    
    Write-Host "📦 Instalando RustDesk..." -ForegroundColor Yellow
    
    # Instalar silenciosamente
    Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait
    
    # Esperar a que la instalación complete
    Start-Sleep -Seconds 5
    
    # Buscar ejecutable de RustDesk
    $rustdeskPaths = @(
        "$env:ProgramFiles\RustDesk\rustdesk.exe",
        "${env:ProgramFiles(x86)}\RustDesk\rustdesk.exe",
        "$env:LOCALAPPDATA\RustDesk\rustdesk.exe"
    )
    
    $rustdeskExe = $null
    foreach ($path in $rustdeskPaths) {
        if (Test-Path $path) {
            $rustdeskExe = $path
            break
        }
    }
    
    if (-not $rustdeskExe) {
        throw "No se pudo encontrar el ejecutable de RustDesk después de la instalación"
    }
    
    Write-Host "⚙️ Configurando RustDesk para Bytefense..." -ForegroundColor Yellow
    
    # Configurar RustDesk
    if ($Config) {
        try {
            & $rustdeskExe --config $Config
        } catch {
            Write-Warning "No se pudo aplicar configuración personalizada: $_"
        }
    }
    
    if ($Password) {
        try {
            & $rustdeskExe --password $Password
        } catch {
            Write-Warning "No se pudo establecer contraseña: $_"
        }
    }
    
    # Obtener ID
    try {
        $rustdeskId = & $rustdeskExe --get-id 2>$null
    } catch {
        $rustdeskId = "No disponible"
    }
    
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "🆔 RustDesk ID: $rustdeskId" -ForegroundColor Green
    Write-Host "🔑 Password: $Password" -ForegroundColor Green
    Write-Host "🌐 Configuración: $Config" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Cyan
    
    # Crear servicio de Windows
    Write-Host "🔧 Configurando servicio de Windows..." -ForegroundColor Yellow
    
    try {
        # Instalar como servicio
        & $rustdeskExe --install-service
        
        # Configurar servicio para inicio automático
        Set-Service -Name "RustDesk" -StartupType Automatic -ErrorAction SilentlyContinue
        Start-Service -Name "RustDesk" -ErrorAction SilentlyContinue
    } catch {
        Write-Warning "No se pudo configurar el servicio: $_"
    }
    
    # Limpiar archivos temporales
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ RustDesk instalado y configurado exitosamente para Bytefense OS" -ForegroundColor Green
    
} catch {
    Write-Error "❌ Error durante la instalación: $_"
    exit 1
}