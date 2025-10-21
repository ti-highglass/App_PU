========================================
SISTEMA DE ALOCAÇÃO DE PU - OPERA
INSTRUÇÕES DE INSTALAÇÃO E USO
========================================

REQUISITOS:
- Python 3.7 ou superior
- Conexão com internet (para instalar dependências)

INSTALAÇÃO:
1. Baixe/copie toda a pasta do sistema
2. Certifique-se que o arquivo .env está presente com as credenciais do banco
   - Para integrar com o painel de acompanhamento de corte, adicione também:
     ACOMP_CORTE_BASE_URL, SSO_SHARED_SECRET, SSO_SALT, ACOMP_CORTE_SSO_URL,
     ACOMP_CORTE_FALLBACK_URL, ACOMP_CORTE_SSO_LOGOUT_URL e ACOMP_CORTE_DEFAULT_NEXT
3. Execute o arquivo "iniciar_sistema.bat"

PRIMEIRO USO:
1. Clique duas vezes no arquivo "iniciar_sistema.bat"
2. Aguarde a instalação das dependências (primeira vez apenas)
3. Quando aparecer "Sistema iniciado com sucesso!", abra o navegador
4. Acesse: http://localhost:9990
5. Faça login com suas credenciais

USUÁRIOS PADRÃO:
- Consulte o administrador do sistema para credenciais

ACESSO EM REDE:
- O sistema roda na porta 9990
- Outros computadores podem acessar via: http://IP_DA_MAQUINA:9990
- Exemplo: http://192.168.1.100:9990

PARAR O SISTEMA:
- Feche a janela do prompt de comando
- Ou pressione Ctrl+C na janela

PROBLEMAS COMUNS:
- "Python não encontrado": Instale Python 3.7+ do site python.org
- "Erro de conexão": Verifique se o arquivo .env está correto
- "Porta ocupada": Feche outros programas que usem a porta 9990

SUPORTE:
- Entre em contato com o setor de T.I da Opera
