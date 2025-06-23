#!/bin/bash

# Bytefense OS - Instalación Directa
# Versión: 1.0.0

set -e

PACKAGE_NAME="bytefense-os"
VERSION="1.0.0"
INSTALL_DIR="/opt/bytefense"
USER="bytefense"

echo "🔧 Iniciando instalación de Bytefense OS v$VERSION"

# Verificar permisos de root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Este script debe ejecutarse como root (sudo)"
   exit 1
fi

# Crear usuario del sistema
echo "👤 Creando usuario del sistema..."
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" -c "Bytefense System User" "$USER"
fi

# Crear directorios
echo "📁 Creando estructura de directorios..."
mkdir -p "$INSTALL_DIR"/{bin,web,system,feeds,logs,config,data}
chown -R "$USER:$USER" "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"

# Copiar archivos
echo "📋 Copiando archivos del sistema..."
cp -r bin/* "$INSTALL_DIR/bin/"
cp -r bytefense_web/* "$INSTALL_DIR/web/"
cp -r system/* "$INSTALL_DIR/system/"
cp -r feeds/* "$INSTALL_DIR/feeds/"

# Hacer ejecutables
chmod +x "$INSTALL_DIR/bin"/*

# Instalar dependencias Python
echo "🐍 Instalando dependencias de Python..."
pip3 install requests psutil flask cryptography

# Instalar servicios systemd
echo "⚙️ Configurando servicios del sistema..."
cp "$INSTALL_DIR/system"/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bytefense-watch.service
systemctl enable bytefense-intel-updater.service

# Configurar firewall básico
echo "🔥 Configurando firewall..."
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Crear enlaces simbólicos para comandos
echo "🔗 Creando enlaces de comandos..."
ln -sf "$INSTALL_DIR/bin/bytefense-ctl" /usr/local/bin/bytefense-ctl
ln -sf "$INSTALL_DIR/bin/bytefense-health" /usr/local/bin/bytefense-health

# Iniciar servicios
echo "🚀 Iniciando servicios..."
systemctl start bytefense-watch.service
systemctl start bytefense-intel-updater.service

echo "✅ ¡Instalación completada exitosamente!"
echo "📊 Estado del sistema: bytefense-ctl status"
echo "🌐 Dashboard web: http://localhost/bytefense"