let paginaAtual = 1;
const itensPorPagina = 20;
let timeoutBusca;

document.addEventListener('DOMContentLoaded', () => {
    carregarLogs();
    
    const campoBusca = document.getElementById('campoBusca');
    campoBusca.addEventListener('input', () => {
        clearTimeout(timeoutBusca);
        timeoutBusca = setTimeout(() => {
            carregarLogs(1);
        }, 300);
    });
});

async function carregarLogs(pagina = 1) {
    paginaAtual = pagina;
    const tbody = document.getElementById('logs-tbody');
    
    try {
        const params = new URLSearchParams({
            page: pagina,
            limit: itensPorPagina
        });
        
        const busca = document.getElementById('campoBusca').value;
        if (busca) params.append('busca', busca);
        
        const response = await fetch(`/api/logs?${params}`);
        const data = await response.json();
        
        tbody.innerHTML = '';
        
        if (data.error) {
            tbody.innerHTML = `<tr><td colspan="4" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro: ${data.error}</td></tr>`;
            return;
        }
        
        if (data.dados.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Nenhum log encontrado</td></tr>';
            return;
        }
        
        data.dados.forEach(log => {
            const row = tbody.insertRow();
            row.className = 'hover:bg-gray-50';
            
            const dataFormatada = new Date(log.data_acao).toLocaleString('pt-BR');
            
            [dataFormatada, log.usuario, log.acao, log.detalhes].forEach(value => {
                const cell = row.insertCell();
                cell.textContent = value || '-';
                cell.className = 'border border-gray-200 px-4 py-3 text-sm text-gray-700';
            });
        });
        
        criarPaginacao(data.pagination);
        
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="4" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro ao carregar logs</td></tr>';
    }
}

function criarPaginacao(pagination) {
    const container = document.getElementById('paginacao');
    container.innerHTML = '';
    
    if (pagination.total_pages <= 1) return;
    
    // Botão Anterior
    const btnAnterior = document.createElement('button');
    btnAnterior.textContent = 'Anterior';
    btnAnterior.className = 'btn-pagination';
    btnAnterior.disabled = pagination.current_page === 1;
    btnAnterior.onclick = () => carregarLogs(pagination.current_page - 1);
    container.appendChild(btnAnterior);
    
    // Números das páginas
    const inicio = Math.max(1, pagination.current_page - 2);
    const fim = Math.min(pagination.total_pages, pagination.current_page + 2);
    
    for (let i = inicio; i <= fim; i++) {
        const btnPagina = document.createElement('button');
        btnPagina.textContent = i;
        btnPagina.className = `btn-pagination ${i === pagination.current_page ? 'bg-blue-600' : ''}`;
        btnPagina.onclick = () => carregarLogs(i);
        container.appendChild(btnPagina);
    }
    
    // Botão Próximo
    const btnProximo = document.createElement('button');
    btnProximo.textContent = 'Próximo';
    btnProximo.className = 'btn-pagination';
    btnProximo.disabled = pagination.current_page === pagination.total_pages;
    btnProximo.onclick = () => carregarLogs(pagination.current_page + 1);
    container.appendChild(btnProximo);
}



let sortDirection = {};

function sortTable(columnIndex) {
    const table = document.getElementById('tabela-logs');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    if (rows.length === 0 || rows[0].cells.length <= columnIndex) return;
    
    const isAsc = !sortDirection[columnIndex];
    sortDirection[columnIndex] = isAsc;
    
    document.querySelectorAll('th.sortable').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    const currentHeader = document.querySelectorAll('th.sortable')[columnIndex];
    currentHeader.classList.add(isAsc ? 'sort-asc' : 'sort-desc');
    
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex]?.textContent.trim() || '';
        const bText = b.cells[columnIndex]?.textContent.trim() || '';
        
        return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

async function gerarExcel() {
    try {
        const busca = document.getElementById('campoBusca').value;
        const params = new URLSearchParams({ page: 1, limit: 10000 });
        if (busca) params.append('busca', busca);
        
        const response = await fetch(`/api/logs?${params}`);
        const data = await response.json();
        
        if (data.error) {
            alert('Erro ao buscar dados: ' + data.error);
            return;
        }
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/api/gerar-excel-logs';
        
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'dados';
        input.value = JSON.stringify(data.dados);
        
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
        
    } catch (error) {
        alert('Erro ao gerar Excel: ' + error.message);
    }
}