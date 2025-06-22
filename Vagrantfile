# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile para Bytefense OS
# Crea una VM Ubuntu con Bytefense OS preinstalado y configurado

Vagrant.configure("2") do |config|
  # Imagen base Ubuntu 22.04 LTS
  config.vm.box = "ubuntu/jammy64"
  config.vm.box_version = ">= 20220420.0.0"
  
  # Configuración de red
  config.vm.network "private_network", ip: "192.168.56.10"
  config.vm.network "forwarded_port", guest: 8080, host: 8080, host_ip: "127.0.0.1"
  config.vm.network "forwarded_port", guest: 80, host: 8081, host_ip: "127.0.0.1"
  config.vm.network "forwarded_port", guest: 53, host: 5353, protocol: "udp"
  config.vm.network "forwarded_port", guest: 51820, host: 51820, protocol: "udp"
  
  # Configuración de la VM
  config.vm.provider "virtualbox" do |vb|
    vb.name = "Bytefense-OS"
    vb.memory = "2048"
    vb.cpus = 2
    vb.gui = false
    
    # Configuraciones adicionales para mejor rendimiento
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    vb.customize ["modifyvm", :id, "--accelerate3d", "off"]
    vb.customize ["modifyvm", :id, "--vram", "16"]
  end
  
  # Hostname de la VM
  config.vm.hostname = "bytefense-node"
  
  # Sincronización de carpetas
  config.vm.synced_folder ".", "/vagrant", disabled: false
  
  # Script de aprovisionamiento
  config.vm.provision "shell", inline: <<-SHELL
    set -e
    
    echo "=== Iniciando instalación de Bytefense OS ==="
    
    # Actualizar sistema
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get upgrade -y
    
    # Instalar dependencias básicas
    apt-get install -y curl wget git sqlite3 ufw python3 python3-pip \
                       wireguard wireguard-tools qrencode dnsutils \
                       net-tools htop nano vim sudo systemd
    
    # Crear usuario bytefense si no existe
    if ! id "bytefense" &>/dev/null; then
        useradd -m -s /bin/bash -G sudo bytefense
        echo "bytefense:bytefense123" | chpasswd
        echo "bytefense ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/bytefense
    fi
    
    # Copiar archivos del proyecto
    echo "Copiando archivos de Bytefense OS..."
    mkdir -p /opt/bytefense/{bin,web,system,feeds,logs}
    
    # Copiar binarios
    cp /vagrant/bin/* /opt/bytefense/bin/
    chmod +x /opt/bytefense/bin/*
    
    # Copiar archivos web
    cp /vagrant/web/* /opt/bytefense/web/
    
    # Copiar archivos del sistema
    cp /vagrant/system/* /opt/bytefense/system/
    
    # Copiar feeds
    cp /vagrant/feeds/* /opt/bytefense/feeds/
    
    # Crear enlaces simbólicos
    ln -sf /opt/bytefense/bin/bytefense-ctl /usr/local/bin/bytefense-ctl
    
    # Configurar servicios systemd
    cp /opt/bytefense/system/*.service /etc/systemd/system/
    systemctl daemon-reload
    
    # Inicializar base de datos
    echo "Inicializando base de datos..."
    sqlite3 /opt/bytefense/system/bytefense.db < /opt/bytefense/system/schema.sql
    chown -R bytefense:bytefense /opt/bytefense
    
    # Configurar UFW
    echo "Configurando firewall..."
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 8080/tcp  # Dashboard
    ufw allow 80/tcp    # Pi-hole
    ufw allow 53/udp    # DNS
    ufw allow 51820/udp # WireGuard
    ufw --force enable
    
    # Instalar Pi-hole
    echo "Instalando Pi-hole..."
    curl -sSL https://install.pi-hole.net | bash /dev/stdin --unattended \
        --admin-password="bytefense123" \
        --pihole-interface="eth1" \
        --pihole-dns-1="1.1.1.1" \
        --pihole-dns-2="8.8.8.8" \
        --query-logging=true \
        --install-web-server=true \
        --install-web-interface=true \
        --lighttpd-enabled=true
    
    # Configurar WireGuard
    echo "Configurando WireGuard..."
    mkdir -p /etc/wireguard
    
    # Generar claves del servidor
    wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key
    chmod 600 /etc/wireguard/server_private.key
    
    # Crear configuración del servidor
    cat > /etc/wireguard/wg0.conf << EOF
[Interface]
PrivateKey = $(cat /etc/wireguard/server_private.key)
Address = 10.8.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

EOF
    
    # Habilitar IP forwarding
    echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
    sysctl -p
    
    # Habilitar servicios
    echo "Habilitando servicios..."
    systemctl enable bytefense-dashboard
    systemctl enable bytefense-watch
    systemctl enable wg-quick@wg0
    
    # Iniciar servicios
    systemctl start bytefense-dashboard
    systemctl start bytefense-watch
    systemctl start wg-quick@wg0
    
    # Inicializar nodo
    echo "Inicializando nodo Bytefense..."
    sudo -u bytefense /opt/bytefense/bin/bytefense-ctl init --name="vagrant-node" --type="master"
    
    # Crear cliente WireGuard de ejemplo
    echo "Creando cliente WireGuard de ejemplo..."
    sudo -u bytefense /opt/bytefense/bin/bytefense-ctl wireguard add-client --name="test-client"
    
    # Mostrar información de acceso
    echo ""
    echo "=== Bytefense OS instalado correctamente ==="
    echo "Dashboard web: http://192.168.56.10:8080"
    echo "Pi-hole admin: http://192.168.56.10/admin (password: bytefense123)"
    echo "SSH: vagrant@192.168.56.10 (password: vagrant)"
    echo "Usuario Bytefense: bytefense (password: bytefense123)"
    echo ""
    echo "Para conectar por WireGuard, ejecuta:"
    echo "  vagrant ssh"
    echo "  sudo bytefense-ctl wireguard show-client test-client"
    echo ""
    
  SHELL
  
  # Mensaje final
  config.vm.post_up_message = <<-MSG
    ╔══════════════════════════════════════════════════════════════╗
    ║                    BYTEFENSE OS READY                       ║
    ╠══════════════════════════════════════════════════════════════╣
    ║ Dashboard:    http://localhost:8080                         ║
    ║ Pi-hole:      http://localhost:8081/admin                   ║
    ║ SSH:          vagrant ssh                                    ║
    ║                                                              ║
    ║ Credenciales:                                                ║
    ║   Pi-hole admin: bytefense123                               ║
    ║   Usuario bytefense: bytefense123                           ║
    ║                                                              ║
    ║ Comandos útiles:                                             ║
    ║   vagrant ssh -c "sudo bytefense-ctl status"                ║
    ║   vagrant ssh -c "sudo bytefense-ctl wireguard show-client test-client" ║
    ╚══════════════════════════════════════════════════════════════╝
  MSG
end