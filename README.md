# Sistema de Alocação de PU

## Descrição

Sistema web desenvolvido em Flask para gerenciamento completo de alocação de peças de PU (Poliuretano) automotivas da Opera. O sistema oferece controle total do fluxo desde a coleta de dados até o armazenamento final no estoque, com funcionalidades avançadas de otimização, rastreamento e relatórios.

## 🚀 Versão Atual: 2.5

**Principais atualizações v2.5:**
- **NOVO:** Sistema de impressão automática de etiquetas para novos locais
- **NOVO:** Integração com impressoras Zebra via serviço HTTP
- **NOVO:** Template ZPL personalizável para etiquetas (ZEBRA.prn)
- **NOVO:** APIs de teste e status do serviço de impressão
- **NOVO:** Containerização completa com Docker
- **NOVO:** Imagem .tar para deploy simplificado
- **NOVO:** Scripts automatizados de build e execução
- **NOVO:** Suporte a Alpine Linux para maior estabilidade
- **MELHORADO:** Correção na atualização de status de lotes específicos
- **MELHORADO:** Filtros aprimorados para etapa RT-RP
- **MELHORADO:** Geração correta de lotes PU (VDA019 → PUA019)

**Principais atualizações:**
- **NOVO:** Atualização automática de status dos lotes (pu_cortado → 'CORTADO')
- **NOVO:** Verificação inteligente de lotes completos no estoque
- **NOVO:** API para verificação manual de status dos lotes
- **NOVO:** Script de teste para validação da funcionalidade
- Sistema de 3 racks (RACK1, RACK2, RACK3)
- Integração com API externa pplug.com.br
- Sistema de etiquetas com códigos de barras
- Envio de credenciais por email
- Interface mobile otimizada e responsiva para tablets
- Dashboard standalone em tempo real (porta 9991)
- Sistema de alertas por estágio de produção
- Processamento em lotes para evitar timeouts
- Ordenação correta de datas em formato brasileiro
- Upload de arquivos XLSX com validação
- Sistema "Voltar Peça" para reintegração ao estoque
- Notificações não-bloqueantes
- Contadores dinâmicos de peças
- Visualização de peças por local

## Funcionalidades Principais

### 🔐 Sistema de Autenticação
- ✅ Login seguro com hash de senhas
- ✅ Controle de acesso por setor (Produção, Administrativo, T.I)
- ✅ Gerenciamento de usuários (apenas T.I)
- ✅ Diferentes níveis de permissão
- ✅ SSO com o painel Acompanhamento de Corte
- ✅ Logout sincronizado com o painel de acompanhamento

### 📊 Coleta e Otimização de Dados
- ✅ Coleta automática de dados do banco dados_uso_geral.dados_op
- ✅ Filtros por estágio de produção (FILA, FORNO-S, etc.)
- ✅ Algoritmo inteligente de sugestão de locais de armazenamento
- ✅ Workflow de otimização com validação de espaços
- ✅ Prevenção de duplicatas no sistema
- ✅ Upload de arquivos XLSX com validação automática
- ✅ Processamento em lotes para evitar timeouts

### 🏭 Gestão de Estoque
- ✅ Controle completo de inventário
- ✅ Rastreamento de movimentações
- ✅ Histórico de saídas com auditoria
- ✅ Status dinâmico de locais (Ativo/Utilizando)
- ✅ Operações em lote (seleção múltipla)
- ✅ Saída massiva com identificação nos logs
- ✅ Sistema "Voltar Peça" para reintegração
- ✅ Contador dinâmico de peças em estoque
- ✅ Filtragem com atualização automática do contador
- ✅ **NOVO:** Atualização automática de status dos lotes
- ✅ **NOVO:** Verificação inteligente de lotes completos
- ✅ **NOVO:** Impressão automática de etiquetas para novos locais

### 📍 Gerenciamento de Locais
- ✅ Cadastro de locais COLMEIA e GAVETEIRO
- ✅ Algoritmo de sequenciamento automático
- ✅ Monitoramento de ocupação em tempo real
- ✅ Validação de disponibilidade
- ✅ Visualização de peças armazenadas por local
- ✅ Contadores de peças por local com badges visuais
- ✅ Ordenação por quantidade de peças

### 📈 Relatórios e Exportação
- ✅ Geração de arquivos XML com base em camadas
- ✅ Exportação Excel com colunas alinhadas
- ✅ Relatórios de estoque, saídas e logs
- ✅ Filtros e busca avançada
- ✅ Salvamento automático em pastas sincronizadas

### 🔍 Sistema de Logs e Auditoria
- ✅ Rastreamento completo de ações dos usuários
- ✅ Logs detalhados com timestamp
- ✅ Busca e filtros nos logs (apenas T.I)
- ✅ Exportação de relatórios de auditoria
- ✅ **NOVO:** Logs de verificação automática de lotes
- ✅ **NOVO:** Debug detalhado para status dos lotes

### 🖨️ Sistema de Impressão de Etiquetas
- ✅ **NOVO:** Impressão automática para novos locais de armazenamento
- ✅ **NOVO:** Integração com impressoras Zebra via ZPL
- ✅ **NOVO:** Template personalizável (ZEBRA.prn)
- ✅ **NOVO:** Serviço HTTP independente para impressão
- ✅ **NOVO:** APIs de teste e monitoramento
- ✅ **NOVO:** Detecção inteligente de locais novos vs. reutilizados
- ✅ **NOVO:** Códigos de barras automáticos (Peça + OP)
- ✅ **NOVO:** Campos dinâmicos (data, projeto, veículo, etc.)

### 🎨 Interface e Experiência
- ✅ Design responsivo e moderno para tablets
- ✅ Tabelas com ordenação correta por datas brasileiras
- ✅ Paginação inteligente
- ✅ Modais para operações críticas
- ✅ Dashboard standalone em tempo real
- ✅ Sistema de alertas visuais por estágio
- ✅ Animações e transições suaves
- ✅ Contadores visuais dinâmicos
- ✅ Ícones de ordenação discretos
- ✅ Badges coloridos para status e contagens
- ✅ Botões de limpeza em campos de pesquisa

## Tecnologias Utilizadas

- **Backend**: Python 3.x + Flask + Flask-Login
- **Frontend**: HTML5 + CSS3 + JavaScript (Vanilla)
- **Banco de Dados**: PostgreSQL (Supabase)
- **Autenticação**: Werkzeug Security
- **Exportação**: Pandas + OpenPyXL
- **Impressão**: ZPL (Zebra Programming Language) + HTTP Service
- **Códigos de Barras**: Code128 via template ZPL
- **Ícones**: Font Awesome 6.0
- **Estilo**: CSS customizado com design system próprio

## Instalação e Execução

### 🐳 Método Docker (Recomendado)

#### 1. Construir e exportar imagem
```bash
# Executar script automatizado
./build-image.bat

# Ou manualmente
docker build -t sistema-alocacao-pu:latest .
docker save -o sistema-alocacao-pu.tar sistema-alocacao-pu:latest
```

#### 2. Carregar imagem em servidor
```bash
docker load -i sistema-alocacao-pu.tar
```

#### 3. Executar container
```bash
# Editar configurações no script
nano run-container.sh

# Executar
chmod +x run-container.sh
./run-container.sh
```

#### 4. Acessar sistema
```
Sistema Principal: http://SEU_IP:9996
Dashboard: http://SEU_IP:9991
```

### 💻 Método Tradicional

#### 1. Configurar ambiente
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente (.env)
cp .env.example .env
# Editar .env com suas configurações
```

#### 2. Executar aplicação
```bash
# Opção 1: Script completo (recomendado)
iniciar_sistema_completo.bat

# Opção 2: Manual
# Terminal 1 - Serviço de Impressão
python send_to_printer.py --serve --host 127.0.0.1 --port 5000

# Terminal 2 - Sistema Principal
python app.py
```

#### 3. Login inicial
- Usuário padrão deve ser criado via T.I
- Setores: Produção, Administrativo, T.I
- Funções: user, admin

#### 4. Configurar Impressora (Opcional)
- Instalar driver da impressora Zebra
- Configurar como impressora padrão
- Testar impressão via `/api/testar-impressao-etiqueta`

## Estrutura do Projeto

```
Sistema Alocação de PU/
│
├── app.py                    # Aplicação Flask principal
├── requirements.txt          # Dependências Python
├── README.md                # Documentação
├── .env                     # Variáveis de ambiente (não versionado)
├── iniciar_sistema.bat      # Script de inicialização
├── README_INSTALACAO.txt    # Guia de instalação
│
├── templates/
│   ├── navbar.html          # Navegação centralizada
│   ├── login.html           # Tela de login
│   ├── index.html           # Otimização de peças
│   ├── estoque.html         # Gestão de estoque
│   ├── locais.html          # Gerenciamento de locais
│   ├── otimizadas.html      # Peças em processo
│   ├── saidas.html          # Histórico de saídas
│   ├── register.html        # Gestão de usuários
│   └── logs.html            # Sistema de logs
│
└── static/
    ├── css/
    │   ├── style.css        # Estilos principais
    │   └── login.css        # Estilos do login
    ├── js/
    │   ├── protection.js    # Proteção de código
    │   ├── index.js         # Lógica da otimização
    │   ├── estoque.js       # Lógica do estoque
    │   ├── locais.js        # Lógica dos locais
    │   ├── otimizadas.js    # Lógica das otimizadas
    │   ├── saidas.js        # Lógica das saídas
    │   ├── register.js      # Lógica dos usuários
    │   └── logs.js          # Lógica dos logs
    └── img/
        └── opera.jpg        # Logo da empresa
```

## Estrutura do Banco de Dados

### Tabelas Principais

#### plano_controle_corte_vidro2 (Controle de Lotes)
| Campo           | Tipo      | Descrição                    |
|-----------------|-----------|------------------------------|
| id_lote         | TEXT      | ID único do lote            |
| op              | TEXT      | Ordem de Produção           |
| peca            | TEXT      | Código da peça              |
| projeto         | TEXT      | Projeto da peça             |
| status          | TEXT      | Status geral do lote        |
| pu_cortado      | TEXT      | **NOVO:** Status PU (PROGRAMANDO/PROGRAMADO/CORTADO) |
| data_programacao| DATE      | Data de programação         |
| turno_programacao| TEXT     | Turno programado            |

#### pu_inventory (Estoque Final)
| Campo     | Tipo      | Descrição                 |
|-----------|-----------|---------------------------|
| id        | SERIAL    | Chave primária           |
| op_pai    | TEXT      | OP pai                   |
| op        | TEXT      | Ordem de Produção        |
| peca      | TEXT      | Código da peça           |
| projeto   | TEXT      | Projeto da peça          |
| veiculo   | TEXT      | Modelo do veículo        |
| local     | TEXT      | Local de armazenamento   |
| rack      | TEXT      | Tipo de rack             |
| lote_vd   | TEXT      | **NOVO:** ID do lote VD  |
| lote_pu   | TEXT      | **NOVO:** ID do lote PU  |

#### pu_otimizadas (Processo Intermediário)
| Campo           | Tipo      | Descrição                 |
|-----------------|-----------|---------------------------|
| id              | SERIAL    | Chave primária           |
| op_pai          | TEXT      | OP pai                   |
| op              | TEXT      | Ordem de Produção        |
| peca            | TEXT      | Código da peça           |
| projeto         | TEXT      | Projeto da peça          |
| veiculo         | TEXT      | Modelo do veículo        |
| local           | TEXT      | Local sugerido           |
| rack            | TEXT      | Tipo de rack             |
| cortada         | BOOLEAN   | Status de corte          |
| user_otimizacao | TEXT      | Usuário responsável      |
| data_otimizacao | TIMESTAMP | Data da otimização       |

#### pu_locais (Gestão de Locais)
| Campo  | Tipo   | Descrição              |
|--------|--------|------------------------|
| id     | SERIAL | Chave primária        |
| local  | TEXT   | Código do local       |
| rack   | TEXT   | COLMEIA ou GAVETEIRO  |
| status | TEXT   | Ativo ou Utilizando   |

#### pu_exit (Histórico de Saídas)
| Campo   | Tipo      | Descrição              |
|---------|-----------|------------------------|
| id      | SERIAL    | Chave primária        |
| op_pai  | TEXT      | OP pai                |
| op      | TEXT      | Ordem de Produção     |
| peca    | TEXT      | Código da peça        |
| projeto | TEXT      | Projeto da peça       |
| veiculo | TEXT      | Modelo do veículo     |
| local   | TEXT      | Local de origem       |
| rack    | TEXT      | Tipo de rack          |
| usuario | TEXT      | Usuário responsável   |
| data    | TIMESTAMP | Data da saída         |

#### users_pu (Controle de Usuários)
| Campo   | Tipo   | Descrição                    |
|---------|--------|------------------------------|
| id      | SERIAL | Chave primária              |
| usuario | TEXT   | Nome do usuário             |
| senha   | TEXT   | Hash da senha               |
| funcao  | TEXT   | user ou admin               |
| setor   | TEXT   | Produção/Administrativo/T.I |

#### pu_logs (Sistema de Auditoria)
| Campo     | Tipo      | Descrição              |
|-----------|-----------|------------------------|
| id        | SERIAL    | Chave primária        |
| usuario   | TEXT      | Usuário da ação       |
| acao      | TEXT      | Tipo de ação          |
| detalhes  | TEXT      | Detalhes da ação      |
| data_acao | TIMESTAMP | Timestamp da ação     |

### Tabela de Origem (Somente Leitura)

#### apontamento_pplug_jarinu
| Campo   | Tipo | Descrição                    |
|---------|------|------------------------------|
| op      | TEXT | Ordem de Produção           |
| item    | TEXT | Código da peça              |
| projeto | TEXT | Projeto                     |
| veiculo | TEXT | Modelo do veículo           |
| data    | DATE | Data do apontamento         |
| etapa   | TEXT | Etapa (filtro: EMPOLVADO)   |

## API Endpoints

### Autenticação
- `GET /` - Página de login
- `POST /login` - Autenticação de usuário
- `GET /logout` - Logout do sistema

### Páginas Principais
- `GET /index` - Tela de otimização (redireciona Produção para /otimizadas)
- `GET /estoque` - Gestão de estoque
- `GET /locais` - Gerenciamento de locais
- `GET /otimizadas` - Peças em processo
- `GET /saidas` - Histórico de saídas
- `GET /register` - Gestão de usuários (apenas T.I)
- `GET /logs` - Sistema de logs (apenas T.I admin)

### APIs de Dados
- `GET /api/dados` - Coleta dados com filtros de data
- `GET /api/estoque` - Lista itens do estoque
- `GET /api/otimizadas` - Lista peças otimizadas
- `GET /api/locais` - Lista locais com status
- `GET /api/contagem-pecas-locais` - Contagem de peças por local
- `GET /api/local-detalhes/<local>` - Detalhes das peças em um local
- `GET /api/saidas` - Histórico paginado de saídas
- `GET /api/logs` - Logs paginados (apenas T.I)
- `GET /api/usuarios` - Lista usuários (apenas T.I)
- `POST /api/verificar-status-lotes` - **NOVO:** Verifica status de todos os lotes

### APIs de Operação
- `POST /api/otimizar-pecas` - Envia peças para otimização
- `POST /api/enviar-estoque` - Move peças otimizadas para estoque (lotes)
- `POST /api/remover-estoque` - Remove peças do estoque (lotes)
- `POST /api/adicionar-local` - Cadastra novo local
- `POST /api/upload-xlsx` - Upload de arquivos Excel
- `POST /api/voltar-peca-estoque` - Reintegra peça ao estoque (com impressão automática)
- `POST /api/verificar-peca-existente` - Verifica duplicatas
- `GET /api/buscar-op/<op>` - Busca dados da OP
- `GET /api/buscar-veiculo/<op>` - Busca veículo da OP

### APIs de Impressão
- `POST /api/testar-impressao-etiqueta` - Testa impressão de etiqueta
- `GET /api/status-servico-impressao` - Status do serviço de impressão

### APIs de Usuários (T.I)
- `POST /api/cadastrar-usuario` - Cria novo usuário
- `PUT /api/editar-usuario/<id>` - Edita usuário
- `PUT /api/resetar-senha/<id>` - Reseta senha
- `DELETE /api/excluir-usuario/<id>` - Exclui usuário

### APIs de Exportação
- `POST /api/gerar-xml` - Gera XMLs de otimização
- `POST /api/gerar-excel-otimizacao` - Excel das peças selecionadas
- `POST /api/gerar-excel-estoque` - Excel do estoque
- `POST /api/gerar-excel-saidas` - Excel das saídas
- `POST /api/gerar-excel-logs` - Excel dos logs (T.I)

## Fluxo de Trabalho

### 1. Coleta e Otimização
1. **Login** no sistema com credenciais apropriadas
2. **Acesse Otimização** (tela principal)
3. **Configure filtros** de data/hora se necessário
4. **Colete dados** do banco de origem
5. **Selecione peças** para otimização
6. **Gere XML** ou **Excel** conforme necessidade
7. **Otimize peças** selecionadas

### 2. Processamento (Tela Otimizadas)
1. **Visualize peças** em processo de otimização
2. **Selecione peças** processadas
3. **Envie para estoque** final

### 3. Gestão de Estoque
1. **Monitore inventário** completo
2. **Remova peças** quando necessário
3. **Exporte relatórios** em Excel
4. **Acompanhe movimentações**

### 4. Dashboard de Produção
1. **Acesse dashboard** em tempo real (porta 9991)
2. **Monitore peças** por estágio de produção
3. **Visualize alertas** críticos e avisos
4. **Acompanhe fluxo** de peças em tempo real

### 5. Administração (T.I)
1. **Gerencie usuários** e permissões
2. **Monitore logs** do sistema
3. **Configure locais** de armazenamento
4. **Exporte relatórios** de auditoria
5. **NOVO:** **Verifique status** dos lotes manualmente
6. **NOVO:** **Execute testes** de funcionalidade dos lotes

## Algoritmo de Armazenamento

### COLMEIA (Peças específicas)
**Peças**: PBS, VGA, VGE, VGD, TSP, TSA, TSB, TSC

**Sequência de preenchimento**:
1. E1→E2→E3→E4→E5→E6→E7
2. F1→F2→F3→F4→F5→F6→F7→F8→F9
3. G1→G2→...→G11
4. H1→H2→...→H12
5. I1→I2→...→I14
6. J1→J2→...→J16
7. K1→K2→...→K17
8. L1→L2→...→L17
9. D1→D2→D3→D4→D5→D6
10. C1→C2→C3→C4
11. B1→B2→B3
12. A1

### GAVETEIRO (Demais peças)
**Sequência de preenchimento**:
1. **Linha A**: A7→A8→...→A20, depois A6→A5→...→A1
2. **Linhas B-F**: B7→C7→D7→E7→F7, depois B8→C8→D8→E8→F8, etc.

## Requisitos do Sistema

### Software
- **Python**: 3.7+
- **PostgreSQL**: 12+
- **Navegadores**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### Dependências Python
```
Flask==2.3.3
Flask-Login==0.6.3
psycopg2-binary==2.9.7
pandas==2.0.3
openpyxl==3.1.2
python-dotenv==1.0.0
Werkzeug==2.3.7
requests==2.31.0
reportlab==4.0.4
python-barcode==0.15.1
Pillow==10.0.0
pywin32==305
```

### Configuração de Rede
- **Porta Principal**: 9996
- **Dashboard**: 9991 (auto-iniciado)
- **Serviço de Impressão**: 5000 (auto-iniciado)
- **Host**: 0.0.0.0 (acesso em rede local)
- **Protocolo**: HTTP

## Segurança

- ✅ Autenticação com hash de senhas (Werkzeug)
- ✅ Controle de sessão (Flask-Login)
- ✅ Validação de permissões por setor
- ✅ Proteção contra inspeção de código
- ✅ Logs de auditoria completos
- ✅ Validação de entrada de dados

## Performance

- ✅ Consultas otimizadas com índices
- ✅ Paginação em tabelas grandes
- ✅ Cache de locais ocupados
- ✅ Operações em lote com processamento por chunks
- ✅ Timeout de conexão configurado (10s)
- ✅ Statement timeout (30s) para evitar travamentos
- ✅ Compressão de arquivos ZIP
- ✅ **NOVO:** Verificação eficiente de lotes completos
- ✅ **NOVO:** Atualização automática sem impacto na performance

## Personalização

### Configurar Banco de Dados
Edite o arquivo `.env` com suas credenciais PostgreSQL

### Modificar Algoritmo de Armazenamento
Altere a função `sugerir_local_armazenamento()` em `app.py`

### Customizar Interface
- **Estilos**: Modifique `static/css/style.css`
- **Lógica**: Edite arquivos JavaScript em `static/js/`
- **Layout**: Altere templates HTML em `templates/`

### Adicionar Funcionalidades
1. **Backend**: Crie novas rotas em `app.py`
2. **Frontend**: Adicione JavaScript correspondente
3. **Interface**: Crie/modifique templates HTML

## Manutenção

### Backup Recomendado
- **Banco de dados**: Backup diário automático
- **Logs**: Rotação semanal
- **Arquivos**: Backup dos XMLs gerados

### Monitoramento
- **Logs de sistema**: Tabela `pu_logs`
- **Performance**: Monitorar consultas lentas
- **Espaço**: Verificar crescimento das tabelas

## 🐳 Docker e Deploy

### Arquivos Docker
- `Dockerfile` - Imagem principal (Debian)
- `Dockerfile.alpine` - Imagem alternativa (Alpine Linux)
- `docker-compose.yml` - Orquestração completa
- `build-image.bat` - Script de build automatizado
- `run-container.sh` - Script de execução Linux
- `.env.example` - Template de variáveis de ambiente

### Comandos Úteis Docker
```bash
# Ver logs
docker logs -f sistema-alocacao-pu

# Reiniciar
docker restart sistema-alocacao-pu

# Parar
docker stop sistema-alocacao-pu

# Remover
docker rm -f sistema-alocacao-pu
```

## Suporte e Desenvolvimento

**Desenvolvido por**: Pedro Torres  
**GitHub**: pgtorres7  
**Versão**: 2.5  
**Data**: Janeiro de 2025

### Funcionalidades Recentes (v2.5)
- **Sistema de Impressão**: Etiquetas automáticas para novos locais
- **Integração Zebra**: Suporte completo a impressoras ZPL
- **Template Personalizável**: ZEBRA.prn editável
- **Serviço HTTP**: Impressão via API independente
- **Containerização Docker**: Deploy simplificado com imagens .tar
- **Correção de Lotes**: Atualização precisa por peça individual
- **Filtros Aprimorados**: Suporte a etapa RT-RP
- **Geração de Lotes PU**: Conversão correta VDA019 → PUA019

### Contato
- **Suporte técnico**: Setor T.I Opera
- **Melhorias**: Solicitar via chamados
- **Deploy**: Usar imagens Docker para produção
- **Impressão**: Consultar IMPRESSAO_ETIQUETAS.md para configuração

---

*Sistema em produção - Todas as operações são logadas e auditadas*
