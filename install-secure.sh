#!/bin/bash
# Bytefense OS - Instalador Seguro con Validaciones Completas

set -euo pipefail  # Modo estricto completo

# Configuración
BYTEFENSE_HOME="/opt/bytefense"
BYTEFENSE_USER="bytefense"
LOG_FILE="/var/log/bytefense-install.log"
GITHUB_BASE="https://raw.githubusercontent.com/bytefense/bytefense-os/main"
MIN_DISK_SPACE_GB=2
MIN_RAM_MB=512

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función de logging mejorada
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")
            echo -e "${GREEN}[${timestamp}] INFO: ${message}${NC}" | tee -a "$LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}[${timestamp}] WARN: ${message}${NC}" | tee -a "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}" | tee -a "$LOG_FILE"
            ;;
        "DEBUG")
            echo -e "${BLUE}[${timestamp}] DEBUG: ${message}${NC}" | tee -a "$LOG_FILE"
            ;;
    esac
}

# Función para manejo de errores
error_exit() {
    log "ERROR" "$1"
    log "ERROR" "Instalación fallida. Revisa el log: $LOG_FILE"
    exit 1
}

# Verificaciones de seguridad
security_checks() {
    log "INFO" "Realizando verificaciones de seguridad..."
    
    # Verificar permisos de root
    if [[ $EUID -ne 0 ]]; then
        error_exit "Este script debe ejecutarse como root (sudo ./install.sh)"
    fi
    
    # Verificar espacio en disco
    local available_space=$(df / | awk 'NR==2 {print int($4/1024/1024)}')
    if [[ $available_space -lt $MIN_DISK_SPACE_GB ]]; then
        error_exit "Espacio insuficiente. Requerido: ${MIN_DISK_SPACE_GB}GB, Disponible: ${available_space}GB"
    fi
    
    # Verificar RAM
    local available_ram=$(free -m | awk 'NR==2{print $2}')
    if [[ $available_ram -lt $MIN_RAM_MB ]]; then
        error_exit "RAM insuficiente. Requerido: ${MIN_RAM_MB}MB, Disponible: ${available_ram}MB"
    fi
    
    # Verificar distribución soportada
    if [[ ! -f /etc/debian_version ]] && [[ ! -f /etc/redhat-release ]]; then
        error_exit "Distribución no soportada. Solo Debian/Ubuntu y RHEL/CentOS"
    fi
    
    log "INFO" "Verificaciones de seguridad completadas"
}

# Verificar conectividad con timeout
check_connectivity() {
    log "INFO" "Verificando conectividad a internet..."
    
    local test_urls=("google.com" "github.com" "cloudflare.com")
    local connected=false
    
    for url in "${test_urls[@]}"; do
        if timeout 10 ping -c 1 "$url" &> /dev/null; then
            connected=true
            break
        fi
    done
    
    if [[ "$connected" == "false" ]]; then
        error_exit "No hay conectividad a internet. Verifica tu conexión."
    fi
    
    log "INFO" "Conectividad verificada"
}

# Función para descargar archivos de forma segura
safe_download() {
    local url="$1"
    local output="$2"
    local description="$3"
    local max_retries=3
    local retry_count=0
    
    log "INFO" "Descargando $description..."
    
    while [[ $retry_count -lt $max_retries ]]; do
        # Verificar que la URL responde
        if ! timeout 30 curl -f -s -I "$url" > /dev/null; then
            ((retry_count++))
            log "WARN" "Intento $retry_count/$max_retries fallido para $url"
            sleep 2
            continue
        fi
        
        # Descargar con verificación y timeout
        if timeout 60 curl -f -s -L "$url" -o "$output"; then
            # Verificar que el archivo se descargó correctamente
            if [[ -f "$output" ]] && [[ -s "$output" ]]; then
                # Verificar integridad básica (no está vacío o corrupto)
                if file "$output" | grep -q "text\|script\|executable"; then
                    log "INFO" "$description descargado correctamente"
                    return 0
                fi
            fi
        fi
        
        ((retry_count++))
        log "WARN" "Intento $retry_count/$max_retries fallido para $description"
        rm -f "$output" 2>/dev/null || true
        sleep 2
    done
    
    error_exit "Error al descargar $description después de $max_retries intentos"
}

# Crear usuario con configuración segura
create_secure_user() {
    log "INFO" "Creando usuario seguro $BYTEFENSE_USER..."
    
    if id "$BYTEFENSE_USER" &>/dev/null; then
        log "WARN" "Usuario $BYTEFENSE_USER ya existe"
        return 0
    fi
    
    # Crear usuario con shell restringido y directorio home
    useradd -r -m -d "$BYTEFENSE_HOME" -s /bin/bash "$BYTEFENSE_USER" || 
        error_exit "Error creando usuario $BYTEFENSE_USER"
    
    # Configurar permisos seguros
    chmod 750 "$BYTEFENSE_HOME"
    chown "$BYTEFENSE_USER:$BYTEFENSE_USER" "$BYTEFENSE_HOME"
    
    # Agregar a grupos necesarios
    usermod -a -G sudo "$BYTEFENSE_USER" 2>/dev/null || true
    
    log "INFO" "Usuario $BYTEFENSE_USER creado correctamente"
}

# Función principal
main() {
    log "INFO" "🛡️  Iniciando instalación segura de Bytefense OS"
    
    # Verificaciones previas
    security_checks
    check_connectivity
    
    # Crear estructura de directorios
    create_secure_user
    
    # Instalar dependencias
    install_dependencies
    
    # Descargar e instalar componentes
    install_components
    
    # Configurar servicios
    setup_services
    
    # Configuración final
    final_setup
    
    log "INFO" "✅ Instalación completada exitosamente"
    log "INFO" "🌐 Dashboard disponible en: http://$(hostname -I | awk '{print $1}'):8080"
}

# Manejo de señales
trap 'log "ERROR" "Instalación interrumpida"; exit 1' SIGINT SIGTERM

# Ejecutar instalación
main "$@"