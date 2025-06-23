# Bytefense OS Makefile

PACKAGE_NAME = bytefense-os
VERSION = 1.0.0
INSTALL_DIR = /opt/bytefense
USER = bytefense

.PHONY: install uninstall clean status

install:
	@echo "🔧 Instalando Bytefense OS v$(VERSION)..."
	@if [ "$$(id -u)" != "0" ]; then echo "❌ Ejecutar como root: sudo make install"; exit 1; fi
	@echo "👤 Creando usuario del sistema..."
	@id $(USER) >/dev/null 2>&1 || useradd -r -s /bin/false -d $(INSTALL_DIR) -c "Bytefense System User" $(USER)
	@echo "📁 Creando directorios..."
	@mkdir -p $(INSTALL_DIR)/{bin,web,system,feeds,logs,config,data}
	@echo "📋 Copiando archivos..."
	@cp -r bin/* $(INSTALL_DIR)/bin/
	@cp -r bytefense_web/* $(INSTALL_DIR)/web/
	@cp -r system/* $(INSTALL_DIR)/system/
	@cp -r feeds/* $(INSTALL_DIR)/feeds/
	@chmod +x $(INSTALL_DIR)/bin/*
	@chown -R $(USER):$(USER) $(INSTALL_DIR)
	@echo "🐍 Instalando dependencias..."
	@pip3 install requests psutil flask cryptography
	@echo "⚙️ Configurando servicios..."
	@cp $(INSTALL_DIR)/system/*.service /etc/systemd/system/
	@systemctl daemon-reload
	@systemctl enable bytefense-watch.service bytefense-intel-updater.service
	@echo "🔗 Creando enlaces..."
	@ln -sf $(INSTALL_DIR)/bin/bytefense-ctl /usr/local/bin/bytefense-ctl
	@ln -sf $(INSTALL_DIR)/bin/bytefense-health /usr/local/bin/bytefense-health
	@echo "🚀 Iniciando servicios..."
	@systemctl start bytefense-watch.service bytefense-intel-updater.service
	@echo "✅ ¡Instalación completada!"

status:
	@echo "📊 Estado de Bytefense OS:"
	@systemctl status bytefense-watch.service --no-pager -l
	@systemctl status bytefense-intel-updater.service --no-pager -l

uninstall:
	@echo "🗑️ Desinstalando Bytefense OS..."
	@systemctl stop bytefense-watch.service bytefense-intel-updater.service || true
	@systemctl disable bytefense-watch.service bytefense-intel-updater.service || true
	@rm -f /etc/systemd/system/bytefense-*.service
	@systemctl daemon-reload
	@rm -f /usr/local/bin/bytefense-*
	@userdel $(USER) || true
	@rm -rf $(INSTALL_DIR)
	@echo "✅ Desinstalación completada"

clean:
	@echo "🧹 Limpiando archivos temporales..."
	@rm -rf dist/ debian-build/ *.deb
	@echo "✅ Limpieza completada"