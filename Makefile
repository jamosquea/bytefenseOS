# Makefile para Bytefense OS

PACKAGE_NAME = bytefense-os
VERSION = 1.0.0
ARCH = all
BUILD_DIR = debian
OUTPUT_DIR = dist

.PHONY: all clean build install uninstall test

all: build

build:
	@echo "📦 Construyendo paquete .deb..."
	@./build-deb.sh

clean:
	@echo "🧹 Limpiando archivos de construcción..."
	@rm -rf $(BUILD_DIR) $(OUTPUT_DIR)

install: build
	@echo "🚀 Instalando paquete..."
	@sudo dpkg -i $(OUTPUT_DIR)/$(PACKAGE_NAME)_$(VERSION)_$(ARCH).deb
	@sudo apt-get install -f

uninstall:
	@echo "🗑️ Desinstalando paquete..."
	@sudo apt remove $(PACKAGE_NAME)

test:
	@echo "🧪 Ejecutando pruebas..."
	@lintian $(OUTPUT_DIR)/$(PACKAGE_NAME)_$(VERSION)_$(ARCH).deb

help:
	@echo "Comandos disponibles:"
	@echo "  make build     - Construir paquete .deb"
	@echo "  make install   - Instalar paquete"
	@echo "  make uninstall - Desinstalar paquete"
	@echo "  make clean     - Limpiar archivos temporales"
	@echo "  make test      - Ejecutar pruebas"