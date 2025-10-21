#!/bin/bash

# Script para executar o container do Sistema de Alocação de PU

echo "Iniciando Sistema de Alocação de PU..."

docker run -d \
  --name sistema-alocacao-pu \
  --restart unless-stopped \
  -p 9996:9996 \
  -p 9991:9991 \
  -e DB_HOST=seu_host_postgresql \
  -e DB_USER=seu_usuario \
  -e DB_PSW=sua_senha \
  -e DB_PORT=5432 \
  -e DB_NAME=seu_banco \
  -e SSO_SHARED_SECRET=chave_compartilhada \
  -e SSO_SALT=app-pu-acomp-sso \
  -e ACOMP_CORTE_BASE_URL=http://10.150.16.54:5555 \
  -e EMAIL_REMETENTE=seu_email@empresa.com \
  -e EMAIL_SENHA=sua_senha_email \
  -v $(pwd)/logs:/app/logs \
  sistema-alocacao-pu:latest

echo "Container iniciado!"
echo "Acesse: http://localhost:9996"
echo ""
echo "Para ver logs: docker logs -f sistema-alocacao-pu"
echo "Para parar: docker stop sistema-alocacao-pu"