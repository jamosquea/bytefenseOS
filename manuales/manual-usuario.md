# 👤 Manual del Usuario - Bytefense OS 
 
## 🚀 Instalación Rápida 
 
### Requisitos del Sistema 
 
- **SO**: Ubuntu 20.04+ / Debian 11+ / Raspberry Pi OS 
- **RAM**: Mínimo 2GB (Recomendado 4GB) 
- **Almacenamiento**: 8GB libres 
- **Red**: Conexión a Internet para actualizaciones 
 
### Instalación Automática 
 
```bash 
# Descargar e instalar 
wget -O install.sh https://raw.githubusercontent.com/bytefense/bytefense-os/main/install.sh 
chmod +x install.sh 
sudo ./install.sh --all 
``` 
 
### Configuración Inicial 
 
```bash 
# Inicializar nodo 
sudo bytefense-ctl init 
 
# Verificar estado 
sudo bytefense-ctl status 
``` 
