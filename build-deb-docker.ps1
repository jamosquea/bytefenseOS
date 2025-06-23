# Script PowerShell para construir .deb usando Docker
param(
    [string]$Version = "1.0.0"
)

$PackageName = "bytefense-os"
$ImageName = "bytefense-builder"
$ContainerName = "bytefense-build-temp"

Write-Host "🐳 Construyendo paquete .deb usando Docker" -ForegroundColor Green

# Verificar si Docker está disponible
try {
    docker --version | Out-Null
    Write-Host "✅ Docker detectado" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está instalado. Descárgalo de: https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
    exit 1
}

# Limpiar contenedores anteriores
docker rm -f $ContainerName 2>$null

# Construir imagen
Write-Host "🔨 Construyendo imagen Docker..." -ForegroundColor Yellow
docker build -f Dockerfile.deb -t $ImageName .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Imagen construida exitosamente" -ForegroundColor Green
    
    # Crear directorio de salida
    if (!(Test-Path "dist")) {
        New-Item -ItemType Directory -Path "dist" -Force
    }
    
    # Ejecutar contenedor y extraer archivos
    Write-Host "📦 Extrayendo paquete .deb..." -ForegroundColor Yellow
    docker run --name $ContainerName -v "${PWD}\dist:/output" $ImageName
    
    # Limpiar contenedor
    docker rm $ContainerName
    
    # Verificar resultado
    $DebFile = Get-ChildItem "dist\*.deb" | Select-Object -First 1
    if ($DebFile) {
        Write-Host "✅ Paquete .deb creado exitosamente:" -ForegroundColor Green
        Write-Host "📦 Archivo: $($DebFile.FullName)" -ForegroundColor Cyan
        Write-Host "📏 Tamaño: $([math]::Round($DebFile.Length / 1MB, 2)) MB" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Error: No se encontró el archivo .deb" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Error al construir la imagen Docker" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Proceso completado" -ForegroundColor Green