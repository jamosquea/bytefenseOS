#!/bin/bash

# Activar modo estricto
set -euo pipefail
IFS=$'\n\t'

# Verificar ejecución como root
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  Este instalador debe ejecutarse como root."
  exit 1
fi

# Crear carpeta de logs
mkdir -p /opt/bytefense/logs
exec > >(tee -i /opt/bytefense/logs/install.log)
exec 2>&1

echo "🚀 [Bytefense] Instalación iniciada - $(date)"

# Crear estructura de directorios
echo "📂 Creando estructura base..."
mkdir -p /opt/bytefense/{bin,logs,feeds,intel,honey,tmp,web,wireguard}

# Crear usuario del sistema si no existe
if ! id "byteuser" &>/dev/null; then
  useradd -r -s /bin/false byteuser
  echo "👤 Usuario byteuser creado."
fi

# Actualizar sistema
echo "🔄 Actualizando paquetes del sistema..."
apt update && apt upgrade -y

# Instalar dependencias esenciales
echo "📦 Instalando dependencias..."
apt install -y \
  curl git unzip dnsutils net-tools ufw \
  python3 python3-pip python3-venv \
  qrencode lighttpd wireguard \
  sudo

# Descargar scripts principales
cd /opt/bytefense/bin

declare -A SCRIPTS=(
  ["bytefense-ctl"]="https://raw.githubusercontent.com/jamosquea/bytefenseOS/main/bin/bytefense-ctl"
  ["bytefense-watch"]="https://raw.githubusercontent.com/jamosquea/bytefenseOS/main/bin/bytefense-watch"
  ["bytefense-register"]="https://raw.githubusercontent.com/jamosquea/bytefenseOS/main/bin/bytefense-register"
  ["clone.sh"]="https://raw.githubusercontent.com/jamosquea/bytefenseOS/main/bin/clone.sh"
)

echo "⬇️  Descargando scripts desde el repositorio..."
for script in "${!SCRIPTS[@]}"; do
  echo "→ $script"
  curl -fsSL "${SCRIPTS[$script]}" -o "$script"
  chmod +x "$script"
done

# Symlink al sistema
ln -sf /opt/bytefense/bin/bytefense-ctl /usr/local/bin/bytefense-ctl

# Configurar lighttpd para servir en 8080
echo "🌐 Configurando servidor web..."
sed -i 's/server.port\s*=.*/server.port = 8080/' /etc/lighttpd/lighttpd.conf
systemctl enable lighttpd
systemctl restart lighttpd

# Crear index temporal
echo "<h1>Bytefense OS en curso de configuración...</h1>" > /var/www/html/index.html

# Finalizar
echo "✅ Instalación completada."
echo "🎯 Ejecutá ahora: sudo bytefense-ctl init"