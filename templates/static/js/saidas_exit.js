let dadosOriginais = [];
let ordemAtual = { coluna: -1, crescente: true };
let paginaAtual = 1;
const itensPorPagina = 50;
let dadosFiltrados = [];
let pesquisaAtiva = false;

document.addEventListener('DOMContentLoaded', function() {
    carregarSaidasExit();
});

async function carregarSaidasExit() {
    try {
        const response = await fetch('/api/saidas-exit');
        const dados = await response.json();
        dadosOriginais = dados;
        
        renderizarTabela(dados);
        
    } catch (error) {
        console.error('Erro ao carregar saídas:', error);
        const tbody = document.getElementById('exit-tbody');
        tbody.innerHTML = '<tr><td colspan="9" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro ao carregar dados</td></tr>';
    }
}

function renderizarTabela(dados) {
    const tbody = document.getElementById('exit-tbody');
    tbody.innerHTML = '';
    
    if (!dados || dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Nenhuma saída encontrada</td></tr>';
        atualizarPaginacao(0, []);
        return;
    }
    
    let dadosParaExibir;
    
    if (pesquisaAtiva) {
        dadosParaExibir = dados;
    } else {
        const inicio = (paginaAtual - 1) * itensPorPagina;
        const fim = inicio + itensPorPagina;
        dadosParaExibir = dados.slice(inicio, fim);
    }
    
    dadosParaExibir.forEach(item => {
        const row = tbody.insertRow();
        row.className = 'hover:bg-gray-50';
        
        [
            item.op || '',
            item.peca || '',
            item.projeto || '',
            item.veiculo || '',
            item.local || '',
            item.rack || '',
            item.usuario || '',
            item.data || '',
            item.motivo || ''
        ].forEach(value => {
            const cell = row.insertCell();
            cell.textContent = value;
            cell.className = 'border border-gray-200 px-4 py-3 text-sm text-gray-700';
        });
    });
    
    atualizarPaginacao(dados.length, dadosParaExibir);
}

function ordenarTabela(coluna) {
    if (ordemAtual.coluna === coluna) {
        ordemAtual.crescente = !ordemAtual.crescente;
    } else {
        ordemAtual.coluna = coluna;
        ordemAtual.crescente = true;
    }
    
    const colunas = ['op', 'peca', 'projeto', 'veiculo', 'local', 'rack', 'usuario', 'data', 'motivo'];
    const propriedade = colunas[coluna];
    
    const dadosOrdenados = [...dadosOriginais].sort((a, b) => {
        let valorA = (a[propriedade] || '').toString().toLowerCase();
        let valorB = (b[propriedade] || '').toString().toLowerCase();
        
        if (coluna === 7) { // Data
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
    const filtro = document.getElementById('campoPesquisaExit').value.toLowerCase();
    
    if (!filtro) {
        pesquisaAtiva = false;
        paginaAtual = 1;
        renderizarTabela(dadosOriginais);
        return;
    }
    
    pesquisaAtiva = true;
    dadosFiltrados = dadosOriginais.filter(item => {
        const pecaOP = ((item.peca || '') + (item.op || '')).toLowerCase();
        
        return Object.values(item).some(valor => 
            (valor || '').toString().toLowerCase().includes(filtro)
        ) || pecaOP.includes(filtro);
    });
    
    renderizarTabela(dadosFiltrados);
}

function mudarPagina(direcao) {
    if (pesquisaAtiva) return;
    
    const totalPaginas = Math.ceil(dadosOriginais.length / itensPorPagina);
    const novaPagina = paginaAtual + direcao;
    
    if (novaPagina >= 1 && novaPagina <= totalPaginas) {
        paginaAtual = novaPagina;
        renderizarTabela(dadosOriginais);
    }
}

function atualizarPaginacao(totalItens, itensExibidos) {
    const infoRegistros = document.getElementById('info-registros');
    const infoPagina = document.getElementById('info-pagina');
    const btnAnterior = document.getElementById('btn-anterior');
    const btnProximo = document.getElementById('btn-proximo');
    const paginacao = document.getElementById('paginacao');
    
    if (pesquisaAtiva) {
        infoRegistros.textContent = `${totalItens} encontrado(s)`;
        infoPagina.textContent = 'Pesquisa ativa';
        btnAnterior.disabled = true;
        btnProximo.disabled = true;
        paginacao.style.display = totalItens > 0 ? 'flex' : 'none';
    } else {
        const totalPaginas = Math.ceil(dadosOriginais.length / itensPorPagina);
        const inicio = (paginaAtual - 1) * itensPorPagina + 1;
        const fim = Math.min(paginaAtual * itensPorPagina, dadosOriginais.length);
        
        infoRegistros.textContent = `${inicio}-${fim} de ${dadosOriginais.length}`;
        infoPagina.textContent = `Página ${paginaAtual} de ${totalPaginas}`;
        btnAnterior.disabled = paginaAtual === 1;
        btnProximo.disabled = paginaAtual === totalPaginas;
        paginacao.style.display = 'flex';
    }
}