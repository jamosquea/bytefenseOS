# Script PowerShell para construir .deb usando WSL
param(
    [string]$Version = "1.0.0",
    [string]$Architecture = "all"
)

$PackageName = "bytefense-os"
$OutputDir = "dist"
$DebFile = "$OutputDir\${PackageName}_${Version}_${Architecture}.deb"

Write-Host "📦 Construyendo paquete .deb de Bytefense OS v$Version" -ForegroundColor Green

# Verificar si WSL está disponible
try {
    wsl --version | Out-Null
    Write-Host "✅ WSL detectado" -ForegroundColor Green
} catch {
    Write-Host "❌ WSL no está instalado. Instálalo con: wsl --install" -ForegroundColor Red
    exit 1
}

# Ejecutar construcción en WSL con copia al sistema de archivos Linux
Write-Host "🔨 Ejecutando construcción en WSL..." -ForegroundColor Yellow

$wslCommand = @"
cd /tmp
rm -rf bytefense-build
cp -r /mnt/c/proyectos/bytefense bytefense-build
cd bytefense-build
chmod +x build-deb.sh
./build-deb.sh
cp -r dist /mnt/c/proyectos/bytefense/
"@

wsl bash -c $wslCommand

if (Test-Path $DebFile) {
    Write-Host "✅ Paquete .deb creado exitosamente:" -ForegroundColor Green
    Write-Host "📦 Archivo: $DebFile" -ForegroundColor Cyan
    Write-Host "📏 Tamaño: $([math]::Round((Get-Item $DebFile).Length / 1MB, 2)) MB" -ForegroundColor Cyan
    
    # Mostrar información del paquete
    Write-Host "\n📊 Información del paquete:" -ForegroundColor Yellow
    wsl dpkg-deb --info "/mnt/c/proyectos/bytefense/$DebFile"
} else {
    Write-Host "❌ Error: No se pudo crear el paquete .deb" -ForegroundColor Red
    Write-Host "🔍 Revisa los logs de construcción arriba" -ForegroundColor Yellow
}