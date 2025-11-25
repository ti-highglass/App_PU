let dadosOriginais = [];
let ordemAtual = { coluna: -1, crescente: true };
let paginaAtual = 1;
const itensPorPagina = 100;
let dadosFiltrados = [];
let pesquisaAtiva = false;
let paginationData = {};
let searchTimeout = null;

document.addEventListener('DOMContentLoaded', function() {
    carregarSaidasExit();
    
    // Adicionar listener para busca em tempo real
    const campoPesquisa = document.getElementById('campoPesquisaExit');
    if (campoPesquisa) {
        campoPesquisa.addEventListener('input', function() {
            const valor = this.value.trim();
            
            // Mostrar/ocultar botão de limpar
            const btnLimpar = document.getElementById('btn-limpar-pesquisa');
            if (btnLimpar) {
                btnLimpar.style.display = valor ? 'block' : 'none';
            }
            
            // Mostrar loading
            mostrarLoadingPesquisa(true);
            
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                paginaAtual = 1; // Reset para primeira página
                carregarSaidasExit();
            }, 500); // Aguarda 500ms após parar de digitar
        });
    }
});

function mostrarLoadingPesquisa(mostrar) {
    const loadingIcon = document.getElementById('search-loading');
    const btnLimpar = document.getElementById('btn-limpar-pesquisa');
    
    if (loadingIcon) {
        loadingIcon.style.display = mostrar ? 'block' : 'none';
    }
    
    if (btnLimpar && mostrar) {
        btnLimpar.style.display = 'none';
    }
}

function limparPesquisa() {
    const campoPesquisa = document.getElementById('campoPesquisaExit');
    if (campoPesquisa) {
        campoPesquisa.value = '';
        campoPesquisa.focus();
    }
    
    const btnLimpar = document.getElementById('btn-limpar-pesquisa');
    if (btnLimpar) {
        btnLimpar.style.display = 'none';
    }
    
    paginaAtual = 1;
    carregarSaidasExit();
}

async function carregarSaidasExit() {
    try {
        // Mostrar loading na tabela
        const tbody = document.getElementById('exit-tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="border border-gray-200 px-4 py-6 text-center text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Carregando dados...</td></tr>';
        }
        
        const campoPesquisa = document.getElementById('campoPesquisaExit');
        const termoBusca = campoPesquisa ? campoPesquisa.value.trim() : '';
        
        // Construir URL com parâmetros
        const params = new URLSearchParams({
            page: paginaAtual,
            limit: itensPorPagina
        });
        
        if (termoBusca) {
            params.append('search', termoBusca);
            pesquisaAtiva = true;
        } else {
            pesquisaAtiva = false;
        }
        
        const response = await fetch(`/api/saidas-exit?${params}`);
        const resultado = await response.json();
        
        if (resultado.error) {
            throw new Error(resultado.error);
        }
        
        dadosOriginais = resultado.dados;
        paginationData = resultado.pagination;
        
        renderizarTabela(dadosOriginais);
        
        // Ocultar loading da pesquisa
        mostrarLoadingPesquisa(false);
        
        // Mostrar botão de limpar se há texto
        const btnLimpar = document.getElementById('btn-limpar-pesquisa');
        if (btnLimpar && termoBusca) {
            btnLimpar.style.display = 'block';
        }
        
    } catch (error) {
        console.error('Erro ao carregar saídas:', error);
        const tbody = document.getElementById('exit-tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="border border-gray-200 px-4 py-6 text-center text-red-500"><i class="fas fa-exclamation-triangle mr-2"></i>Erro ao carregar dados</td></tr>';
        }
        
        // Ocultar loading da pesquisa
        mostrarLoadingPesquisa(false);
    }
}

function renderizarTabela(dados) {
    const tbody = document.getElementById('exit-tbody');
    tbody.innerHTML = '';
    
    if (!dados || dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Nenhuma saída encontrada</td></tr>';
        atualizarPaginacao();
        return;
    }
    
    // Renderizar todos os dados recebidos (já paginados pelo servidor)
    dados.forEach(item => {
        const row = tbody.insertRow();
        row.className = 'hover:bg-gray-50';
        
        [
            item.op || '',
            item.peca || '',
            item.projeto || '',
            item.veiculo || '',
            item.local || '',
            item.usuario || '',
            item.data || '',
            item.motivo || ''
        ].forEach(value => {
            const cell = row.insertCell();
            cell.textContent = value;
            cell.className = 'border border-gray-200 px-4 py-3 text-sm text-gray-700';
        });
    });
    
    atualizarPaginacao();
}

function ordenarTabela(coluna) {
    if (ordemAtual.coluna === coluna) {
        ordemAtual.crescente = !ordemAtual.crescente;
    } else {
        ordemAtual.coluna = coluna;
        ordemAtual.crescente = true;
    }
    
    const colunas = ['op', 'peca', 'projeto', 'veiculo', 'local', 'usuario', 'data', 'motivo'];
    const propriedade = colunas[coluna];
    
    const dadosOrdenados = [...dadosOriginais].sort((a, b) => {
        let valorA = (a[propriedade] || '').toString().toLowerCase();
        let valorB = (b[propriedade] || '').toString().toLowerCase();
        
        if (coluna === 6) { // Data
            valorA = new Date(a[propriedade] || '1900-01-01');
            valorB = new Date(b[propriedade] || '1900-01-01');
        }
        
        if (valorA < valorB) return ordemAtual.crescente ? -1 : 1;
        if (valorA > valorB) return ordemAtual.crescente ? 1 : -1;
        return 0;
    });
    
    renderizarTabela(dadosOrdenados);
    atualizarIconesOrdenacao(coluna);
}

function atualizarIconesOrdenacao(colunaAtiva) {
    document.querySelectorAll('th i').forEach((icone, index) => {
        if (index === colunaAtiva) {
            icone.className = ordemAtual.crescente ? 'fas fa-sort-up text-xs ml-1' : 'fas fa-sort-down text-xs ml-1';
        } else {
            icone.className = 'fas fa-sort text-xs ml-1 opacity-50';
        }
    });
}

function filtrarTabelaExit() {
    // A busca agora é feita automaticamente pelo listener de input
    // Esta função é mantida para compatibilidade
    paginaAtual = 1;
    carregarSaidasExit();
}

function mudarPagina(direcao) {
    const novaPagina = paginaAtual + direcao;
    
    if (novaPagina >= 1 && novaPagina <= (paginationData.total_pages || 1)) {
        paginaAtual = novaPagina;
        carregarSaidasExit();
    }
}

function irParaPagina(pagina) {
    if (pagina >= 1 && pagina <= (paginationData.total_pages || 1)) {
        paginaAtual = pagina;
        carregarSaidasExit();
    }
}

function atualizarPaginacao() {
    const infoRegistros = document.getElementById('info-registros');
    const infoPagina = document.getElementById('info-pagina');
    const btnAnterior = document.getElementById('btn-anterior');
    const btnProximo = document.getElementById('btn-proximo');
    const paginacao = document.getElementById('paginacao');
    
    if (!paginationData || !paginationData.total_records) {
        if (paginacao) paginacao.style.display = 'none';
        return;
    }
    
    const totalRecords = paginationData.total_records;
    const totalPages = paginationData.total_pages;
    const currentPage = paginationData.current_page;
    const limit = paginationData.limit;
    
    // Calcular range de registros exibidos
    const inicio = ((currentPage - 1) * limit) + 1;
    const fim = Math.min(currentPage * limit, totalRecords);
    
    if (infoRegistros) {
        if (pesquisaAtiva) {
            infoRegistros.textContent = `${totalRecords} registros encontrado(s)`;
        } else {
            infoRegistros.textContent = `${inicio}-${fim} de ${totalRecords}`;
        }
    }
    
    if (infoPagina) {
        infoPagina.textContent = `Página ${currentPage} de ${totalPages}`;
    }
    
    if (btnAnterior) {
        btnAnterior.disabled = !paginationData.has_prev;
    }
    
    if (btnProximo) {
        btnProximo.disabled = !paginationData.has_next;
    }
    
    if (paginacao) {
        paginacao.style.display = totalRecords > 0 ? 'flex' : 'none';
    }
}

function gerarExcelSaidas() {
    try {
        // Obter filtro atual
        const campoPesquisa = document.getElementById('campoPesquisaExit');
        const filtro = campoPesquisa ? campoPesquisa.value.trim() : '';
        
        // Construir URL com parâmetros
        let url = '/api/gerar-excel-saidas';
        if (filtro) {
            url += '?filtro=' + encodeURIComponent(filtro);
        }
        
        // Abrir em nova janela para download
        window.open(url, '_blank');
        
    } catch (error) {
        console.error('Erro ao gerar Excel:', error);
        alert('Erro ao gerar Excel: ' + error.message);
    }
}