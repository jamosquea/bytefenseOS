@echo off
chcp 65001 >nul
echo 🛡️  Generador de Manuales Bytefense OS
echo =====================================
echo.

REM Crear carpeta manuales
if not exist "manuales" (
    mkdir manuales
    echo ✅ Carpeta 'manuales' creada
) else (
    echo ⚠️  Carpeta 'manuales' ya existe
)

cd manuales

REM Generar Manual del Programador
echo 📝 Generando Manual del Programador...
echo # 📚 Manual del Programador - Bytefense OS > manual-programador.md
echo. >> manual-programador.md
echo ## 🎯 Introducción >> manual-programador.md
echo. >> manual-programador.md
echo Bytefense OS es un sistema de defensa digital distribuida diseñado para proteger redes domésticas y empresariales. Este manual técnico está dirigido a desarrolladores que necesiten entender, modificar o extender el sistema. >> manual-programador.md
echo. >> manual-programador.md
echo ## 🏗️ Arquitectura del Sistema >> manual-programador.md
echo. >> manual-programador.md
echo ### Componentes Principales >> manual-programador.md
echo. >> manual-programador.md
echo 1. **Core System** ^(`/opt/bytefense/`^) >> manual-programador.md
echo    - Sistema base con SQLite como base de datos >> manual-programador.md
echo    - API REST para comunicación entre componentes >> manual-programador.md
echo    - Panel web de administración >> manual-programador.md
echo. >> manual-programador.md
echo 2. **Módulos Disponibles** >> manual-programador.md
echo    - `core`: Sistema base ^(obligatorio^) >> manual-programador.md
echo    - `pi-hole`: Filtrado DNS y bloqueo de anuncios >> manual-programador.md
echo    - `vpn`: Servidor WireGuard VPN >> manual-programador.md
echo    - `intel`: Sistema de inteligencia de amenazas >> manual-programador.md
echo    - `honeypot`: Trampa para atacantes >> manual-programador.md
echo    - `reticularium`: Red distribuida de nodos >> manual-programador.md
echo. >> manual-programador.md
echo ### Estructura de Directorios >> manual-programador.md
echo. >> manual-programador.md
echo ```text >> manual-programador.md
echo /opt/bytefense/ >> manual-programador.md
echo ├── bin/                    # Ejecutables principales >> manual-programador.md
echo │   ├── bytefense-api.py   # API REST ^(Puerto 8080^) >> manual-programador.md
echo │   ├── bytefense-ctl      # Controlador principal >> manual-programador.md
echo │   ├── bytefense-watch    # Monitor de amenazas >> manual-programador.md
echo │   ├── bytefense-alerts.py # Sistema de alertas >> manual-programador.md
echo │   ├── bytefense-auth.py  # Autenticación JWT >> manual-programador.md
echo │   └── bytefense-health   # Monitor de salud >> manual-programador.md
echo ├── system/                # Configuración del sistema >> manual-programador.md
echo │   ├── bytefense.db      # Base de datos SQLite >> manual-programador.md
echo │   ├── schema.sql        # Esquema de BD >> manual-programador.md
echo │   └── bytefense.conf    # Configuración principal >> manual-programador.md
echo ├── web/                   # Interfaz web >> manual-programador.md
echo │   ├── index.html        # Dashboard principal >> manual-programador.md
echo │   └── reticularium.html # Panel de red distribuida >> manual-programador.md
echo ├── modules/               # Módulos instalados >> manual-programador.md
echo └── intel/                # Inteligencia de amenazas >> manual-programador.md
echo ``` >> manual-programador.md

REM Generar Manual del Usuario
echo 📝 Generando Manual del Usuario...
echo # 👤 Manual del Usuario - Bytefense OS > manual-usuario.md
echo. >> manual-usuario.md
echo ## 🚀 Instalación Rápida >> manual-usuario.md
echo. >> manual-usuario.md
echo ### Requisitos del Sistema >> manual-usuario.md
echo. >> manual-usuario.md
echo - **SO**: Ubuntu 20.04+ / Debian 11+ / Raspberry Pi OS >> manual-usuario.md
echo - **RAM**: Mínimo 2GB ^(Recomendado 4GB^) >> manual-usuario.md
echo - **Almacenamiento**: 8GB libres >> manual-usuario.md
echo - **Red**: Conexión a Internet para actualizaciones >> manual-usuario.md
echo. >> manual-usuario.md
echo ### Instalación Automática >> manual-usuario.md
echo. >> manual-usuario.md
echo ```bash >> manual-usuario.md
echo # Descargar e instalar >> manual-usuario.md
echo wget -O install.sh https://raw.githubusercontent.com/bytefense/bytefense-os/main/install.sh >> manual-usuario.md
echo chmod +x install.sh >> manual-usuario.md
echo sudo ./install.sh --all >> manual-usuario.md
echo ``` >> manual-usuario.md
echo. >> manual-usuario.md
echo ### Configuración Inicial >> manual-usuario.md
echo. >> manual-usuario.md
echo ```bash >> manual-usuario.md
echo # Inicializar nodo >> manual-usuario.md
echo sudo bytefense-ctl init >> manual-usuario.md
echo. >> manual-usuario.md
echo # Verificar estado >> manual-usuario.md
echo sudo bytefense-ctl status >> manual-usuario.md
echo ``` >> manual-usuario.md

REM Generar Manual de Servicio
echo 📝 Generando Manual de Servicio...
echo # ⚙️ Manual de Servicio - Bytefense OS > manual-servicio.md
echo. >> manual-servicio.md
echo ## 🔧 Configuración de Servicios >> manual-servicio.md
echo. >> manual-servicio.md
echo ### Servicios Systemd >> manual-servicio.md
echo. >> manual-servicio.md
echo Bytefense OS utiliza varios servicios systemd: >> manual-servicio.md
echo. >> manual-servicio.md
echo - `bytefense-api.service` - API REST principal >> manual-servicio.md
echo - `bytefense-watch.service` - Monitor de amenazas >> manual-servicio.md
echo - `bytefense-alerts.service` - Sistema de alertas >> manual-servicio.md
echo - `bytefense-dashboard.service` - Panel web >> manual-servicio.md
echo. >> manual-servicio.md
echo ### Comandos de Gestión >> manual-servicio.md
echo. >> manual-servicio.md
echo ```bash >> manual-servicio.md
echo # Iniciar servicios >> manual-servicio.md
echo sudo systemctl start bytefense-api >> manual-servicio.md
echo sudo systemctl start bytefense-watch >> manual-servicio.md
echo. >> manual-servicio.md
echo # Habilitar en arranque >> manual-servicio.md
echo sudo systemctl enable bytefense-api >> manual-servicio.md
echo sudo systemctl enable bytefense-watch >> manual-servicio.md
echo. >> manual-servicio.md
echo # Ver estado >> manual-servicio.md
echo sudo systemctl status bytefense-* >> manual-servicio.md
echo ``` >> manual-servicio.md

REM Generar Manual de Mantenimiento
echo 📝 Generando Manual de Mantenimiento...
echo # 🔧 Manual de Mantenimiento - Bytefense OS > manual-mantenimiento.md
echo. >> manual-mantenimiento.md
echo ## 💾 Procedimientos de Backup >> manual-mantenimiento.md
echo. >> manual-mantenimiento.md
echo ### Backup de Base de Datos >> manual-mantenimiento.md
echo. >> manual-mantenimiento.md
echo ```bash >> manual-mantenimiento.md
echo # Backup manual >> manual-mantenimiento.md
echo sudo sqlite3 /opt/bytefense/system/bytefense.db ".backup /backup/bytefense-$(date +%%Y%%m%%d).db" >> manual-mantenimiento.md
echo. >> manual-mantenimiento.md
echo # Backup automático ^(cron^) >> manual-mantenimiento.md
echo echo "0 2 * * * root sqlite3 /opt/bytefense/system/bytefense.db '.backup /backup/bytefense-$(date +%%Y%%m%%d).db'" ^| sudo tee -a /etc/crontab >> manual-mantenimiento.md
echo ``` >> manual-mantenimiento.md
echo. >> manual-mantenimiento.md
echo ### Backup de Configuración >> manual-mantenimiento.md
echo. >> manual-mantenimiento.md
echo ```bash >> manual-mantenimiento.md
echo # Backup completo de configuración >> manual-mantenimiento.md
echo sudo tar -czf /backup/bytefense-config-$(date +%%Y%%m%%d).tar.gz /opt/bytefense/system/ >> manual-mantenimiento.md
echo ``` >> manual-mantenimiento.md

REM Generar Resumen del Proyecto
echo 📝 Generando Resumen del Proyecto...
echo # 📊 Resumen del Proyecto - Bytefense OS > resumen-proyecto.md
echo. >> resumen-proyecto.md
echo ## 🎯 Objetivos del Proyecto >> resumen-proyecto.md
echo. >> resumen-proyecto.md
echo Bytefense OS es un sistema de defensa digital distribuida que tiene como objetivos: >> resumen-proyecto.md
echo. >> resumen-proyecto.md
echo 1. **Protección Proactiva**: Detectar y bloquear amenazas antes de que afecten la red >> resumen-proyecto.md
echo 2. **Facilidad de Uso**: Interfaz intuitiva para usuarios no técnicos >> resumen-proyecto.md
echo 3. **Escalabilidad**: Arquitectura modular que permite crecimiento >> resumen-proyecto.md
echo 4. **Distribución**: Red de nodos interconectados para mayor resistencia >> resumen-proyecto.md
echo. >> resumen-proyecto.md
echo ## 🛠️ Tecnologías Utilizadas >> resumen-proyecto.md
echo. >> resumen-proyecto.md
echo ### Backend >> resumen-proyecto.md
echo - **Python 3.8+**: Lenguaje principal >> resumen-proyecto.md
echo - **SQLite**: Base de datos embebida >> resumen-proyecto.md
echo - **HTTP Server**: API REST nativa >> resumen-proyecto.md
echo - **JWT**: Autenticación y autorización >> resumen-proyecto.md
echo. >> resumen-proyecto.md
echo ### Frontend >> resumen-proyecto.md
echo - **HTML5/CSS3**: Interfaz web >> resumen-proyecto.md
echo - **JavaScript**: Lógica del cliente >> resumen-proyecto.md
echo - **Chart.js**: Visualización de datos >> resumen-proyecto.md
echo. >> resumen-proyecto.md
echo ### Infraestructura >> resumen-proyecto.md
echo - **Systemd**: Gestión de servicios >> resumen-proyecto.md
echo - **UFW**: Firewall >> resumen-proyecto.md
echo - **WireGuard**: VPN >> resumen-proyecto.md
echo - **Pi-hole**: Filtrado DNS >> resumen-proyecto.md

echo ✅ Archivos Markdown generados exitosamente
echo.
echo 🔄 Verificando herramientas de conversión...

REM Verificar si Pandoc está instalado
pandoc --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Pandoc encontrado - Convirtiendo a PDF...
    pandoc manual-programador.md -o manual-programador.pdf
    pandoc manual-usuario.md -o manual-usuario.pdf
    pandoc manual-servicio.md -o manual-servicio.pdf
    pandoc manual-mantenimiento.md -o manual-mantenimiento.pdf
    pandoc resumen-proyecto.md -o resumen-proyecto.pdf
    echo ✅ PDFs generados exitosamente
) else (
    echo ⚠️  Pandoc no encontrado
    echo 📥 Descarga Pandoc desde: https://pandoc.org/installing.html
    echo 💡 O usa una herramienta online para convertir los .md a PDF
)

echo.
echo 🎉 Proceso completado!
echo 📁 Archivos disponibles en la carpeta 'manuales':
dir /b *.md *.pdf 2>nul
echo.
echo 📖 Para ver los manuales:
echo    - Abre los archivos .md en cualquier editor
echo    - Los PDFs ^(si se generaron^) están listos para imprimir
echo.
pause