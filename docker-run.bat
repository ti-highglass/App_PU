@echo off
echo 🚀 Sistema de Alocação de PU - Docker Setup
echo ==========================================

REM Verificar se Docker está instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker não está instalado. Instale o Docker Desktop primeiro.
    pause
    exit /b 1
)

REM Verificar se Docker Compose está instalado
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose não está instalado. Instale o Docker Desktop primeiro.
    pause
    exit /b 1
)

REM Verificar se arquivo .env existe
if not exist .env (
    echo ⚠️  Arquivo .env não encontrado. Copiando .env.example...
    copy .env.example .env
    echo 📝 Configure o arquivo .env com suas credenciais antes de continuar.
    echo    Edite o arquivo .env e execute este script novamente.
    pause
    exit /b 1
)

echo 📦 Construindo imagem Docker...
docker-compose build

echo 🔧 Iniciando containers...
docker-compose up -d

echo ✅ Sistema iniciado com sucesso!
echo.
echo 🌐 Acesse o sistema em: http://localhost:9996
echo.
echo 📋 Comandos úteis:
echo    Ver logs:           docker-compose logs -f
echo    Parar sistema:      docker-compose down
echo    Reiniciar:          docker-compose restart
echo    Status:             docker-compose ps
echo.
pause