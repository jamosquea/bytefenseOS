@echo off
chcp 65001 >nul
echo 🚀 Preparando Bytefense OS para GitHub
echo =====================================
echo.

REM Verificar si Git está instalado
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git no está instalado
    echo 📥 Descarga Git desde: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git encontrado
echo.

REM Inicializar repositorio si no existe
if not exist ".git" (
    echo 🔧 Inicializando repositorio Git...
    git init
    echo ✅ Repositorio inicializado
) else (
    echo ✅ Repositorio Git ya existe
)

REM Configurar remote si no existe
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔗 Configurando remote origin...
    git remote add origin https://github.com/jamosquea/bytefenseOS.git
    echo ✅ Remote configurado
) else (
    echo ✅ Remote ya configurado
)

REM Añadir todos los archivos
echo 📁 Añadiendo archivos al staging...
git add .

REM Mostrar estado
echo 📊 Estado del repositorio:
git status --short

echo.
echo 🎯 Siguiente paso:
echo    git commit -m "Initial commit: Bytefense OS complete system"
echo    git push -u origin main
echo.
echo ⚠️  Recuerda configurar tu usuario Git si no lo has hecho:
echo    git config --global user.name "jamosquea"
echo    git config --global user.email "shello_1@hotmail.com"
echo.
pause