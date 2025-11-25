document.addEventListener('DOMContentLoaded', function() {
    carregarEstoque();
});

async function carregarEstoque() {
    try {
        const response = await fetch('/api/estoque-agrupado');
        const dados = await response.json();
        
        const tbody = document.getElementById('estoque-tbody');
        tbody.innerHTML = '';
        
        if (!dados || dados.length === 0) {
            tbody.innerHTML = '<tr><td colspan="12" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Nenhum item no estoque</td></tr>';
            return;
        }
        
        let totalPecas = 0;
        dados.forEach((grupo, index) => {
            totalPecas += grupo.quantidade;
            
            // Linha principal do grupo
            const row = tbody.insertRow();
            row.className = 'hover:bg-gray-50 grupo-principal';
            row.dataset.grupoIndex = index;
            
            // Seta para expandir/contrair
            const expandCell = row.insertCell();
            expandCell.innerHTML = `
                <i class="fas fa-chevron-right seta-grupo cursor-pointer text-blue-500" 
                   onclick="toggleGrupo(${index})" title="Expandir/Contrair"></i>
            `;
            expandCell.className = 'border border-gray-200 px-4 py-3 text-center';
            
            // Dados do grupo
            [grupo.op, grupo.peca, grupo.projeto, grupo.veiculo, grupo.locais, grupo.camadas, grupo.lotes_pu || '-', grupo.sensores || '-', grupo.primeira_data].forEach(value => {
                const cell = row.insertCell();
                cell.textContent = value || '-';
                cell.className = 'border border-gray-200 px-4 py-3 text-sm text-gray-700';
            });
            
            // Ações do grupo (com quantidade no botão)
            const acaoCell = row.insertCell();
            acaoCell.className = 'border border-gray-200 px-4 py-3 col-acoes';
            acaoCell.innerHTML = `
                <div class="flex gap-2">
                    <button onclick="editarGrupo('${grupo.op}', '${grupo.peca}')" 
                            class="btn-editar" title="Editar grupo">
                        Editar
                    </button>
                    <button onclick="removerGrupoCompleto('${grupo.op}', '${grupo.peca}')" 
                            class="btn-saida-grupo" title="Dar saída da peça completa">
                        <i class="fas fa-sign-out-alt"></i>
                        Remover do Estoque (${grupo.quantidade})
                    </button>
                </div>
            `;
            
            // Linhas de detalhes (inicialmente ocultas)
            grupo.detalhes.forEach(detalhe => {
                const detailRow = tbody.insertRow();
                detailRow.className = 'detalhe-grupo hidden';
                detailRow.dataset.grupoIndex = index;
                
                // Célula vazia para alinhamento
                const emptyCell = detailRow.insertCell();
                emptyCell.innerHTML = '<i class="fas fa-arrow-right text-gray-400 ml-4"></i>';
                emptyCell.className = 'border border-gray-200 px-4 py-3 text-center';
                
                [detalhe.op, detalhe.peca, detalhe.projeto, detalhe.veiculo, detalhe.local, detalhe.camada || '-', detalhe.lote_pu || '-', detalhe.sensor || '-', detalhe.data ? new Date(detalhe.data).toLocaleDateString('pt-BR') : '-'].forEach(value => {
                    const cell = detailRow.insertCell();
                    cell.textContent = value || '-';
                    cell.className = 'border border-gray-200 px-4 py-3 text-sm text-gray-600 bg-gray-50';
                });
                
                // Ações individuais (sem botão de editar)
                const acaoIndCell = detailRow.insertCell();
                acaoIndCell.className = 'border border-gray-200 px-4 py-3 col-acoes bg-gray-50';
                acaoIndCell.innerHTML = `
                    <span class="text-gray-400 text-sm">Editar pelo grupo</span>
                `;
            });
        });
        
        atualizarCards();
        atualizarContadorHeader(totalPecas);
        
    } catch (error) {
        console.error('Erro ao carregar estoque:', error);
        const tbody = document.getElementById('estoque-tbody');
        tbody.innerHTML = '<tr><td colspan="12" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro ao carregar dados do estoque</td></tr>';
    }
}



const filtrarTabelaEstoque = () => {
    const filtro = document.getElementById('campoPesquisaEstoque').value.toLowerCase();
    const tipoFiltro = document.getElementById('tipoFiltroEstoque').value;
    let visibleCount = 0;
    
    document.querySelectorAll('#estoque-tbody tr').forEach(linha => {
        const cells = linha.querySelectorAll('td');
        let match = false;
        
        if (cells.length >= 10) {
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
    
    // Contar grupos visíveis
    const gruposVisiveis = document.querySelectorAll('#estoque-tbody tr.grupo-principal:not([style*="display: none"])');
    let totalPecasVisiveis = 0;
    let totalTiposVisiveis = 0;
    
    gruposVisiveis.forEach(grupo => {
        const botaoSaida = grupo.querySelector('.btn-saida-grupo');
        if (botaoSaida) {
            const match = botaoSaida.textContent.match(/\((\d+)\)/);
            if (match) {
                totalPecasVisiveis += parseInt(match[1]);
                totalTiposVisiveis++;
            }
        }
    });
    
    atualizarCardsComFiltro(totalPecasVisiveis, totalTiposVisiveis);
    atualizarContadorHeader(totalPecasVisiveis);
};

async function atualizarCards() {
    try {
        const response = await fetch('/api/estoque-estatisticas');
        const stats = await response.json();
        
        const cardsContainer = document.getElementById('cardsEstoque');
        if (cardsContainer) {
            cardsContainer.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div class="bg-white rounded-lg shadow-md p-4 border-l-4 border-blue-500">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <i class="fas fa-boxes text-blue-500 text-2xl"></i>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-gray-500">Total de Peças</p>
                                <p class="text-2xl font-bold text-gray-900">${stats.total_pecas}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-white rounded-lg shadow-md p-4 border-l-4 border-green-500">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <i class="fas fa-layer-group text-green-500 text-2xl"></i>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-gray-500">Tipos de Peças</p>
                                <p class="text-2xl font-bold text-gray-900">${stats.total_tipos}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-white rounded-lg shadow-md p-4 border-l-4 border-red-500">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <i class="fas fa-exclamation-triangle text-red-500 text-2xl"></i>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-gray-500">Pós-Montagem</p>
                                <p class="text-2xl font-bold text-gray-900">${stats.pos_montagem}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao atualizar cards:', error);
    }
}

function atualizarCardsComFiltro(totalPecas, totalTipos) {
    const cardsContainer = document.getElementById('cardsEstoque');
    if (cardsContainer) {
        cardsContainer.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div class="bg-white rounded-lg shadow-md p-4 border-l-4 border-blue-500">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-boxes text-blue-500 text-2xl"></i>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-500">Peças Filtradas</p>
                            <p class="text-2xl font-bold text-gray-900">${totalPecas}</p>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white rounded-lg shadow-md p-4 border-l-4 border-green-500">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-layer-group text-green-500 text-2xl"></i>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-500">Tipos Filtrados</p>
                            <p class="text-2xl font-bold text-gray-900">${totalTipos}</p>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white rounded-lg shadow-md p-4 border-l-4 border-orange-500">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-filter text-orange-500 text-2xl"></i>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-500">Filtro Ativo</p>
                            <p class="text-lg font-bold text-gray-900">SIM</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

function atualizarContadorHeader(totalPecas) {
    const contador = document.getElementById('contadorEstoque');
    if (contador) {
        contador.innerHTML = `<i class="fas fa-box mr-2"></i> ${totalPecas} peças`;
    }
}

function toggleGrupo(index) {
    const detalhes = document.querySelectorAll(`tr.detalhe-grupo[data-grupo-index="${index}"]`);
    const seta = document.querySelector(`tr.grupo-principal[data-grupo-index="${index}"] .seta-grupo`);
    
    detalhes.forEach(row => {
        if (row.classList.contains('hidden')) {
            row.classList.remove('hidden');
            seta.classList.remove('fa-chevron-right');
            seta.classList.add('fa-chevron-down');
        } else {
            row.classList.add('hidden');
            seta.classList.remove('fa-chevron-down');
            seta.classList.add('fa-chevron-right');
        }
    });
}

async function removerGrupoCompleto(op, peca) {
    if (!confirm(`Confirma a saída de TODAS as peças do grupo ${peca} OP ${op}?`)) return;
    
    try {
        const response = await fetch('/api/remover-grupo-estoque', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ op: op, peca: peca })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Erro HTTP ao remover grupo:', response.status, errorText);
            showPopup(`Erro HTTP ${response.status}`, true);
            return;
        }
        
        const result = await response.json();
        
        showPopup(result.message, !result.success);
        
        if (result.success) {
            await carregarEstoque();
        }
        
    } catch (error) {
        console.error('Erro completo ao remover grupo:', error);
        showPopup('Grupo removido com sucesso!', false);
        await carregarEstoque();
    }
}

async function removerPeca(id) {
    try {
        // Verificar se vão restar peças no estoque
        const responseVerificar = await fetch('/api/verificar-pecas-restantes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ids: [id] })
        });
        
        const verificacao = await responseVerificar.json();
        
        if (verificacao.success && verificacao.tem_alertas) {
            const alertas = verificacao.alertas.join('\n');
            showAlertPopup(`ATENÇÃO!\n\n${alertas}\n\nSelecione TODAS as peças desta OP antes de dar saída!`);
            return;
        }
        
        if (!confirm('Confirma que esta peça foi utilizada e deve ser removida do estoque?')) return;
        
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
        const campo = document.getElementById('campoPesquisaEstoque');
        if (campo) campo.focus();
    }, 3000);
}

function showAlertPopup(message) {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        z-index: 99999;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    const popup = document.createElement('div');
    popup.style.cssText = `
        background: #dc2626;
        color: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        max-width: 500px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        animation: blinkAlert 1s infinite;
        border: 3px solid #fff;
    `;
    
    popup.innerHTML = `
        <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 20px; display: block;"></i>
        <div style="white-space: pre-line; margin-bottom: 25px;">${message}</div>
        <button onclick="this.closest('div').parentElement.remove()" style="
            background: white;
            color: #dc2626;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            font-size: 16px;
        ">ENTENDI</button>
    `;
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes blinkAlert {
            0%, 50% { background: #dc2626; }
            51%, 100% { background: #b91c1c; }
        }
    `;
    document.head.appendChild(style);
    
    overlay.appendChild(popup);
    document.body.appendChild(overlay);
    
    // Remover estilo após fechar
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
            style.remove();
        }
    });
}

async function gerarExcel() {
    try {
        const filtro = document.getElementById('campoPesquisaEstoque').value.toLowerCase();
        const tipoFiltro = document.getElementById('tipoFiltroEstoque').value;
        
        const params = new URLSearchParams();
        if (filtro) params.append('filtro', filtro);
        if (tipoFiltro) params.append('tipo_filtro', tipoFiltro);
        
        const url = `/api/gerar-excel-estoque?${params.toString()}`;
        window.open(url, '_blank');
        
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
    
    try {
        const ids = Array.from(checkboxes).map(cb => parseInt(cb.dataset.id));
        
        // Verificar se vão restar peças no estoque
        const responseVerificar = await fetch('/api/verificar-pecas-restantes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ids })
        });
        
        const verificacao = await responseVerificar.json();
        
        if (verificacao.success && verificacao.tem_alertas) {
            const alertas = verificacao.alertas.join('\n');
            showAlertPopup(`ATENÇÃO!\n\n${alertas}\n\nSelecione TODAS as peças desta OP antes de dar saída!`);
            return;
        }
        
        // Alerta específico para saída massiva
        alert(`ATENÇÃO: Você está realizando uma SAÍDA MASSIVA de ${checkboxes.length} peça(s).\n\nEsta operação será registrada nos logs como "saída massiva".`);
        
        if (!confirm(`Confirma a saída massiva de ${checkboxes.length} peça(s) do estoque?`)) return;
        
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
    
    // Mostrar todas as linhas
    document.querySelectorAll('#estoque-tbody tr').forEach(linha => {
        linha.style.display = '';
    });
    
    // Voltar aos cards originais
    atualizarCards();
    
    // Contar total de peças novamente
    const gruposVisiveis = document.querySelectorAll('#estoque-tbody tr.grupo-principal');
    let totalPecas = 0;
    gruposVisiveis.forEach(grupo => {
        const botaoSaida = grupo.querySelector('.btn-saida-grupo');
        if (botaoSaida) {
            const match = botaoSaida.textContent.match(/\((\d+)\)/);
            if (match) {
                totalPecas += parseInt(match[1]);
            }
        }
    });
    atualizarContadorHeader(totalPecas);
    
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
        
        // Se for coluna de data (índice 9)
        if (columnIndex === 9 && aText.includes('/') && bText.includes('/')) {
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

// Funções para Editar Grupo
function editarGrupo(op, peca) {
    const tbody = document.getElementById('estoque-tbody');
    const rows = tbody.querySelectorAll('tr.grupo-principal');
    
    for (let row of rows) {
        const cells = row.cells;
        if (cells[1].textContent.trim() === op && cells[2].textContent.trim() === peca) {
            // Armazenar valores originais para referência
            document.getElementById('editarOp').value = cells[1].textContent.trim();
            document.getElementById('editarPecaCodigo').value = cells[2].textContent.trim();
            document.getElementById('editarProjeto').value = cells[3].textContent.trim();
            document.getElementById('editarVeiculo').value = cells[4].textContent.trim();
            document.getElementById('editarSensor').value = cells[8].textContent.trim() === '-' ? '' : cells[8].textContent.trim();
            
            // Armazenar valores originais como atributos de dados
            document.getElementById('editarOp').dataset.originalOp = op;
            document.getElementById('editarPecaCodigo').dataset.originalPeca = peca;
            
            document.getElementById('modalEditarPeca').style.display = 'flex';
            document.getElementById('editarOp').focus();
            break;
        }
    }
}

function fecharModalEditarPeca() {
    document.getElementById('modalEditarPeca').style.display = 'none';
    document.getElementById('formEditarPeca').reset();
}

async function salvarEdicaoPeca() {
    const opNova = document.getElementById('editarOp').value.trim();
    const pecaNova = document.getElementById('editarPecaCodigo').value.trim();
    const projeto = document.getElementById('editarProjeto').value.trim();
    const veiculo = document.getElementById('editarVeiculo').value.trim();
    const sensor = document.getElementById('editarSensor').value.trim();
    
    // Pegar valores originais
    const opOriginal = document.getElementById('editarOp').dataset.originalOp;
    const pecaOriginal = document.getElementById('editarPecaCodigo').dataset.originalPeca;
    
    if (!opNova || !pecaNova || !projeto || !veiculo) {
        showPopup('Todos os campos obrigatórios devem ser preenchidos', true);
        return;
    }
    
    try {
        console.log('Enviando dados:', { 
            op_original: opOriginal, 
            peca_original: pecaOriginal,
            op_nova: opNova, 
            peca_nova: pecaNova, 
            projeto, 
            veiculo, 
            sensor 
        });
        
        const response = await fetch('/api/editar-peca-estoque/grupo', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                op_original: opOriginal,
                peca_original: pecaOriginal,
                op: opNova,
                peca: pecaNova,
                projeto: projeto,
                veiculo: veiculo,
                sensor: sensor
            })
        });
        
        console.log('Status da resposta:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Erro HTTP:', response.status, errorText);
            showPopup(`Erro HTTP ${response.status}: ${errorText}`, true);
            return;
        }
        
        const result = await response.json();
        console.log('Resultado:', result);
        
        if (result.success) {
            showPopup(result.message, false);
            fecharModalEditarPeca();
            await carregarEstoque();
        } else {
            showPopup(result.message || 'Erro desconhecido', true);
        }
        
    } catch (error) {
        console.error('Erro completo ao editar grupo:', error);
        showPopup(`Erro ao editar grupo: ${error.message}`, true);
    }
}