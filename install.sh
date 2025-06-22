#!/bin/bash
# Bytefense OS - Instalador Modular
# Compatible con Raspberry Pi 5, VM y servidores Linux

set -e  # Detener en cualquier error
set -u  # Detener en variables no definidas
set -o pipefail  # Detener en errores de pipe

BYTEFENSE_HOME="/opt/bytefense"
BYTEFENSE_USER="bytefense"
LOG_FILE="/var/log/bytefense-install.log"
MODULES_DIR="$BYTEFENSE_HOME/modules"
GITHUB_BASE="https://raw.githubusercontent.com/bytefense/bytefense-os/main"

# Módulos disponibles
AVAILABLE_MODULES=("core" "pi-hole" "vpn" "intel" "honeypot" "reticularium")
SELECTED_MODULES=()

echo "🛡️  Instalador Modular de Bytefense OS"
echo "📝 Log de instalación: $LOG_FILE"

# Función de logging mejorada
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función para manejo de errores
error_exit() {
    log "❌ ERROR: $1"
    exit 1
}

# Verificar permisos de root
if [[ $EUID -ne 0 ]]; then
   error_exit "Este script debe ejecutarse como root (sudo ./install.sh)"
fi

# Verificar conectividad a internet
check_connectivity() {
    log "🌐 Verificando conectividad a internet..."
    if ! ping -c 1 google.com &> /dev/null; then
        error_exit "No hay conectividad a internet. Verifica tu conexión."
    fi
    log "✅ Conectividad verificada"
}

# Función para descargar archivos de forma segura
safe_download() {
    local url="$1"
    local output="$2"
    local description="$3"
    
    log "📥 Descargando $description..."
    
    # Verificar que la URL responde
    if ! curl -f -s -I "$url" > /dev/null; then
        error_exit "No se puede acceder a $url"
    fi
    
    # Descargar con verificación
    if ! curl -f -s -L "$url" -o "$output"; then
        error_exit "Error al descargar $description desde $url"
    fi
    
    # Verificar que el archivo se descargó correctamente
    if [[ ! -f "$output" ]] || [[ ! -s "$output" ]]; then
        error_exit "El archivo descargado $output está vacío o no existe"
    fi
    
    log "✅ $description descargado correctamente"
}

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
else
    error_exit "No se puede detectar la distribución del sistema"
fi

log "🔍 Sistema detectado: $OS $VER"

# Verificar conectividad antes de continuar
check_connectivity

# Actualizar sistema con manejo de errores
log "📦 Actualizando repositorios..."
if ! apt update; then
    error_exit "Error al actualizar repositorios"
fi

if ! apt upgrade -y; then
    log "⚠️  Advertencia: Algunas actualizaciones fallaron, continuando..."
fi

# Instalar dependencias base (CORREGIDO: agregado qrencode y ufw)
log "🔧 Instalando dependencias base..."
if ! apt install -y curl wget git ufw qrencode sqlite3 python3 python3-pip \
    dnsutils net-tools htop fail2ban jq openssl; then
    error_exit "Error al instalar dependencias base"
fi

# Crear usuario del sistema con validación
log "👤 Creando usuario bytefense..."
if ! id "$BYTEFENSE_USER" &>/dev/null; then
    if ! useradd -r -s /bin/bash -d "$BYTEFENSE_HOME" "$BYTEFENSE_USER"; then
        error_exit "Error al crear usuario $BYTEFENSE_USER"
    fi
    log "✅ Usuario $BYTEFENSE_USER creado"
else
    log "ℹ️  Usuario $BYTEFENSE_USER ya existe"
fi

# Crear estructura de directorios base con validación
log "📁 Creando estructura de directorios..."
if ! mkdir -p "$BYTEFENSE_HOME"/{bin,feeds,intel,honey,wireguard,web,docs,system,logs,modules}; then
    error_exit "Error al crear estructura de directorios"
fi

if ! chown -R "$BYTEFENSE_USER":"$BYTEFENSE_USER" "$BYTEFENSE_HOME"; then
    error_exit "Error al cambiar propietario de $BYTEFENSE_HOME"
fi

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
    
    # Instalar dependencias Python con manejo de errores
    log "🐍 Instalando dependencias Python..."
    if ! pip3 install --upgrade pip; then
        error_exit "Error al actualizar pip"
    fi
    
    if ! pip3 install flask pyjwt bcrypt pyotp qrcode[pil] requests feedparser schedule; then
        error_exit "Error al instalar dependencias Python"
    fi
    
    # Descargar scripts desde GitHub de forma segura
    local scripts=("bytefense-api.py" "bytefense-ctl" "bytefense-alerts.py" "bytefense-auth.py")
    
    for script in "${scripts[@]}"; do
        safe_download "$GITHUB_BASE/bin/$script" "$BYTEFENSE_HOME/bin/$script" "script $script"
        chmod +x "$BYTEFENSE_HOME/bin/$script"
    done
    
    # Descargar archivos web
    safe_download "$GITHUB_BASE/web/index.html" "$BYTEFENSE_HOME/web/index.html" "dashboard web"
    safe_download "$GITHUB_BASE/system/schema.sql" "$BYTEFENSE_HOME/system/schema.sql" "esquema de base de datos"
    
    # Crear enlace simbólico con validación
    if ! ln -sf "$BYTEFENSE_HOME/bin/bytefense-ctl" /usr/local/bin/bytefense-ctl; then
        error_exit "Error al crear enlace simbólico para bytefense-ctl"
    fi
    
    # Configurar firewall básico con validación
    log "🔥 Configurando firewall..."
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
    
    # Instalar WireGuard con qrencode (YA CORREGIDO)
    if ! apt install -y wireguard wireguard-tools; then
        error_exit "Error al instalar WireGuard"
    fi
    
    # qrencode ya está instalado en dependencias base
    
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
if [[ -d "$BYTEFENSE_HOME/system" ]]; then
    cp "$BYTEFENSE_HOME/system/"*.service /etc/systemd/system/ 2>/dev/null || true
    systemctl daemon-reload
fi

# Habilitar servicios base
log "🚀 Habilitando servicios base..."
for service in bytefense-dashboard bytefense-watch; do
    if systemctl enable "$service" 2>/dev/null; then
        log "✅ Servicio $service habilitado"
        if systemctl start "$service" 2>/dev/null; then
            log "✅ Servicio $service iniciado"
        else
            log "⚠️  Advertencia: No se pudo iniciar $service"
        fi
    else
        log "⚠️  Advertencia: No se pudo habilitar $service"
    fi
done

# Habilitar firewall
if ! ufw --force enable; then
    log "⚠️  Advertencia: Error al habilitar firewall UFW"
fi

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

# Función para instalar módulo speedtest
install_speedtest_module() {
    log "🚀 Instalando módulo OpenSpeedTest..."
    
    # Instalar speedtest-cli
    if ! pip3 install speedtest-cli; then
        log "⚠️  Advertencia: No se pudo instalar speedtest-cli"
    fi
    
    # Descargar OpenSpeedTest
    SPEEDTEST_DIR="$BYTEFENSE_HOME/web/speedtest"
    mkdir -p "$SPEEDTEST_DIR"
    
    # Clonar OpenSpeedTest
    if ! git clone https://github.com/openspeedtest/Speed-Test.git "$SPEEDTEST_DIR"; then
        log "⚠️  Error al descargar OpenSpeedTest"
        return 1
    fi
    
    # Configurar permisos
    chown -R "$BYTEFENSE_USER":"$BYTEFENSE_USER" "$SPEEDTEST_DIR"
    
    # Crear servicio systemd
    cat > "/etc/systemd/system/bytefense-speedtest.service" << EOF
[Unit]
Description=Bytefense SpeedTest Monitor
After=network.target

[Service]
Type=simple
User=$BYTEFENSE_USER
WorkingDirectory=$BYTEFENSE_HOME
ExecStart=/usr/bin/python3 $BYTEFENSE_HOME/bin/bytefense-speedtest.py daemon
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF
    
    # Habilitar servicio
    systemctl daemon-reload
    systemctl enable bytefense-speedtest
    systemctl start bytefense-speedtest
    
    # Configurar nginx/lighttpd para servir OpenSpeedTest
    cat > "/etc/lighttpd/conf-available/50-speedtest.conf" << EOF
alias.url += ( "/speedtest" => "$SPEEDTEST_DIR" )
EOF
    
    lighttpd-enable-mod speedtest
    systemctl reload lighttpd
    
    log "✅ Módulo OpenSpeedTest instalado"
}

# Agregar speedtest a los módulos disponibles
AVAILABLE_MODULES=("core" "pi-hole" "vpn" "intel" "honeypot" "reticularium" "speedtest")

# En la función install_module, agregar:
case $module in
    "speedtest")
        install_speedtest_module
        ;;
esac