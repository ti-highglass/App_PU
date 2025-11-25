#!/bin/bash

# Script para iniciar ambos os serviços no container

# Função para cleanup
cleanup() {
    echo "Parando serviços..."
    kill $DASHBOARD_PID $APP_PID 2>/dev/null
    exit 0
}

# Capturar sinais para cleanup
trap cleanup SIGTERM SIGINT

echo "Iniciando Dashboard na porta 9991..."
python dashboard_app.py &
DASHBOARD_PID=$!

echo "Aguardando 3 segundos..."
sleep 3

echo "Iniciando aplicação principal na porta 9996..."
gunicorn app:app \
  -b 0.0.0.0:9996 \
  --workers ${GUNICORN_WORKERS:-2} \
  --worker-class ${GUNICORN_WORKER_CLASS:-gthread} \
  --threads ${GUNICORN_THREADS:-4} \
  --timeout ${GUNICORN_TIMEOUT:-120} \
  --access-logfile - \
  --error-logfile - \
  --log-level info &
APP_PID=$!

echo "Serviços iniciados:"
echo "- Dashboard PID: $DASHBOARD_PID"
echo "- App Principal PID: $APP_PID"

# Aguardar ambos os processos
wait $DASHBOARD_PID $APP_PID