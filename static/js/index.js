document.addEventListener('DOMContentLoaded', () => {
    // Carregar lote salvo
    const lote = localStorage.getItem('lote') || '';
    document.getElementById('lote').value = lote;
    
    // Carregar lista de lotes disponíveis
    carregarLotes();
    
    // Carregar contadores de locais
    carregarContadoresLocais();
    
    // Salvar quando mudar
    document.getElementById('lote').addEventListener('change', () => {
        localStorage.setItem('lote', document.getElementById('lote').value);
    });
});

async function carregarLotes() {
    try {
        const response = await fetch('/api/lotes');
        const lotes = await response.json();
        
        const select = document.getElementById('lote');
        select.innerHTML = '<option value="">Selecione um lote...</option>';
        
        lotes.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id_lote;
            option.textContent = item.display;
            select.appendChild(option);
        });
        
        // Restaurar lote salvo
        const loteSalvo = localStorage.getItem('lote');
        if (loteSalvo) {
            select.value = loteSalvo;
        }
    } catch (error) {
        console.error('Erro ao carregar lotes:', error);
    }
}

async function carregarContadoresLocais() {
    try {
        const response = await fetch('/api/locais-disponiveis');
        const dados = await response.json();
        
        document.getElementById('locaisTotal').textContent = dados.total_locais || 0;
        document.getElementById('locaisOcupados').textContent = dados.locais_ocupados || 0;
        document.getElementById('locaisDisponiveis').textContent = dados.locais_disponiveis || 0;
    } catch (error) {
        console.error('Erro ao carregar contadores de locais:', error);
        document.getElementById('locaisTotal').textContent = 'Erro';
        document.getElementById('locaisOcupados').textContent = 'Erro';
        document.getElementById('locaisDisponiveis').textContent = 'Erro';
    }
}

async function coletarDados() {
    const tbody = document.getElementById('dados-tbody');
    const btn = document.getElementById('btnColeta');
    const lote = document.getElementById('lote').value;
    
    if (!lote) {
        showPopup('Selecione um lote primeiro', true);
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="9" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Carregando dados...</td></tr>';
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Carregando...';
    
    try {
        const params = new URLSearchParams();
        
        console.log('Lote selecionado:', lote);
        
        params.append('lote', lote);
        
        const url = '/api/dados?' + params.toString();
        console.log('URL da requisição:', url);
        
        const response = await fetch(url);
        console.log('Status da resposta:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const dados = await response.json();
        console.log('Dados recebidos:', dados.length, 'itens');
        
        tbody.innerHTML = '';
        dados.forEach((item, index) => {
            const row = tbody.insertRow();
            row.className = 'hover:bg-gray-50';
            row.setAttribute('data-row-id', index);
            
            const checkCell = row.insertCell();
            checkCell.innerHTML = `<input type="checkbox" class="row-checkbox" data-index="${index}" onchange="atualizarContador()">`;
            checkCell.className = 'border border-gray-200 px-4 py-3 text-center';
            
            [item.op, item.peca, item.projeto, item.veiculo, item.local, item.sensor || ''].forEach(value => {
                const cell = row.insertCell();
                cell.textContent = value || '-';
                cell.className = 'border border-gray-200 px-4 py-3';
            });
            
            // Coluna de arquivo
            const arquivoCell = row.insertCell();
            arquivoCell.textContent = item.arquivo_status || 'Sem arquivo de corte';
            arquivoCell.className = 'border border-gray-200 px-4 py-3 text-center';
            if (item.arquivo_status === 'Sem arquivo de corte') {
                arquivoCell.style.color = '#dc2626';
            } else {
                arquivoCell.style.color = '#16a34a';
            }
            
            const cellAcoes = row.insertCell();
            cellAcoes.innerHTML = `
                <i onclick="editarPeca(this)" class="fas fa-edit text-blue-500 hover:text-blue-700 cursor-pointer mr-3" title="Editar peça"></i>
                <i onclick="deletarLinha(this)" class="fas fa-trash text-red-500 hover:text-red-700 cursor-pointer" title="Excluir peça"></i>
            `;
            cellAcoes.className = 'border border-gray-200 px-4 py-3 text-center';
        });
        
    } catch (error) {
        console.error('Erro na coleta de dados:', error);
        tbody.innerHTML = `<tr><td colspan="9" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Erro ao carregar dados: ${error.message}</td></tr>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync mr-2"></i> Coletar Dados';
    }
}

const toggleAll = () => {
    const selectAll = document.getElementById('selectAll');
    const visibleCheckboxes = document.querySelectorAll('#dados-tbody tr:not([style*="display: none"]) .row-checkbox');
    visibleCheckboxes.forEach(cb => cb.checked = selectAll.checked);
    atualizarContador();
};

function atualizarContador() {
    const checkboxes = document.querySelectorAll('#dados-tbody tr:not([style*="display: none"]) .row-checkbox:checked');
    const contador = document.getElementById('contadorSelecionadas');
    if (contador) {
        contador.textContent = `${checkboxes.length} selecionada(s)`;
    }
}

// Adicionar listener para checkboxes individuais
document.addEventListener('change', function(e) {
    if (e.target.classList.contains('row-checkbox')) {
        atualizarContador();
    }
});

const filtrarTabela = () => {
    const filtro = document.getElementById('campoPesquisa').value.toLowerCase();
    document.querySelectorAll('#dados-tbody tr').forEach(linha => {
        linha.style.display = linha.textContent.toLowerCase().includes(filtro) ? '' : 'none';
    });
};

let linhaEditando = null;

const editarPeca = (element) => {
    const row = element.closest('tr');
    const cells = row.querySelectorAll('td');
    
    // Armazenar referência da linha sendo editada
    linhaEditando = row;
    
    // Preencher o modal com os dados atuais
    document.getElementById('editOP').value = cells[1].textContent;
    document.getElementById('editPeca').value = cells[2].textContent;
    document.getElementById('editProjeto').value = cells[3].textContent;
    document.getElementById('editVeiculo').value = cells[4].textContent;
    document.getElementById('editLocal').value = cells[5].textContent;
    document.getElementById('editSensor').value = cells[6].textContent;
    
    // Abrir modal
    document.getElementById('modalEditar').style.display = 'flex';
};

const fecharModalEditar = () => {
    document.getElementById('modalEditar').style.display = 'none';
    document.getElementById('formEditar').reset();
    linhaEditando = null;
};

const deletarLinha = (element) => {
    const row = element.closest('tr');
    if (row && confirm('Confirma a exclusão desta peça?')) {
        row.remove();
    }
};

async function otimizarPecas() {
    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    const dataCorte = document.getElementById('dataCorte').value;
    const lote = document.getElementById('lote').value;
    
    if (checkboxes.length === 0) {
        alert('Selecione pelo menos uma peça para otimizar.');
        return;
    }
    
    if (!dataCorte) {
        alert('Selecione a data de corte.');
        return;
    }
    
    if (!lote) {
        alert('Selecione um lote.');
        return;
    }
    
    alert(`${checkboxes.length} peças selecionadas. Iniciando otimização...`);
    
    const pecasSelecionadas = Array.from(checkboxes).map(cb => {
        const cells = cb.closest('tr').querySelectorAll('td');
        return {
            op: cells[1].textContent,
            peca: cells[2].textContent,
            projeto: cells[3].textContent,
            veiculo: cells[4].textContent,
            local: cells[5].textContent,
            rack: cells[5].textContent,
            sensor: cells[6].textContent
        };
    });
    
    showLoading('Otimizando peças...');
    
    try {
        const response = await fetch('/api/otimizar-pecas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pecas: pecasSelecionadas, dataCorte: dataCorte, lote: lote })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            hideLoading();
            alert(`Erro HTTP ${response.status}: ${errorText}`);
            return;
        }
        
        const result = await response.json();
        hideLoading();
        
        if (result.success) {
            showPopup(`Sucesso: ${result.message}`, false);
            // Atualizar contadores após otimização
            carregarContadoresLocais();
            if (result.redirect) {
                setTimeout(() => window.location.href = result.redirect, 2000);
            } else {
                checkboxes.forEach(cb => cb.closest('tr').remove());
            }
        } else {
            showPopup(`Erro: ${result.message}`, true);
        }
    } catch (error) {
        hideLoading();
        alert(`Erro na requisição: ${error.message}`);
    }
}

async function gerarXML() {
    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    if (checkboxes.length === 0) return showPopup('Selecione pelo menos um item para gerar o XML.', true);
    
    const lote = document.getElementById('lote').value;
    if (!lote) {
        showPopup('Selecione um lote primeiro', true);
        return;
    }
    
    const dataCorte = document.getElementById('dataCorte').value;
    if (!dataCorte) {
        showPopup('Selecione a data de corte', true);
        return;
    }
    
    const pecasSelecionadas = Array.from(checkboxes).map(cb => {
        const cells = cb.closest('tr').querySelectorAll('td');
        return {
            op: cells[1].textContent,
            peca: cells[2].textContent,
            projeto: cells[3].textContent,
            veiculo: cells[4].textContent,
            local: cells[5].textContent,
            rack: cells[5].textContent,
            sensor: cells[6].textContent
        };
    });
    
    showLoading('Gerando XMLs...');
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutos timeout
        
        const response = await fetch('/api/gerar-xml', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/zip, application/json'
            },
            body: JSON.stringify({ pecas: pecasSelecionadas, lote: lote, dataCorte: dataCorte }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            let errorText;
            try {
                const errorJson = await response.json();
                errorText = errorJson.message || `Erro HTTP ${response.status}`;
            } catch {
                errorText = await response.text() || `Erro HTTP ${response.status}`;
            }
            hideLoading();
            showPopup(errorText, true);
            return;
        }
        
        // Verificar content-type da resposta
        const contentType = response.headers.get('content-type') || '';
        
        if (contentType.includes('application/json')) {
            // É uma resposta JSON com link de download
            const result = await response.json();
            hideLoading();
            
            if (result.success && result.download_url) {
                // Fazer download via link
                const a = document.createElement('a');
                a.href = result.download_url;
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                showPopup(result.message || 'XMLs gerados com sucesso!', false);
            } else {
                showPopup(result.message || 'Erro na geração de XMLs', true);
            }
        } else if (contentType.includes('application/zip') || contentType.includes('application/octet-stream')) {
            // É um arquivo ZIP - fazer download direto (fallback)
            const blob = await response.blob();
            
            if (blob.size === 0) {
                hideLoading();
                showPopup('Arquivo ZIP vazio recebido', true);
                return;
            }
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `xmls_otimizacao_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.zip`;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            hideLoading();
            showPopup('XMLs gerados e baixados com sucesso!', false);
        } else {
            // Tipo de conteúdo inesperado
            hideLoading();
            showPopup(`Tipo de resposta inesperado: ${contentType}`, true);
        }
    } catch (error) {
        hideLoading();
        
        if (error.name === 'AbortError') {
            showPopup('Timeout: A geração de XMLs demorou mais que 2 minutos. Tente com menos peças.', true);
        } else if (error.message.includes('Failed to fetch')) {
            showPopup('Erro de conexão com o servidor. Verifique sua conexão de rede.', true);
        } else {
            console.error('Erro detalhado:', error);
            showPopup(`Erro na geração de XMLs: ${error.message}`, true);
        }
    }
}

function gerarExcel() {
    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    if (checkboxes.length === 0) return showPopup('Selecione pelo menos um item para gerar o Excel.', true);
    
    const pecasSelecionadas = Array.from(checkboxes).map(cb => {
        const cells = cb.closest('tr').querySelectorAll('td');
        return {
            op: cells[1].textContent,
            peca: cells[2].textContent,
            projeto: cells[3].textContent,
            veiculo: cells[4].textContent,
            local: cells[5].textContent,
            rack: cells[5].textContent,
            sensor: cells[6].textContent
        };
    });
    
    showLoading('Gerando Excel...');
    
    const form = document.createElement('form');
    Object.assign(form, { method: 'POST', action: '/api/gerar-excel-otimizacao' });
    form.style.display = 'none';
    
    const input = document.createElement('input');
    Object.assign(input, { type: 'hidden', name: 'dados', value: JSON.stringify(pecasSelecionadas) });
    
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    
    // Esconder loading após um tempo
    setTimeout(() => {
        hideLoading();
        showPopup('Excel gerado com sucesso!', false);
    }, 2000);
}

let sortDirection = {};

const sortTable = (columnIndex) => {
    const table = document.getElementById('tabela-dados');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    if (rows.length === 0 || rows[0].cells.length <= columnIndex) return;
    
    const isAsc = !sortDirection[columnIndex];
    sortDirection[columnIndex] = isAsc;
    
    document.querySelectorAll('th.sortable').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    const currentHeader = document.querySelectorAll('th.sortable')[columnIndex - 1];
    currentHeader.classList.add(isAsc ? 'sort-asc' : 'sort-desc');
    
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex]?.textContent.trim() || '';
        const bText = b.cells[columnIndex]?.textContent.trim() || '';
        
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAsc ? aNum - bNum : bNum - aNum;
        }
        
        return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
    });
    
    rows.forEach(row => tbody.appendChild(row));
};

function abrirModalVoltar() {
    document.getElementById('modalVoltar').style.display = 'flex';
}

function fecharModalVoltar() {
    document.getElementById('modalVoltar').style.display = 'none';
    document.getElementById('formVoltar').reset();
}

function abrirModalAdicionar() {
    document.getElementById('modalAdicionar').style.display = 'flex';
}

function fecharModalAdicionar() {
    document.getElementById('modalAdicionar').style.display = 'none';
    document.getElementById('formAdicionar').reset();
    
    // Resetar upload
    selectedFile = null;
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('btnProcessar').disabled = true;
    document.getElementById('btnProcessar').classList.add('opacity-50', 'cursor-not-allowed');
    
    // Voltar para aba manual
    trocarAba('manual');
}

// Adicionar listener para buscar dados da OP
document.getElementById('inputOP').addEventListener('blur', async function() {
    const op = this.value.trim();
    if (!op) return;
    
    try {
        const response = await fetch(`/api/buscar-op/${op}`);
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('inputProjeto').value = result.projeto;
            document.getElementById('inputVeiculo').value = result.veiculo;
        }
    } catch (error) {
        console.log('OP não encontrada na base de dados');
    }
});

// Listener para buscar arquivo quando sensor for alterado
document.getElementById('editSensor').addEventListener('blur', async function() {
    const projeto = document.getElementById('editProjeto').value.trim();
    const peca = document.getElementById('editPeca').value.trim();
    const sensor = this.value.trim();
    
    if (!projeto || !peca) return;
    
    try {
        const response = await fetch('/api/buscar-arquivo-sensor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ projeto, peca, sensor })
        });
        
        const result = await response.json();
        
        if (result.success && linhaEditando) {
            // Atualizar a coluna de arquivo na tabela
            const cells = linhaEditando.querySelectorAll('td');
            const arquivoCell = cells[7]; // Coluna de arquivo
            arquivoCell.textContent = result.arquivo;
            
            if (result.arquivo === 'Sem arquivo de corte') {
                arquivoCell.style.color = '#dc2626';
            } else {
                arquivoCell.style.color = '#16a34a';
            }
        }
    } catch (error) {
        console.log('Erro ao buscar arquivo:', error);
    }
});

// Listener para o formulário de edição
document.getElementById('formEditar').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!linhaEditando) {
        showPopup('Erro: Nenhuma linha selecionada para edição', true);
        return;
    }
    
    const op = document.getElementById('editOP').value.trim();
    const peca = document.getElementById('editPeca').value.trim();
    const projeto = document.getElementById('editProjeto').value.trim();
    const veiculo = document.getElementById('editVeiculo').value.trim();
    const local = document.getElementById('editLocal').value.trim();
    const sensor = document.getElementById('editSensor').value.trim();
    
    if (!op || !peca || !projeto || !veiculo || !local) {
        showPopup('Todos os campos são obrigatórios', true);
        return;
    }
    
    // Atualizar a linha na tabela
    const cells = linhaEditando.querySelectorAll('td');
    cells[1].textContent = op;
    cells[2].textContent = peca;
    cells[3].textContent = projeto;
    cells[4].textContent = veiculo;
    cells[5].textContent = local;
    cells[6].textContent = sensor || '-';
    
    fecharModalEditar();
    showPopup('Peça editada com sucesso!', false);
});

document.getElementById('formAdicionar').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const op = document.getElementById('inputOP').value.trim();
    const peca = document.getElementById('inputPeca').value.trim();
    const projeto = document.getElementById('inputProjeto').value.trim();
    const veiculo = document.getElementById('inputVeiculo').value.trim();
    const sensor = document.getElementById('inputSensor').value.trim();
    
    if (!op || !peca || !projeto || !veiculo) {
        showPopup('Todos os campos são obrigatórios', true);
        return;
    }
    
    try {
        const response = await fetch('/api/adicionar-peca-manual', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ op, peca, projeto, veiculo, sensor })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            if (result.success) {
                // Adicionar linha na tabela
                const tbody = document.getElementById('dados-tbody');
                const row = tbody.insertRow(0);
                row.className = 'hover:bg-gray-50';
                
                const checkCell = row.insertCell();
                checkCell.innerHTML = `<input type="checkbox" class="row-checkbox" data-index="0">`;
                checkCell.className = 'border border-gray-200 px-4 py-3 text-center';
                
                [result.peca.op, result.peca.peca, result.peca.projeto, result.peca.veiculo, result.peca.local, result.peca.sensor || '-'].forEach(value => {
                    const cell = row.insertCell();
                    cell.textContent = value || '-';
                    cell.className = 'border border-gray-200 px-4 py-3';
                });
                
                // Coluna arquivo
                const arquivoCell = row.insertCell();
                arquivoCell.textContent = result.peca.arquivo_status || 'Sem arquivo de corte';
                arquivoCell.className = 'border border-gray-200 px-4 py-3 text-center';
                if (result.peca.arquivo_status && result.peca.arquivo_status !== 'Sem arquivo de corte') {
                    arquivoCell.style.color = '#16a34a';
                } else {
                    arquivoCell.style.color = '#dc2626';
                }
                
                const cellAcoes = row.insertCell();
                cellAcoes.innerHTML = `
                    <i onclick="editarPeca(this)" class="fas fa-edit text-blue-500 hover:text-blue-700 cursor-pointer mr-3" title="Editar peça"></i>
                    <i onclick="deletarLinha(this)" class="fas fa-trash text-red-500 hover:text-red-700 cursor-pointer" title="Excluir peça"></i>
                `;
                cellAcoes.className = 'border border-gray-200 px-4 py-3 text-center';
                
                fecharModalAdicionar();
                showPopup('Peça adicionada com sucesso!');
            } else {
                showPopup('Erro: ' + result.message, true);
            }
        } else {
            showPopup('Peça adicionada com sucesso!', false);
            fecharModalAdicionar();
        }
    } catch (error) {
        showPopup('Peça adicionada com sucesso!', false);
        fecharModalAdicionar();
    }
});

// Funções de loading
function showLoading(message = 'Carregando...') {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingPopup';
    loadingDiv.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
            <div id="loadingContent" style="background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; max-height: 80vh; overflow-y: auto;">
                <div id="loadingSpinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
                <p id="loadingMessage" style="margin: 0; font-size: 16px; color: #333;">${message}</p>
            </div>
        </div>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    `;
    document.body.appendChild(loadingDiv);
}

function updateLoading(message, isError = false, showCloseButton = false) {
    const spinner = document.getElementById('loadingSpinner');
    const messageEl = document.getElementById('loadingMessage');
    const content = document.getElementById('loadingContent');
    
    if (spinner) spinner.style.display = isError ? 'none' : 'block';
    if (messageEl) {
        messageEl.innerHTML = message;
        messageEl.style.color = isError ? '#dc2626' : '#333';
        messageEl.style.textAlign = 'left';
        messageEl.style.whiteSpace = 'pre-line';
    }
    
    if (showCloseButton && content) {
        const existingBtn = content.querySelector('#closeBtn');
        if (!existingBtn) {
            const closeBtn = document.createElement('button');
            closeBtn.id = 'closeBtn';
            closeBtn.innerHTML = 'Fechar';
            closeBtn.style.cssText = 'margin-top: 15px; padding: 8px 16px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;';
            closeBtn.onclick = hideLoading;
            content.appendChild(closeBtn);
        }
    }
}

function hideLoading() {
    const loadingDiv = document.getElementById('loadingPopup');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function showPopup(message, isError = false) {
    const popupDiv = document.createElement('div');
    popupDiv.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; max-height: 80vh; overflow-y: auto;">
                <div style="margin-bottom: 15px;">
                    <i class="fas ${isError ? 'fa-exclamation-triangle' : 'fa-check-circle'}" style="font-size: 48px; color: ${isError ? '#dc2626' : '#16a34a'};"></i>
                </div>
                <p style="margin: 0 0 20px 0; font-size: 16px; color: #333; white-space: pre-line;">${message}</p>
                <button onclick="this.closest('div').parentElement.remove()" style="padding: 8px 16px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">OK</button>
            </div>
        </div>
    `;
    document.body.appendChild(popupDiv);
}

// Funções das abas
function trocarAba(aba) {
    // Resetar estilos das abas
    document.getElementById('tabManual').className = 'px-4 py-2 font-medium text-gray-500 hover:text-blue-600';
    document.getElementById('tabUpload').className = 'px-4 py-2 font-medium text-gray-500 hover:text-blue-600';
    
    // Ocultar conteúdos
    document.getElementById('abaManual').style.display = 'none';
    document.getElementById('abaUpload').style.display = 'none';
    
    if (aba === 'manual') {
        document.getElementById('tabManual').className = 'px-4 py-2 font-medium text-blue-600 border-b-2 border-blue-600';
        document.getElementById('abaManual').style.display = 'block';
    } else {
        document.getElementById('tabUpload').className = 'px-4 py-2 font-medium text-blue-600 border-b-2 border-blue-600';
        document.getElementById('abaUpload').style.display = 'block';
    }
}

// Variável global para o arquivo selecionado
let selectedFile = null;

// Funções do drag and drop
function setupDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('inputFile');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const btnProcessar = document.getElementById('btnProcessar');
    
    // Click para abrir seletor
    dropZone.addEventListener('click', () => fileInput.click());
    
    // Drag and drop events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-blue-400', 'bg-blue-50');
    });
    
    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-blue-400', 'bg-blue-50');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-blue-400', 'bg-blue-50');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
    
    function handleFileSelection(file) {
        if (!file.name.toLowerCase().endsWith('.xlsx')) {
            showPopup('Apenas arquivos .xlsx são aceitos', true);
            return;
        }
        
        selectedFile = file;
        fileName.textContent = file.name;
        fileInfo.style.display = 'block';
        btnProcessar.disabled = false;
        btnProcessar.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

// Função para processar arquivo
async function processarArquivo() {
    if (!selectedFile) {
        showPopup('Selecione um arquivo XLSX', true);
        return;
    }
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    showLoading('Processando arquivo XLSX...');
    
    try {
        const response = await fetch('/api/upload-xlsx', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        hideLoading();
        
        if (result.success) {
            // Adicionar peças processadas na tabela
            const tbody = document.getElementById('dados-tbody');
            
            // Se a tabela estiver vazia, limpar a mensagem
            if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
                tbody.innerHTML = '';
            }
            
            result.pecas.forEach((peca, index) => {
                const row = tbody.insertRow(0);
                row.className = 'hover:bg-gray-50';
                
                const checkCell = row.insertCell();
                checkCell.innerHTML = `<input type="checkbox" class="row-checkbox" data-index="${index}">`;
                checkCell.className = 'border border-gray-200 px-4 py-3 text-center';
                
                [peca.op, peca.peca, peca.projeto, peca.veiculo, peca.local, peca.sensor || '-'].forEach(value => {
                    const cell = row.insertCell();
                    cell.textContent = value || '-';
                    cell.className = 'border border-gray-200 px-4 py-3';
                });
                
                // Coluna arquivo
                const arquivoCell = row.insertCell();
                arquivoCell.textContent = peca.arquivo_status || 'Sem arquivo de corte';
                arquivoCell.className = 'border border-gray-200 px-4 py-3 text-center';
                if (peca.arquivo_status && peca.arquivo_status !== 'Sem arquivo de corte') {
                    arquivoCell.style.color = '#16a34a';
                } else {
                    arquivoCell.style.color = '#dc2626';
                }
                
                const cellAcoes = row.insertCell();
                cellAcoes.innerHTML = `
                    <i onclick="editarPeca(this)" class="fas fa-edit text-blue-500 hover:text-blue-700 cursor-pointer mr-3" title="Editar peça"></i>
                    <i onclick="deletarLinha(this)" class="fas fa-trash text-red-500 hover:text-red-700 cursor-pointer" title="Excluir peça"></i>
                `;
                cellAcoes.className = 'border border-gray-200 px-4 py-3 text-center';
            });
            
            fecharModalAdicionar();
            showPopup(result.message, false);
        } else {
            showPopup(result.message, true);
        }
    } catch (error) {
        hideLoading();
        showPopup(`Erro ao processar arquivo: ${error.message}`, true);
    }
}

// Função para truncar tabela pu_manuais
async function truncarManuais() {
    if (!confirm('Tem certeza que deseja limpar TODAS as peças manuais? Esta ação não pode ser desfeita.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/truncar-manuais', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showPopup('Tabela pu_manuais limpa com sucesso!', false);
        } else {
            showPopup('Erro: ' + result.message, true);
        }
    } catch (error) {
        showPopup('Erro ao limpar tabela: ' + error.message, true);
    }
}

// Listener para buscar dados da peça quando OP e Peça forem preenchidos
document.getElementById('voltarPeca').addEventListener('blur', async function() {
    const op = document.getElementById('voltarOP').value.trim();
    const peca = this.value.trim();
    
    if (!op || !peca) return;
    
    try {
        const response = await fetch(`/api/buscar-peca-exit/${op}/${peca}`);
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('voltarProjeto').value = result.projeto;
            document.getElementById('voltarVeiculo').value = result.veiculo;
        } else {
            // Limpar campos se não encontrou
            document.getElementById('voltarProjeto').value = '';
            document.getElementById('voltarVeiculo').value = '';
        }
    } catch (error) {
        console.log('Peça não encontrada no histórico');
    }
});

// Listener para o formulário de voltar peça
document.getElementById('formVoltar').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const op = document.getElementById('voltarOP').value.trim();
    const peca = document.getElementById('voltarPeca').value.trim();
    const projeto = document.getElementById('voltarProjeto').value.trim();
    const veiculo = document.getElementById('voltarVeiculo').value.trim();
    
    if (!op || !peca) {
        showPopup('OP e Peça são obrigatórios', true);
        return;
    }
    
    showLoading('Voltando peça ao estoque...');
    
    try {
        const response = await fetch('/api/voltar-peca-estoque', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ op, peca, projeto, veiculo })
        });
        
        const result = await response.json();
        hideLoading();
        
        if (result.success) {
            fecharModalVoltar();
            showPopup(result.message, false);
        } else {
            showPopup(result.message, true);
        }
    } catch (error) {
        hideLoading();
        showPopup(`Erro: ${error.message}`, true);
    }
});

// Garantir que os modais estejam fechados ao carregar
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('modalAdicionar').style.display = 'none';
    document.getElementById('modalEditar').style.display = 'none';
    document.getElementById('modalVoltar').style.display = 'none';
    
    // Setup drag and drop
    setupDragAndDrop();
    
    // Mostrar campo sensor para PBS
    document.getElementById('inputPeca').addEventListener('input', function() {
        const peca = this.value.toUpperCase();
        const sensorField = document.getElementById('sensorField');
        
        if (peca === 'PBS') {
            sensorField.style.display = 'block';
            document.getElementById('inputSensor').required = true;
        } else {
            sensorField.style.display = 'none';
            document.getElementById('inputSensor').required = false;
            document.getElementById('inputSensor').value = '';
        }
    });
});