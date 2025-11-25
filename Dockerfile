FROM python:3.9-slim

WORKDIR /app

# Copiar requirements primeiro para cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretório para logs
RUN mkdir -p /app/logs

# Tornar script executável
RUN chmod +x start.sh

# Expor ambas as portas
EXPOSE 9996 9991

# Usar script de inicialização
CMD ["./start.sh"]