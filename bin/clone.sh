#!/bin/bash
# Bytefense OS - Script de Clonación de Nodos

BYTEFENSE_HOME="/opt/bytefense"
CLONE_DIR="/tmp/bytefense-clone"
DATE=$(date +%Y%m%d_%H%M%S)

echo "📦 Creando imagen de clonación de Bytefense OS..."

# Crear directorio temporal
mkdir -p "$CLONE_DIR"

# Copiar archivos esenciales
echo "📋 Copiando archivos del sistema..."
cp -r "$BYTEFENSE_HOME"/{bin,feeds,web,docs,system} "$CLONE_DIR/"

# Crear script de instalación para el clon
cat > "$CLONE_DIR/install-clone.sh" << 'EOF'
#!/bin/bash
# Instalador de Nodo Clonado Bytefense OS

set -e

BYTEFENSE_HOME="/opt/bytefense"
BYTEFENSE_USER="bytefense"

echo "🛡️ Instalando nodo clonado de Bytefense OS..."

# Verificar permisos de root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Este script debe ejecutarse como root"
   exit 1
fi

# Instalar dependencias básicas
apt update
apt install -y curl wget git ufw sqlite3 lighttpd python3 python3-pip \
    wireguard wireguard-tools qrencode dnsutils net-tools htop fail2ban

# Instalar Pi-hole
curl -sSL https://install.pi-hole.net | bash /dev/stdin --unattended

# Crear usuario del sistema
if ! id "$BYTEFENSE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$BYTEFENSE_HOME" "$BYTEFENSE_USER"
fi

# Crear estructura y copiar archivos
mkdir -p "$BYTEFENSE_HOME"/{intel,honey,wireguard,logs}
cp -r bin feeds web docs system "$BYTEFENSE_HOME/"
chown -R "$BYTEFENSE_USER":"$BYTEFENSE_USER" "$BYTEFENSE_HOME"

# Hacer ejecutables los scripts
chmod +x "$BYTEFENSE_HOME/bin/"*

# Instalar servicios
cp "$BYTEFENSE_HOME/system/"*.service /etc/systemd/system/
systemctl daemon-reload

# Configurar firewall
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 8080/tcp
ufw allow 8081/tcp
ufw allow 51820/udp
ufw --force enable

# Crear enlace simbólico
ln -sf "$BYTEFENSE_HOME/bin/bytefense-ctl" /usr/local/bin/bytefense-ctl

# Inicializar base de datos
sqlite3 "$BYTEFENSE_HOME/intel/threats.db" < "$BYTEFENSE_HOME/system/schema.sql"

# Habilitar servicios
systemctl enable bytefense-dashboard bytefense-watch
systemctl start bytefense-dashboard bytefense-watch

echo "✅ Nodo clonado instalado correctamente"
echo "⚙️ Ejecuta: bytefense-ctl init para configurar"
EOF

chmod +x "$CLONE_DIR/install-clone.sh"

# Crear archivo README
cat > "$CLONE_DIR/README.md" << EOF
# 🛡️ Bytefense OS - Nodo Clonado

Este es un nodo clonado de Bytefense OS creado el $(date).

## Instalación

1. Copia este directorio al nuevo sistema
2. Ejecuta como root: \`./install-clone.sh\`
3. Configura el nodo: \`bytefense-ctl init\`
4. Registra en nodo maestro: \`bytefense-ctl register <ip-maestro>\`

## Acceso

- Dashboard: http://IP:8080
- Pi-hole: http://IP:8081/admin

EOF

# Crear archivo comprimido
echo "📦 Creando archivo de clonación..."
tar -czf "bytefense-clone-$DATE.tar.gz" -C "$CLONE_DIR" .

echo "✅ Imagen de clonación creada: bytefense-clone-$DATE.tar.gz"
echo "📁 Tamaño: $(du -h bytefense-clone-$DATE.tar.gz | cut -f1)"
echo ""
echo "📋 Para instalar en nuevo nodo:"
echo "1. Copia el archivo .tar.gz al nuevo sistema"
echo "2. Extrae: tar -xzf bytefense-clone-$DATE.tar.gz"
echo "3. Ejecuta: sudo ./install-clone.sh"

# Limpiar directorio temporal
rm -rf "$CLONE_DIR"