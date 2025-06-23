#!/bin/bash

# Crear AppImage de Bytefense OS
APP_NAME="BytefenseOS"
VERSION="1.0.0"
APPDIR="$APP_NAME.AppDir"

echo "📦 Creando AppImage de Bytefense OS..."

# Crear estructura AppDir
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/bytefense"

# Copiar archivos
cp -r bin/* "$APPDIR/usr/bin/"
cp -r bytefense_web "$APPDIR/usr/share/bytefense/"
cp -r system "$APPDIR/usr/share/bytefense/"
cp -r feeds "$APPDIR/usr/share/bytefense/"

# Crear desktop file
cat > "$APPDIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Bytefense OS
Exec=bytefense-ctl
Icon=bytefense
Categories=Security;Network;
EOF

# Crear AppRun
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")" 
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/bytefense-ctl" "$@"
EOF

chmod +x "$APPDIR/AppRun"

# Descargar appimagetool
wget -O appimagetool https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool

# Crear AppImage
./appimagetool "$APPDIR" "$APP_NAME-$VERSION-x86_64.AppImage"

echo "✅ AppImage creado: $APP_NAME-$VERSION-x86_64.AppImage"