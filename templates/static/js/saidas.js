let paginaAtual = 1;
let totalPaginas = 1;

document.addEventListener('DOMContentLoaded', function() {
    carregarSaidas();
});

async function carregarSaidas(pagina = 1) {
    try {
        const response = await fetch(`/api/saidas?page=${pagina}&limit=20`);
        const result = await response.json();
        
        const tbody = document.getElementById('saidas-tbody');
        tbody.innerHTML = '';
        
        if (result.error) {
            tbody.innerHTML = `<tr><td colspan="9" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro: ${result.error}</td></tr>`;
            return;
        }
        
        const dados = result.dados || [];
        
        if (dados.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Nenhuma saída registrada</td></tr>';
            document.getElementById('paginacao').style.display = 'none';
            return;
        }
        
        dados.forEach(item => {
            const row = tbody.insertRow();
            row.className = 'hover:bg-gray-50';
            
            const cells = [
                item.op_pai || '-',
                item.op || '-',
                item.peca || '-',
                item.projeto || '-',
                item.veiculo || '-',
                item.local || '-',
                item.rack || '-',
                item.usuario || '-',
                item.data ? new Date(item.data).toLocaleDateString('pt-BR') : '-'
            ];
            
            cells.forEach(value => {
                const cell = row.insertCell();
                cell.textContent = value;
                cell.className = 'border border-gray-200 px-4 py-3 text-sm text-gray-700';
            });
        });
        
        if (result.pagination) {
            paginaAtual = result.pagination.current_page;
            totalPaginas = result.pagination.total_pages;
            
            document.getElementById('infoPagina').textContent = `Página ${paginaAtual} de ${totalPaginas}`;
            document.getElementById('btnAnterior').disabled = paginaAtual <= 1;
            document.getElementById('btnProximo').disabled = paginaAtual >= totalPaginas;
            
            document.getElementById('paginacao').style.display = totalPaginas > 1 ? 'flex' : 'none';
        }
        
    } catch (error) {
        console.error('Erro:', error);
        const tbody = document.getElementById('saidas-tbody');
        tbody.innerHTML = '<tr><td colspan="9" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro ao carregar saídas</td></tr>';
    }
}

function mudarPagina(direcao) {
    const novaPagina = paginaAtual + direcao;
    if (novaPagina >= 1 && novaPagina <= totalPaginas) {
        carregarSaidas(novaPagina);
    }
}

function filtrarTabelaSaidas() {
    const filtro = document.getElementById('campoPesquisaSaidas').value.toLowerCase();
    const linhas = document.querySelectorAll('#saidas-tbody tr');
    linhas.forEach(linha => {
        const textoLinha = linha.textContent.toLowerCase();
        linha.style.display = textoLinha.includes(filtro) ? '' : 'none';
    });
}

let sortDirection = {};

const sortTable = (columnIndex) => {
    const table = document.getElementById('tabela-saidas');
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
        
        // Se for coluna de data (índice 8)
        if (columnIndex === 8 && aText.includes('/') && bText.includes('/')) {
            const [aDay, aMonth, aYear] = aText.split('/');
            const [bDay, bMonth, bYear] = bText.split('/');
            const aDate = new Date(aYear, aMonth - 1, aDay);
            const bDate = new Date(bYear, bMonth - 1, bDay);
            return isAsc ? aDate - bDate : bDate - aDate;
        }
        
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAsc ? aNum - bNum : bNum - aNum;
        }
        
        return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
    });
    
    rows.forEach(row => tbody.appendChild(row));
};

async function gerarExcel() {
    try {
        const tbody = document.getElementById('saidas-tbody');
        const rows = tbody.querySelectorAll('tr');
        
        if (rows.length === 0 || rows[0].cells[0].textContent.includes('Carregando') || rows[0].cells[0].textContent.includes('Nenhum')) {
            showPopup('Nenhum dado para exportar', true);
            return;
        }
        
        const dados = [];
        rows.forEach(row => {
            if (row.style.display !== 'none') {
                const cells = row.cells;
                dados.push({
                    op_pai: cells[0].textContent.trim(),
                    op: cells[1].textContent.trim(),
                    peca: cells[2].textContent.trim(),
                    projeto: cells[3].textContent.trim(),
                    veiculo: cells[4].textContent.trim(),
                    local: cells[5].textContent.trim(),
                    rack: cells[6].textContent.trim(),
                    usuario: cells[7].textContent.trim(),
                    data: cells[8].textContent.trim()
                });
            }
        });
        
        if (dados.length === 0) {
            showPopup('Nenhum dado filtrado para exportar', true);
            return;
        }
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/api/gerar-excel-saidas';
        
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'dados';
        input.value = JSON.stringify(dados);
        
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
        
    } catch (error) {
        showPopup('Erro ao gerar Excel: ' + error.message, true);
    }
}

function showPopup(message, isError = false) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${isError ? '#dc2626' : '#16a34a'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        font-size: 14px;
        font-weight: 600;
        max-width: 300px;
        animation: slideIn 0.3s ease-out;
    `;
    
    notification.innerHTML = `<i class="fas ${isError ? 'fa-exclamation-triangle' : 'fa-check-circle'}" style="margin-right: 8px;"></i>${message}`;
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
        style.remove();
    }, 3000);
}