# Create Debian control files
$DebianDir = "debian\DEBIAN"
if (!(Test-Path $DebianDir)) {
    New-Item -ItemType Directory -Path $DebianDir -Force
}

# Create control file
@"
Package: bytefense-os
Version: 1.0.0
Section: security
Priority: optional
Architecture: amd64
Depends: python3, python3-pip, iptables, systemd
Maintainer: Bytefense Team <info@bytefense.com>
Description: Bytefense OS - Sistema de Seguridad Integral
 Bytefense OS es una solución completa de seguridad que incluye:
  - Firewall avanzado con IA
  - Sistema de detección de intrusos (IDS)
  - Monitoreo de red en tiempo real
  - Dashboard web interactivo
  - API REST para integración
"@ | Out-File -FilePath "$DebianDir\control" -Encoding UTF8

# Create preinst file
@"
#!/bin/bash
set -e

# Pre-installation script for Bytefense OS
echo "Preparando instalación de Bytefense OS..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Este paquete debe instalarse como root"
    exit 1
fi

# Check system requirements
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 es requerido"
    exit 1
fi

# Stop existing services if they exist
for service in bytefense-watch bytefense-dashboard bytefense-intel-updater; do
    if systemctl is-active --quiet $service 2>/dev/null; then
        echo "Deteniendo servicio existente: $service"
        systemctl stop $service || true
    fi
done

exit 0
"@ | Out-File -FilePath "$DebianDir\preinst" -Encoding UTF8

# Create postinst file
@"
#!/bin/bash
set -e

# Post-installation script for Bytefense OS
echo "Configurando Bytefense OS..."

# Set proper permissions
chmod +x /opt/bytefense/bin/*
chown -R root:root /opt/bytefense

# Create bytefense user if it doesn't exist
if ! id "bytefense" &>/dev/null; then
    useradd -r -s /bin/false -d /opt/bytefense bytefense
fi

# Create necessary directories
mkdir -p /var/log/bytefense
mkdir -p /var/lib/bytefense
chown bytefense:bytefense /var/log/bytefense
chown bytefense:bytefense /var/lib/bytefense

# Enable and start services
systemctl daemon-reload
for service in bytefense-watch bytefense-dashboard bytefense-intel-updater; do
    if [ -f "/etc/systemd/system/$service.service" ]; then
        echo "Habilitando servicio: $service"
        systemctl enable $service
        systemctl start $service
    fi
done

echo "Bytefense OS instalado exitosamente"
echo "Dashboard disponible en: http://localhost:8080"

exit 0
"@ | Out-File -FilePath "$DebianDir\postinst" -Encoding UTF8

# Create prerm file
@"
#!/bin/bash
set -e

# Pre-removal script for Bytefense OS
echo "Preparando desinstalación de Bytefense OS..."

# Stop all services
for service in bytefense-watch bytefense-dashboard bytefense-intel-updater; do
    if systemctl is-active --quiet $service 2>/dev/null; then
        echo "Deteniendo servicio: $service"
        systemctl stop $service || true
    fi
    if systemctl is-enabled --quiet $service 2>/dev/null; then
        echo "Deshabilitando servicio: $service"
        systemctl disable $service || true
    fi
done

exit 0
"@ | Out-File -FilePath "$DebianDir\postrm" -Encoding UTF8

# Create postrm file
@"
#!/bin/bash
set -e

# Post-removal script for Bytefense OS
echo "Limpiando Bytefense OS..."

if [ "$1" = "purge" ]; then
    # Remove user and data only on purge
    if id "bytefense" &>/dev/null; then
        userdel bytefense || true
    fi
    
    # Remove log and data directories
    rm -rf /var/log/bytefense
    rm -rf /var/lib/bytefense
    
    echo "Bytefense OS completamente removido"
fi

exit 0
"@ | Out-File -FilePath "$DebianDir\postrm" -Encoding UTF8

Write-Host "✅ Archivos de control Debian creados exitosamente" -ForegroundColor Green