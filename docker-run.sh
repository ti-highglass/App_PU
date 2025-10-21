#!/bin/bash

# Script para executar o Sistema de Alocação de PU com Docker

echo "🚀 Sistema de Alocação de PU - Docker Setup"
echo "=========================================="

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Instale o Docker primeiro."
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Instale o Docker Compose primeiro."
    exit 1
fi

# Verificar se arquivo .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado. Copiando .env.example..."
    cp .env.example .env
    echo "📝 Configure o arquivo .env com suas credenciais antes de continuar."
    echo "   Edite o arquivo .env e execute este script novamente."
    exit 1
fi

echo "📦 Construindo imagem Docker..."
docker-compose build

echo "🔧 Iniciando containers..."
docker-compose up -d

echo "✅ Sistema iniciado com sucesso!"
echo ""
echo "🌐 Acesse o sistema em: http://localhost:9996"
echo ""
echo "📋 Comandos úteis:"
echo "   Ver logs:           docker-compose logs -f"
echo "   Parar sistema:      docker-compose down"
echo "   Reiniciar:          docker-compose restart"
echo "   Status:             docker-compose ps"