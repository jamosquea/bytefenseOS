#!/bin/bash
# Script para construir el paquete .deb de Bytefense OS

set -e

PACKAGE_NAME="bytefense-os"
VERSION="1.0.0"
ARCH="all"
BUILD_DIR="debian"
OUTPUT_DIR="dist"

echo "📦 Construyendo paquete .deb de Bytefense OS v$VERSION"

# Limpiar construcción anterior
echo "🧹 Limpiando construcción anterior..."
rm -rf "$BUILD_DIR" "$OUTPUT_DIR"

# Crear estructura de directorios
echo "📁 Creando estructura de directorios..."
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/bytefense"
mkdir -p "$BUILD_DIR/etc/systemd/system"
mkdir -p "$BUILD_DIR/usr/local/bin"
mkdir -p "$BUILD_DIR/usr/share/doc/bytefense-os"
mkdir -p "$OUTPUT_DIR"

# Copiar archivos del proyecto
echo "📋 Copiando archivos del proyecto..."
cp -r bin feeds web docs system "$BUILD_DIR/opt/bytefense/"

# Copiar servicios systemd
cp system/*.service "$BUILD_DIR/etc/systemd/system/"

# Crear archivos de control (estos se crearían con el contenido mostrado arriba)
echo "⚙️ Creando archivos de control..."
# Los archivos de control se crean con el contenido mostrado anteriormente

# Establecer permisos correctos
echo "🔐 Estableciendo permisos..."
chmod 755 "$BUILD_DIR/DEBIAN/preinst"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"
chmod 755 "$BUILD_DIR/DEBIAN/postrm"
chmod +x "$BUILD_DIR/opt/bytefense/bin/"*

# Comprimir changelog
echo "📄 Comprimiendo changelog..."
gzip -9 "$BUILD_DIR/usr/share/doc/bytefense-os/changelog.Debian"

# Construir el paquete
echo "🔨 Construyendo paquete .deb..."
fakeroot dpkg-deb --build "$BUILD_DIR" "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

# Verificar el paquete
echo "🔍 Verificando paquete..."
lintian "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" || true

# Mostrar información del paquete
echo "📊 Información del paquete:"
dpkg-deb --info "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo ""
echo "✅ Paquete .deb creado exitosamente:"
echo "📦 Archivo: $OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "📏 Tamaño: $(du -h "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" | cut -f1)"
echo ""
echo "🚀 Para instalar:"
echo "   sudo dpkg -i $OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "   sudo apt-get install -f  # Si hay dependencias faltantes"
echo ""
echo "🗑️ Para desinstalar:"
echo "   sudo apt remove $PACKAGE_NAME"
echo "   sudo apt purge $PACKAGE_NAME  # Eliminación completa"