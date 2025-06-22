# 🛡️ Bytefense OS

**Sistema de Defensa Digital Distribuida**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-linux-lightgrey.svg)](https://github.com/jamosquea/bytefenseOS)

## 🎯 Descripción

Bytefense OS es un sistema de defensa digital distribuida diseñado para proteger redes domésticas y empresariales mediante:

- 🛡️ **Filtrado DNS** con Pi-hole
- 🔐 **VPN segura** con WireGuard  
- 📊 **Monitoreo de amenazas** en tiempo real
- 🔥 **Firewall inteligente** con UFW
- 🌐 **Panel de control web** intuitivo
- 🕸️ **Red distribuida** de nodos (Reticularium)

## 🚀 Instalación Rápida

### Requisitos del Sistema
- **SO**: Ubuntu 20.04+ / Debian 11+ / Raspberry Pi OS
- **RAM**: Mínimo 2GB (Recomendado 4GB)
- **Almacenamiento**: 8GB libres
- **Red**: Conexión a Internet

### Instalación Automática

```bash
# Clonar repositorio
git clone https://github.com/jamosquea/bytefenseOS.git
cd bytefenseOS

# Ejecutar instalador
sudo ./install.sh --all

# Configurar nodo
sudo bytefense-ctl init