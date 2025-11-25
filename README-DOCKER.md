# Sistema de Alocação de PU - Docker

## 🐳 Execução com Docker

### Pré-requisitos
- Docker Desktop instalado
- Docker Compose disponível

### 🚀 Execução Rápida

#### Windows
```bash
docker-run.bat
```

#### Linux/WSL/macOS
```bash
chmod +x docker-run.sh
./docker-run.sh
```

### 📋 Execução Manual

1. **Configurar variáveis de ambiente:**
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas credenciais
   ```

2. **Construir e executar:**
   ```bash
   docker-compose up -d
   ```

3. **Acessar sistema:**
   ```
   http://localhost:9996
   ```

### 🔧 Comandos Úteis

```bash
# Ver logs em tempo real
docker-compose logs -f

# Parar sistema
docker-compose down

# Reiniciar containers
docker-compose restart

# Ver status dos containers
docker-compose ps

# Reconstruir imagem
docker-compose build --no-cache

# Executar em modo desenvolvimento (com logs)
docker-compose up
```

### 📁 Estrutura de Arquivos Docker

```
├── Dockerfile              # Definição da imagem
├── docker-compose.yml      # Orquestração dos containers
├── .dockerignore           # Arquivos ignorados no build
├── .env.example            # Template de configuração
├── docker-run.sh           # Script de execução (Linux/macOS)
├── docker-run.bat          # Script de execução (Windows)
└── README-DOCKER.md        # Esta documentação
```

### 🌐 Portas Utilizadas

- **9996**: Sistema Principal
- **9991**: Dashboard (se habilitado)

### 📝 Configurações de Ambiente

O sistema utiliza as seguintes variáveis de ambiente:

```env
# Banco de Dados
DB_HOST=seu_host_postgresql
DB_USER=seu_usuario
DB_PSW=sua_senha
DB_PORT=5432
DB_NAME=nome_do_banco

# Email
EMAIL_REMETENTE=seu_email
EMAIL_SENHA=sua_senha

# SSO
SSO_SHARED_SECRET=chave_secreta
ACOMP_CORTE_BASE_URL=url_do_sistema_corte
```

### 🔍 Troubleshooting

#### Container não inicia
```bash
# Verificar logs
docker-compose logs sistema-pu

# Verificar se portas estão livres
netstat -an | grep 9996
```

#### Problemas de conexão com banco
- Verifique as credenciais no arquivo `.env`
- Certifique-se que o banco está acessível da rede Docker

#### Rebuild completo
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 🏗️ Desenvolvimento

Para desenvolvimento com hot-reload:

```bash
# Montar código como volume
docker-compose -f docker-compose.dev.yml up
```

### 📊 Monitoramento

```bash
# Uso de recursos
docker stats

# Logs específicos
docker-compose logs -f sistema-pu

# Entrar no container
docker-compose exec sistema-pu bash
```