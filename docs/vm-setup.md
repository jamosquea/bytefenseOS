# Configuración de VM para Bytefense OS

## Opción 1: Usar Vagrant (Recomendado para desarrollo)

### Requisitos
- VirtualBox 6.1+
- Vagrant 2.2+
- 4GB RAM disponible
- 20GB espacio en disco

### Instalación rápida

```bash
# Clonar o descargar el proyecto
cd bytefense

# Iniciar VM
vagrant up

# Acceder por SSH
vagrant ssh

# Ver estado del sistema
sudo bytefense-ctl status