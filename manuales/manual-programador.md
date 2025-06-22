# 📚 Manual del Programador - Bytefense OS 
 
## 🎯 Introducción 
 
Bytefense OS es un sistema de defensa digital distribuida diseñado para proteger redes domésticas y empresariales. Este manual técnico está dirigido a desarrolladores que necesiten entender, modificar o extender el sistema. 
 
## 🏗️ Arquitectura del Sistema 
 
### Componentes Principales 
 
1. **Core System** (`/opt/bytefense/`) 
   - Sistema base con SQLite como base de datos 
   - API REST para comunicación entre componentes 
   - Panel web de administración 
 
2. **Módulos Disponibles** 
   - `core`: Sistema base (obligatorio) 
   - `pi-hole`: Filtrado DNS y bloqueo de anuncios 
   - `vpn`: Servidor WireGuard VPN 
   - `intel`: Sistema de inteligencia de amenazas 
   - `honeypot`: Trampa para atacantes 
   - `reticularium`: Red distribuida de nodos 
 
### Estructura de Directorios 
 
```text 
/opt/bytefense/ 
├── bin/                    # Ejecutables principales 
│   ├── bytefense-api.py   # API REST (Puerto 8080) 
│   ├── bytefense-ctl      # Controlador principal 
│   ├── bytefense-watch    # Monitor de amenazas 
│   ├── bytefense-alerts.py # Sistema de alertas 
│   ├── bytefense-auth.py  # Autenticación JWT 
│   └── bytefense-health   # Monitor de salud 
├── system/                # Configuración del sistema 
│   ├── bytefense.db      # Base de datos SQLite 
│   ├── schema.sql        # Esquema de BD 
│   └── bytefense.conf    # Configuración principal 
├── web/                   # Interfaz web 
│   ├── index.html        # Dashboard principal 
│   └── reticularium.html # Panel de red distribuida 
├── modules/               # Módulos instalados 
└── intel/                # Inteligencia de amenazas 
``` 
