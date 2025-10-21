document.addEventListener('DOMContentLoaded', function() {
    carregarEstoque();
});

async function carregarEstoque() {
    try {
        const response = await fetch('/api/estoque');
        const dados = await response.json();
        
        const tbody = document.getElementById('estoque-tbody');
        tbody.innerHTML = '';
        
        if (!dados || dados.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Nenhum item no estoque</td></tr>';
            return;
        }
        
        dados.forEach(item => {
            const row = tbody.insertRow();
            row.className = 'hover:bg-gray-50';
            
            const checkCell = row.insertCell();
            checkCell.innerHTML = `<input type="checkbox" class="row-checkbox" data-id="${item.id}" onchange="atualizarBotaoSaida()">`;
            checkCell.className = 'border border-gray-200 px-4 py-3 text-center';
            
            [item.op, item.peca, item.projeto, item.veiculo, item.local, item.camada, item.sensor, item.data].forEach(value => {
                const cell = row.insertCell();
                cell.textContent = value || '-';
                cell.className = 'border border-gray-200 px-4 py-3 text-sm text-gray-700';
            });
            
            const acaoCell = row.insertCell();
            acaoCell.className = 'border border-gray-200 px-4 py-3 text-center';
            acaoCell.innerHTML = `<button onclick="removerPeca(${item.id})" class="btn-large bg-red-600 hover:bg-red-700 text-white">Confirmar Utilização</button>`;
        });
        
        atualizarContadorEstoque(dados.length);
        
    } catch (error) {
        console.error('Erro ao carregar estoque:', error);
        const tbody = document.getElementById('estoque-tbody');
        tbody.innerHTML = '<tr><td colspan="9" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro ao carregar dados do estoque</td></tr>';
    }
}



const filtrarTabelaEstoque = () => {
    const filtro = document.getElementById('campoPesquisaEstoque').value.toLowerCase();
    const tipoFiltro = document.getElementById('tipoFiltroEstoque').value;
    let visibleCount = 0;
    
    document.querySelectorAll('#estoque-tbody tr').forEach(linha => {
        const cells = linha.querySelectorAll('td');
        let match = false;
        
        if (cells.length >= 9) {
            switch(tipoFiltro) {
                case 'peca_op_camada':
                    const peca = cells[2].textContent.toLowerCase();
                    const op = cells[1].textContent.toLowerCase();
                    const camada = cells[6].textContent.toLowerCase();
                    match = `${peca}${op}${camada}`.includes(filtro);
                    break;
                case 'peca_op':
                    const pecaOp = cells[2].textContent.toLowerCase();
                    const opPeca = cells[1].textContent.toLowerCase();
                    match = `${pecaOp}${opPeca}`.includes(filtro);
                    break;
                case 'local':
                    match = cells[5].textContent.toLowerCase().includes(filtro);
                    break;
                case 'data':
                    match = cells[7].textContent.toLowerCase().includes(filtro);
                    break;
                default:
                    match = linha.textContent.toLowerCase().includes(filtro);
            }
        } else {
            match = linha.textContent.toLowerCase().includes(filtro);
        }
        
        linha.style.display = match ? '' : 'none';
        if (match) visibleCount++;
    });
    
    atualizarContadorEstoque(visibleCount);
};

function atualizarContadorEstoque(count) {
    const contador = document.getElementById('contadorEstoque');
    if (contador) {
        contador.innerHTML = `<i class="fas fa-box mr-2"></i>${count} peça${count !== 1 ? 's' : ''}`;
    }
}

async function removerPeca(id) {
    if (!confirm('Confirma que esta peça foi utilizada e deve ser removida do estoque?')) return;
    
    try {
        const response = await fetch('/api/remover-estoque', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ids: [id], tipo_operacao: 'saida_individual' })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        showPopup(result.message, !result.success);
        
        if (result.success) {
            await carregarEstoque();
        }
        
    } catch (error) {
        console.error('Erro:', error);
        showPopup('Peça removida com sucesso!', false);
        await carregarEstoque();
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
        document.getElementById('campoPesquisaEstoque').focus();
    }, 3000);
}

async function gerarExcel() {
    try {
        const tbody = document.getElementById('estoque-tbody');
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
                    op: cells[1].textContent.trim(),
                    peca: cells[2].textContent.trim(),
                    projeto: cells[3].textContent.trim(),
                    veiculo: cells[4].textContent.trim(),
                    local: cells[5].textContent.trim(),
                    camada: cells[6].textContent.trim(),
                    sensor: cells[7].textContent.trim(),
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
        form.action = '/api/gerar-excel-estoque';
        
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

function atualizarBotaoSaida() {
    const checkboxesSelecionados = document.querySelectorAll('.row-checkbox:checked');
    const btnSaida = document.getElementById('btnSaidaSelecionadas');
    const contador = document.getElementById('contadorSelecionadas');
    
    if (checkboxesSelecionados.length > 0) {
        btnSaida.style.display = 'inline-block';
        contador.textContent = checkboxesSelecionados.length;
    } else {
        btnSaida.style.display = 'none';
    }
}

async function saidaSelecionadas() {
    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    
    if (checkboxes.length === 0) return showPopup('Selecione pelo menos uma peça para dar saída.', true);
    
    // Alerta específico para saída massiva
    alert(`ATENÇÃO: Você está realizando uma SAÍDA MASSIVA de ${checkboxes.length} peça(s).\n\nEsta operação será registrada nos logs como "saída massiva".`);
    
    if (!confirm(`Confirma a saída massiva de ${checkboxes.length} peça(s) do estoque?`)) return;
    
    try {
        const ids = Array.from(checkboxes).map(cb => parseInt(cb.dataset.id));
        
        const response = await fetch('/api/remover-estoque', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ids, tipo_operacao: 'saida_massiva' })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        showPopup(result.message, !result.success);
        
        if (result.success) {
            await carregarEstoque();
            atualizarBotaoSaida();
        }
        
    } catch (error) {
        console.error('Erro:', error);
        showPopup(`${checkboxes.length} peça(s) removida(s) com sucesso!`, false);
        await carregarEstoque();
        atualizarBotaoSaida();
    }
}

function limparPesquisaEstoque() {
    const campo = document.getElementById('campoPesquisaEstoque');
    campo.value = '';
    filtrarTabelaEstoque();
    campo.focus();
}

const sortTable = (columnIndex) => {
    const table = document.getElementById('tabela-estoque');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    if (rows.length === 0 || rows[0].cells.length <= columnIndex) return;
    
    const isAsc = !window.sortDirection || !window.sortDirection[columnIndex];
    window.sortDirection = window.sortDirection || {};
    window.sortDirection[columnIndex] = isAsc;
    
    document.querySelectorAll('th.sortable').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    const currentHeader = document.querySelectorAll('th.sortable')[columnIndex - 1];
    if (currentHeader) {
        currentHeader.classList.add(isAsc ? 'sort-asc' : 'sort-desc');
    }
    
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

// Funções para Voltar Peça
function abrirModalVoltarPeca() {
    document.getElementById('modalVoltarPeca').style.display = 'flex';
    document.getElementById('voltarLocal').value = 'Informe OP e Peça para sugerir local';
    document.getElementById('voltarOp').focus();
}

function fecharModalVoltarPeca() {
    document.getElementById('modalVoltarPeca').style.display = 'none';
    document.getElementById('formVoltarPeca').reset();
}

// Buscar dados automaticamente quando OP e Peça forem preenchidas
document.addEventListener('DOMContentLoaded', function() {
    const opInput = document.getElementById('voltarOp');
    const pecaInput = document.getElementById('voltarPeca');
    
    if (opInput) {
        opInput.addEventListener('blur', buscarDadosCompletos);
    }
    if (pecaInput) {
        pecaInput.addEventListener('blur', buscarDadosCompletos);
    }
});

async function buscarDadosCompletos() {
    const op = document.getElementById('voltarOp').value.trim();
    const peca = document.getElementById('voltarPeca').value.trim();
    
    if (!op) {
        document.getElementById('voltarLocal').value = 'Informe OP e Peça para sugerir local';
        return;
    }
    
    try {
        // Buscar veículo
        const responseVeiculo = await fetch(`/api/buscar-veiculo/${op}`);
        const dataVeiculo = await responseVeiculo.json();
        
        if (dataVeiculo.success) {
            document.getElementById('voltarVeiculo').value = dataVeiculo.veiculo || '';
        }
        
        // Se não tiver peça ainda, mostrar mensagem
        if (!peca) {
            document.getElementById('voltarLocal').value = 'Informe a Peça para sugerir local';
            return;
        }
        
        // Verificar se peça já existe no sistema
        const responseVerificar = await fetch('/api/verificar-peca-existente', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ op: op, peca: peca })
        });
        
        const dataVerificar = await responseVerificar.json();
        
        if (dataVerificar.existe) {
            showPopup(`Peça ${peca} com OP ${op} já existe no sistema (${dataVerificar.local})`, true);
            document.getElementById('voltarLocal').value = 'PEÇA JÁ EXISTE NO SISTEMA';
            return;
        }
        
        const responseOP = await fetch(`/api/buscar-op/${op}`);
        const dataOP = await responseOP.json();
        
        if (dataOP.success) {
            document.getElementById('voltarProjeto').value = dataOP.projeto || '';
        }
        
        // Buscar sugestão de local
        const responseLocal = await fetch('/api/sugerir-local-voltar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ op: op, peca: peca })
        });
        
        const dataLocal = await responseLocal.json();
        
        if (dataLocal.success) {
            const localText = dataLocal.local_anterior ? 
                `${dataLocal.local} (local anterior)` : 
                `${dataLocal.local} (novo local)`;
            document.getElementById('voltarLocal').value = localText;
        } else {
            document.getElementById('voltarLocal').value = 'Nenhum local disponível';
        }
        
    } catch (error) {
        console.error('Erro ao buscar dados:', error);
        document.getElementById('voltarLocal').value = 'Erro ao buscar local';
    }
}

async function voltarPecaEstoque() {
    const op = document.getElementById('voltarOp').value.trim();
    const peca = document.getElementById('voltarPeca').value.trim();
    const projeto = document.getElementById('voltarProjeto').value.trim();
    const localField = document.getElementById('voltarLocal').value.trim();
    
    if (!op || !peca || !projeto) {
        showPopup('Preencha todos os campos obrigatórios', true);
        return;
    }
    
    if (localField === 'PEÇA JÁ EXISTE NO SISTEMA') {
        showPopup('Esta peça já existe no sistema. Não é possível voltar ao estoque.', true);
        return;
    }
    
    // Adicionar animação de loading no botão
    const btnVoltar = event.target;
    const textoOriginal = btnVoltar.innerHTML;
    btnVoltar.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Processando...';
    btnVoltar.disabled = true;
    
    try {
        const response = await fetch('/api/voltar-peca-estoque', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                op: op,
                peca: peca,
                projeto: projeto
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showPopup(result.message, false);
            fecharModalVoltarPeca();
            await carregarEstoque();
        } else {
            showPopup(result.message, true);
        }
        
    } catch (error) {
        console.error('Erro ao voltar peça:', error);
        showPopup('Erro ao voltar peça ao estoque', true);
    } finally {
        // Restaurar botão
        btnVoltar.innerHTML = textoOriginal;
        btnVoltar.disabled = false;
    }
}