// ===== INICIALIZAÇÃO DA PÁGINA =====
document.addEventListener('DOMContentLoaded', () => {
    carregarArquivos();
});

// ===== VARIÁVEIS GLOBAIS =====
let arquivosCache = [];
let sortDirection = {};

// ===== FUNÇÕES DE CARREGAMENTO =====
function carregarArquivos() {
    const tbody = document.getElementById('arquivos-tbody');
    
    tbody.innerHTML = '<tr><td colspan="8" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Carregando...</td></tr>';
    
    fetch('/api/arquivos')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(dados => {
            if (dados.error) {
                throw new Error(dados.error);
            }
            arquivosCache = dados;
            renderizarTabela(dados);
        })
        .catch(error => {
            tbody.innerHTML = `<tr><td colspan="8" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro: ${error.message}</td></tr>`;
        });
}

function renderizarTabela(dados) {
    const tbody = document.getElementById('arquivos-tbody');
    
    if (dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Nenhum arquivo encontrado</td></tr>';
        return;
    }
    
    const rows = dados.map(arquivo => `
        <tr class="hover:bg-gray-50">
            <td class="border border-gray-200 px-4 py-3">${arquivo.projeto || '-'}</td>
            <td class="border border-gray-200 px-4 py-3">${arquivo.peca || '-'}</td>
            <td class="border border-gray-200 px-4 py-3">${arquivo.nome_peca || '-'}</td>
            <td class="border border-gray-200 px-4 py-3">${arquivo.camada || '-'}</td>
            <td class="border border-gray-200 px-4 py-3">${arquivo.espessura || '-'}</td>
            <td class="border border-gray-200 px-4 py-3">${arquivo.quantidade || '-'}</td>
            <td class="border border-gray-200 px-4 py-3">${arquivo.sensor || '-'}</td>
            <td class="border border-gray-200 px-4 py-3 text-center">
                <button onclick="editarArquivo(${arquivo.id})" class="btn-action btn-blue mr-2" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="excluirArquivo(${arquivo.id})" class="btn-action btn-red" title="Excluir">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = rows;
}

// ===== FUNÇÕES DE PESQUISA E ORDENAÇÃO =====
function filtrarTabelaArquivos() {
    const filtro = document.getElementById('campoPesquisaArquivos').value.toLowerCase().trim();
    const linhas = document.querySelectorAll('#arquivos-tbody tr');
    
    linhas.forEach(linha => {
        const texto = linha.textContent.toLowerCase();
        linha.style.display = texto.includes(filtro) ? '' : 'none';
    });
}

function sortTable(columnIndex) {
    const isAsc = !sortDirection[columnIndex];
    sortDirection[columnIndex] = isAsc;
    
    // Atualizar indicadores visuais
    const headers = document.querySelectorAll('th.sortable');
    headers.forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
    
    if (headers[columnIndex]) {
        headers[columnIndex].classList.add(isAsc ? 'sort-asc' : 'sort-desc');
    }
    
    // Ordenar dados
    const colunas = ['projeto', 'peca', 'nome_peca', 'camada', 'espessura', 'quantidade', 'sensor'];
    const coluna = colunas[columnIndex];
    
    const dadosOrdenados = [...arquivosCache].sort((a, b) => {
        const aVal = a[coluna] || '';
        const bVal = b[coluna] || '';
        
        // Tentar conversão numérica
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAsc ? aNum - bNum : bNum - aNum;
        }
        
        return isAsc ? aVal.toString().localeCompare(bVal.toString()) : bVal.toString().localeCompare(aVal.toString());
    });
    
    renderizarTabela(dadosOrdenados);
}

// ===== FUNÇÕES DO MODAL =====
function abrirModalAdicionar() {
    document.getElementById('modalTitulo').textContent = 'Adicionar Arquivo';
    document.getElementById('arquivoId').value = '';
    document.getElementById('formArquivo').reset();
    document.getElementById('sensorField').style.display = 'none';
    document.getElementById('modalArquivo').style.display = 'flex';
    
    setTimeout(() => {
        document.getElementById('inputProjeto').focus();
    }, 100);
}

function editarArquivo(id) {
    const arquivo = arquivosCache.find(a => a.id === id);
    if (!arquivo) return;
    
    document.getElementById('modalTitulo').textContent = 'Editar Arquivo';
    document.getElementById('arquivoId').value = arquivo.id;
    document.getElementById('inputProjeto').value = arquivo.projeto || '';
    document.getElementById('inputPeca').value = arquivo.peca || '';
    document.getElementById('inputNomePeca').value = arquivo.nome_peca || '';
    document.getElementById('inputCamada').value = arquivo.camada || '';
    document.getElementById('inputEspessura').value = arquivo.espessura || '';
    document.getElementById('inputQuantidade').value = arquivo.quantidade || '';
    document.getElementById('inputSensor').value = arquivo.sensor || '';
    
    // Mostrar campo sensor se for peça PBS
    const sensorField = document.getElementById('sensorField');
    sensorField.style.display = arquivo.peca === 'PBS' ? 'block' : 'none';
    
    document.getElementById('modalArquivo').style.display = 'flex';
}

function fecharModal() {
    document.getElementById('modalArquivo').style.display = 'none';
    document.getElementById('formArquivo').reset();
    document.getElementById('sensorField').style.display = 'none';
}

// Adicionar listener para mostrar campo sensor quando peça for PBS
document.addEventListener('DOMContentLoaded', () => {
    const inputPeca = document.getElementById('inputPeca');
    const sensorField = document.getElementById('sensorField');
    
    if (inputPeca && sensorField) {
        inputPeca.addEventListener('input', function() {
            sensorField.style.display = this.value.toUpperCase() === 'PBS' ? 'block' : 'none';
        });
    }
});

// ===== FUNÇÕES DE CRUD =====
function salvarArquivo() {
    const id = document.getElementById('arquivoId').value;
    const dados = {
        projeto: document.getElementById('inputProjeto').value.trim(),
        peca: document.getElementById('inputPeca').value.trim(),
        nome_peca: document.getElementById('inputNomePeca').value.trim(),
        camada: document.getElementById('inputCamada').value.trim(),
        espessura: parseFloat(document.getElementById('inputEspessura').value) || null,
        quantidade: parseInt(document.getElementById('inputQuantidade').value) || null,
        sensor: document.getElementById('inputSensor').value.trim()
    };
    
    // Validar campos obrigatórios
    if (!dados.projeto || !dados.peca || !dados.nome_peca || !dados.camada) {
        showPopup('Projeto, Peça, Nome do Arquivo e Camada são obrigatórios', true);
        return;
    }
    
    const url = id ? `/api/arquivos/${id}` : '/api/arquivos';
    const method = id ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showPopup(result.message);
            fecharModal();
            carregarArquivos();
        } else {
            showPopup(result.message, true);
        }
    })
    .catch(error => {
        showPopup('Erro ao salvar arquivo. Tente novamente.', true);
    });
}

function excluirArquivo(id) {
    if (!confirm('Confirma a exclusão deste arquivo?')) return;
    
    fetch(`/api/arquivos/${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showPopup(result.message);
            carregarArquivos();
        } else {
            showPopup(result.message, true);
        }
    })
    .catch(error => {
        showPopup('Erro ao excluir arquivo. Tente novamente.', true);
    });
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