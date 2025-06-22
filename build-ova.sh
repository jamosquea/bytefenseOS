#!/bin/bash

# Script para construir imagen .ova de Bytefense OS
# Requiere VirtualBox y Vagrant instalados

set -e

echo "=== Construyendo imagen .ova de Bytefense OS ==="

# Verificar dependencias
if ! command -v vagrant &> /dev/null; then
    echo "Error: Vagrant no está instalado"
    exit 1
fi

if ! command -v VBoxManage &> /dev/null; then
    echo "Error: VirtualBox no está instalado"
    exit 1
fi

# Limpiar VMs anteriores
echo "Limpiando VMs anteriores..."
vagrant destroy -f 2>/dev/null || true

# Construir VM
echo "Construyendo VM con Vagrant..."
vagrant up

# Obtener nombre de la VM
VM_NAME="Bytefense-OS"
echo "Preparando VM para exportación..."

# Detener la VM
vagrant halt

# Limpiar y optimizar la VM
echo "Optimizando VM..."
VBoxManage modifyvm "$VM_NAME" --memory 1024
VBoxManage modifyvm "$VM_NAME" --cpus 1

# Exportar a .ova
OVA_FILE="bytefense-os-$(date +%Y%m%d).ova"
echo "Exportando a $OVA_FILE..."
VBoxManage export "$VM_NAME" --output "$OVA_FILE" \
    --manifest \
    --vsys 0 \
    --product "Bytefense OS" \
    --producturl "https://github.com/bytefense/bytefense-os" \
    --vendor "Bytefense Project" \
    --version "1.0.0" \
    --description "Sistema de defensa digital distribuido basado en Raspberry Pi y Linux"

echo "=== Imagen .ova creada: $OVA_FILE ==="
echo "Tamaño: $(du -h "$OVA_FILE" | cut -f1)"
echo ""
echo "Para usar la imagen:"
echo "1. Importar en VirtualBox: File > Import Appliance"
echo "2. Configurar red como 'Host-only' o 'Bridged'"
echo "3. Iniciar la VM"
echo "4. Acceder al dashboard en http://IP_DE_LA_VM:8080"
echo ""
echo "Credenciales por defecto:"
echo "  Usuario: vagrant / Password: vagrant"
echo "  Usuario Bytefense: bytefense / Password: bytefense123"
echo "  Pi-hole admin: bytefense123"