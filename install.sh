#!/bin/bash
# Bytefense OS - Instalador Modular
# Compatible con Raspberry Pi 5, VM y servidores Linux

set -e

BYTEFENSE_HOME="/opt/bytefense"
BYTEFENSE_USER="bytefense"
LOG_FILE="/var/log/bytefense-install.log"
MODULES_DIR="$BYTEFENSE_HOME/modules"

# Módulos disponibles
AVAILABLE_MODULES=("core" "pi-hole" "vpn" "intel" "honeypot" "reticularium")
SELECTED_MODULES=()

echo "🛡️  Instalador Modular de Bytefense OS"
echo "📝 Log de instalación: $LOG_FILE"

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Verificar permisos de root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Este script debe ejecutarse como root (sudo ./install.sh)"
   exit 1
fi

# Función para mostrar ayuda
show_help() {
    cat << EOF
🛡️  Bytefense OS - Instalador Modular

Uso: ./install.sh [opciones]

Opciones:
  --modules=<lista>    Módulos a instalar (separados por coma)
  --interactive        Modo interactivo para seleccionar módulos
  --all               Instalar todos los módulos
  --minimal           Solo instalar módulo core
  --help              Mostrar esta ayuda

Módulos disponibles:
  core        - Sistema base (obligatorio)
  pi-hole     - Filtrado DNS y bloqueo de anuncios
  vpn         - Servidor WireGuard VPN
  intel       - Sistema de inteligencia de amenazas
  honeypot    - Trampa para atacantes
  reticularium - Red distribuida de nodos

Ejemplos:
  ./install.sh --modules=core,pi-hole,vpn
  ./install.sh --interactive
  ./install.sh --all
  ./install.sh --minimal

EOF
}

# Procesar argumentos de línea de comandos
while [[ $# -gt 0 ]]; do
    case $1 in
        --modules=*)
            IFS=',' read -ra SELECTED_MODULES <<< "${1#*=}"
            shift
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        --all)
            SELECTED_MODULES=("${AVAILABLE_MODULES[@]}")
            shift
            ;;
        --minimal)
            SELECTED_MODULES=("core")
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "❌ Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Modo interactivo si no se especificaron módulos
if [ ${#SELECTED_MODULES[@]} -eq 0 ] && [ "$INTERACTIVE" != "true" ]; then
    echo "🤔 No se especificaron módulos. Iniciando modo interactivo..."
    INTERACTIVE=true
fi

if [ "$INTERACTIVE" = "true" ]; then
    echo ""
    echo "📦 Selecciona los módulos a instalar:"
    echo "   (El módulo 'core' es obligatorio y se instalará automáticamente)"
    echo ""
    
    SELECTED_MODULES=("core")
    
    for module in "${AVAILABLE_MODULES[@]}"; do
        if [ "$module" != "core" ]; then
            echo -n "¿Instalar $module? [y/N]: "
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                SELECTED_MODULES+=("$module")
            fi
        fi
    done
fi

# Asegurar que core esté incluido
if [[ ! " ${SELECTED_MODULES[@]} " =~ " core " ]]; then
    SELECTED_MODULES=("core" "${SELECTED_MODULES[@]}")
fi

echo ""
log "📋 Módulos seleccionados: ${SELECTED_MODULES[*]}"
echo ""

# Detectar distribución
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
fi

log "🔍 Sistema detectado: $OS $VER"

# Actualizar sistema
log "📦 Actualizando repositorios..."
apt update && apt upgrade -y

# Instalar dependencias base
log "🔧 Instalando dependencias base..."
apt install -y curl wget git ufw sqlite3 python3 python3-pip \
    dnsutils net-tools htop fail2ban jq openssl

# Crear usuario del sistema
log "👤 Creando usuario bytefense..."
if ! id "$BYTEFENSE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$BYTEFENSE_HOME" "$BYTEFENSE_USER"
fi

# Crear estructura de directorios base
log "📁 Creando estructura de directorios..."
mkdir -p "$BYTEFENSE_HOME"/{bin,feeds,intel,honey,wireguard,web,docs,system,logs,modules}
chown -R "$BYTEFENSE_USER":"$BYTEFENSE_USER" "$BYTEFENSE_HOME"

# Instalar módulos seleccionados
for module in "${SELECTED_MODULES[@]}"; do
    log "🔧 Instalando módulo: $module"
    install_module "$module"
done

# Función para instalar módulos
install_module() {
    local module=$1
    case $module in
        "core")
            install_core_module
            ;;
        "pi-hole")
            install_pihole_module
            ;;
        "vpn")
            install_vpn_module
            ;;
        "intel")
            install_intel_module
            ;;
        "honeypot")
            install_honeypot_module
            ;;
        "reticularium")
            install_reticularium_module
            ;;
        *)
            log "❌ Módulo desconocido: $module"
            ;;
    esac
}

# Módulo Core (obligatorio)
# Función para instalar módulo core
install_core_module() {
    log "📦 Instalando módulo core..."
    
    # Crear directorios base
    mkdir -p "$BYTEFENSE_HOME"/{bin,web,system,logs,intel}
    mkdir -p "$MODULES_DIR"
    
    # Instalar dependencias Python
    log "🐍 Instalando dependencias Python..."
    pip3 install --upgrade pip
    pip3 install flask pyjwt bcrypt pyotp qrcode[pil] requests feedparser schedule
    
    # Copiar archivos base
    cp -r bin/* "$BYTEFENSE_HOME/bin/" 2>/dev/null || true
    cp -r web/* "$BYTEFENSE_HOME/web/" 2>/dev/null || true
    cp -r system/* "$BYTEFENSE_HOME/system/" 2>/dev/null || true
    cp -r docs/* "$BYTEFENSE_HOME/docs/" 2>/dev/null || true
    
    # Hacer ejecutables los scripts
    chmod +x "$BYTEFENSE_HOME/bin/"*
    
    # Crear enlace simbólico
    ln -sf "$BYTEFENSE_HOME/bin/bytefense-ctl" /usr/local/bin/bytefense-ctl
    
    # Configurar firewall básico
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 8080/tcp  # Dashboard Bytefense
    
    # Marcar módulo como instalado
    touch "$MODULES_DIR/core.installed"
    log "✅ Módulo core instalado"
}

# Módulo Pi-hole
install_pihole_module() {
    log "🕳️  Instalando módulo PI-HOLE..."
    
    # Instalar Pi-hole
    curl -sSL https://install.pi-hole.net | bash /dev/stdin --unattended
    
    # Configurar firewall
    ufw allow 8081/tcp  # Pi-hole web
    ufw allow 53/tcp    # DNS
    ufw allow 53/udp    # DNS
    
    # Configurar integración con Bytefense
    cat > "$BYTEFENSE_HOME/modules/pihole-integration.sh" << 'EOF'
#!/bin/bash
# Integración Pi-hole con Bytefense
PIHOLE_LOG="/var/log/pihole.log"
BYTEFENSE_DB="/opt/bytefense/intel/threats.db"

# Función para sincronizar listas bloqueadas
sync_blocklists() {
    # Agregar IPs bloqueadas de Bytefense a Pi-hole
    sqlite3 "$BYTEFENSE_DB" "SELECT ip FROM blocked_ips;" | while read ip; do
        pihole -b "$ip" >/dev/null 2>&1
    done
}

# Ejecutar sincronización
sync_blocklists
EOF
    
    chmod +x "$BYTEFENSE_HOME/modules/pihole-integration.sh"
    
    # Marcar módulo como instalado
    echo "pi-hole" > "$MODULES_DIR/pihole.installed"
    
    log "✅ Módulo PI-HOLE instalado"
}

# Módulo VPN
install_vpn_module() {
    log "🔐 Instalando módulo VPN..."
    
    # Instalar WireGuard
    apt install -y wireguard wireguard-tools qrencode
    
    # Configurar firewall
    ufw allow 51820/udp # WireGuard
    
    # Crear script de configuración VPN
    cat > "$BYTEFENSE_HOME/modules/vpn-setup.sh" << 'EOF'
#!/bin/bash
# Configuración automática de WireGuard
WG_DIR="/opt/bytefense/wireguard"
WG_CONFIG="/etc/wireguard/wg0.conf"

# Generar claves del servidor
if [ ! -f "$WG_DIR/server_private.key" ]; then
    mkdir -p "$WG_DIR"
    wg genkey | tee "$WG_DIR/server_private.key" | wg pubkey > "$WG_DIR/server_public.key"
    chmod 600 "$WG_DIR/server_private.key"
fi

# Configurar servidor WireGuard
cat > "$WG_CONFIG" << EOL
[Interface]
PrivateKey = $(cat $WG_DIR/server_private.key)
Address = 10.8.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

EOL

# Habilitar IP forwarding
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
sysctl -p

# Habilitar servicio
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0
EOF
    
    chmod +x "$BYTEFENSE_HOME/modules/vpn-setup.sh"
    "$BYTEFENSE_HOME/modules/vpn-setup.sh"
    
    # Marcar módulo como instalado
    echo "vpn" > "$MODULES_DIR/vpn.installed"
    
    log "✅ Módulo VPN instalado"
}

# Módulo Intel
install_intel_module() {
    log "🧠 Instalando módulo INTEL..."
    
    # Instalar dependencias adicionales
    pip3 install requests feedparser
    
    # Copiar feeds de amenazas
    cp -r feeds/* "$BYTEFENSE_HOME/feeds/" 2>/dev/null || true
    
    # Inicializar base de datos
    sqlite3 "$BYTEFENSE_HOME/intel/threats.db" < "$BYTEFENSE_HOME/system/schema.sql"
    
    # Crear script de actualización de inteligencia
    cat > "$BYTEFENSE_HOME/modules/intel-updater.sh" << 'EOF'
#!/bin/bash
# Actualizador automático de inteligencia de amenazas
INTEL_DIR="/opt/bytefense/intel"
FEEDS_DIR="/opt/bytefense/feeds"
DB_FILE="$INTEL_DIR/threats.db"

# Fuentes de inteligencia
THREAT_FEEDS=(
    "https://rules.emergingthreats.net/blockrules/compromised-ips.txt"
    "https://www.spamhaus.org/drop/drop.txt"
    "https://reputation.alienvault.com/reputation.data"
)

# Actualizar feeds
for feed in "${THREAT_FEEDS[@]}"; do
    echo "Descargando: $feed"
    wget -q -O "/tmp/$(basename $feed)" "$feed" || continue
    
    # Procesar y agregar a base de datos
    grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' "/tmp/$(basename $feed)" | while read ip; do
        sqlite3 "$DB_FILE" "INSERT OR IGNORE INTO blocked_ips (ip, reason, created_at) VALUES ('$ip', 'threat_feed', datetime('now'));"
    done
done

echo "Inteligencia de amenazas actualizada"
EOF
    
    chmod +x "$BYTEFENSE_HOME/modules/intel-updater.sh"
    
    # Configurar cron para actualizaciones automáticas
    echo "0 */6 * * * $BYTEFENSE_HOME/modules/intel-updater.sh" | crontab -u "$BYTEFENSE_USER" -
    
    # Marcar módulo como instalado
    echo "intel" > "$MODULES_DIR/intel.installed"
    
    log "✅ Módulo INTEL instalado"
}

# Módulo Honeypot
install_honeypot_module() {
    log "🍯 Instalando módulo HONEYPOT..."
    
    # Instalar dependencias
    apt install -y python3-twisted
    pip3 install twisted
    
    # Crear honeypot SSH
    cat > "$BYTEFENSE_HOME/modules/ssh-honeypot.py" << 'EOF'
#!/usr/bin/env python3
import socket
import threading
import sqlite3
import datetime
import logging

class SSHHoneypot:
    def __init__(self, port=2222):
        self.port = port
        self.db_path = '/opt/bytefense/intel/threats.db'
        
    def log_attempt(self, ip, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (event_type, source_ip, details, timestamp) VALUES (?, ?, ?, ?)",
            ('honeypot_ssh', ip, f'user:{username} pass:{password}', datetime.datetime.now())
        )
        conn.commit()
        conn.close()
        
    def handle_connection(self, conn, addr):
        try:
            conn.send(b'SSH-2.0-OpenSSH_7.4\r\n')
            data = conn.recv(1024).decode('utf-8', errors='ignore')
            
            # Simular intercambio SSH básico
            conn.send(b'\x00\x00\x00\x0c\x0a\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            
            # Log del intento
            self.log_attempt(addr[0], 'unknown', 'unknown')
            
        except Exception as e:
            pass
        finally:
            conn.close()
            
    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port))
        sock.listen(5)
        
        print(f"SSH Honeypot iniciado en puerto {self.port}")
        
        while True:
            conn, addr = sock.accept()
            thread = threading.Thread(target=self.handle_connection, args=(conn, addr))
            thread.start()

if __name__ == '__main__':
    honeypot = SSHHoneypot()
    honeypot.start()
EOF
    
    chmod +x "$BYTEFENSE_HOME/modules/ssh-honeypot.py"
    
    # Crear servicio systemd para honeypot
    cat > "/etc/systemd/system/bytefense-honeypot.service" << EOF
[Unit]
Description=Bytefense SSH Honeypot
After=network.target

[Service]
Type=simple
User=$BYTEFENSE_USER
ExecStart=/usr/bin/python3 $BYTEFENSE_HOME/modules/ssh-honeypot.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    # Configurar firewall
    ufw allow 2222/tcp  # Honeypot SSH
    
    # Habilitar servicio
    systemctl daemon-reload
    systemctl enable bytefense-honeypot
    systemctl start bytefense-honeypot
    
    # Marcar módulo como instalado
    echo "honeypot" > "$MODULES_DIR/honeypot.installed"
    
    log "✅ Módulo HONEYPOT instalado"
}

# Módulo Reticularium
install_reticularium_module() {
    log "🕸️  Instalando módulo RETICULARIUM..."
    
    # Instalar dependencias para red distribuida
    pip3 install flask requests schedule
    
    # Crear script de red distribuida
    cat > "$BYTEFENSE_HOME/modules/reticularium-node.py" << 'EOF'
#!/usr/bin/env python3
import requests
import json
import time
import threading
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

class ReticulariumNode:
    def __init__(self):
        self.node_id = self.get_node_id()
        self.peers = []
        self.db_path = '/opt/bytefense/intel/threats.db'
        
    def get_node_id(self):
        try:
            with open('/opt/bytefense/system/bytefense.conf', 'r') as f:
                for line in f:
                    if line.startswith('NODE_ID='):
                        return line.split('=')[1].strip().strip('"')
        except:
            return 'unknown'
            
    def sync_threats(self):
        """Sincronizar amenazas con otros nodos"""
        local_threats = self.get_local_threats()
        
        for peer in self.peers:
            try:
                response = requests.post(f'http://{peer}:8082/api/threats/sync', 
                                       json={'threats': local_threats}, timeout=5)
                if response.status_code == 200:
                    remote_threats = response.json().get('threats', [])
                    self.update_local_threats(remote_threats)
            except:
                continue
                
    def get_local_threats(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ip, reason FROM blocked_ips WHERE created_at > datetime('now', '-24 hours')")
        threats = [{'ip': row[0], 'reason': row[1]} for row in cursor.fetchall()]
        conn.close()
        return threats
        
    def update_local_threats(self, threats):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for threat in threats:
            cursor.execute(
                "INSERT OR IGNORE INTO blocked_ips (ip, reason, created_at) VALUES (?, ?, datetime('now'))",
                (threat['ip'], f"reticularium:{threat['reason']}")
            )
        conn.commit()
        conn.close()

node = ReticulariumNode()

@app.route('/api/threats/sync', methods=['POST'])
def sync_threats():
    remote_threats = request.json.get('threats', [])
    node.update_local_threats(remote_threats)
    local_threats = node.get_local_threats()
    return jsonify({'threats': local_threats})

@app.route('/api/peers', methods=['GET'])
def get_peers():
    return jsonify({'peers': node.peers})

@app.route('/api/peers', methods=['POST'])
def add_peer():
    peer = request.json.get('peer')
    if peer and peer not in node.peers:
        node.peers.append(peer)
    return jsonify({'status': 'ok'})

def periodic_sync():
    while True:
        time.sleep(300)  # Sincronizar cada 5 minutos
        node.sync_threats()

if __name__ == '__main__':
    # Iniciar hilo de sincronización
    sync_thread = threading.Thread(target=periodic_sync, daemon=True)
    sync_thread.start()
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=8082)
EOF
    
    chmod +x "$BYTEFENSE_HOME/modules/reticularium-node.py"
    
    # Crear servicio systemd
    cat > "/etc/systemd/system/bytefense-reticularium.service" << EOF
[Unit]
Description=Bytefense Reticularium Node
After=network.target

[Service]
Type=simple
User=$BYTEFENSE_USER
ExecStart=/usr/bin/python3 $BYTEFENSE_HOME/modules/reticularium-node.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    # Configurar firewall
    ufw allow 8082/tcp  # Reticularium API
    
    # Habilitar servicio
    systemctl daemon-reload
    systemctl enable bytefense-reticularium
    systemctl start bytefense-reticularium
    
    # Marcar módulo como instalado
    echo "reticularium" > "$MODULES_DIR/reticularium.installed"
    
    log "✅ Módulo RETICULARIUM instalado"
}

# Configurar servicios systemd base
log "⚙️  Configurando servicios systemd..."
cp "$BYTEFENSE_HOME/system/"*.service /etc/systemd/system/ 2>/dev/null || true
systemctl daemon-reload

# Habilitar servicios base
log "🚀 Habilitando servicios base..."
systemctl enable bytefense-dashboard 2>/dev/null || true
systemctl enable bytefense-watch 2>/dev/null || true
systemctl start bytefense-dashboard 2>/dev/null || true
systemctl start bytefense-watch 2>/dev/null || true

# Habilitar firewall
ufw --force enable

log "✅ Instalación modular completada!"
echo ""
echo "🛡️  Bytefense OS instalado con módulos: ${SELECTED_MODULES[*]}"
echo "📊 Dashboard: http://$(hostname -I | awk '{print $1}'):8080"

# Mostrar información específica de módulos instalados
for module in "${SELECTED_MODULES[@]}"; do
    case $module in
        "pi-hole")
            echo "🕳️  Pi-hole: http://$(hostname -I | awk '{print $1}'):8081/admin"
            ;;
        "vpn")
            echo "🔐 WireGuard: Puerto 51820/UDP configurado"
            ;;
        "honeypot")
            echo "🍯 Honeypot SSH: Puerto 2222/TCP activo"
            ;;
        "reticularium")
            echo "🕸️  Reticularium: Puerto 8082/TCP para sincronización"
            ;;
    esac
done

echo ""
echo "⚙️  Configuración inicial: sudo bytefense-ctl init"
echo "📖 Consulta la documentación en $BYTEFENSE_HOME/docs/"
echo "📦 Módulos instalados en: $MODULES_DIR"