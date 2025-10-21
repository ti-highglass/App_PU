let dadosImportados = [];

// ===== FUNÇÕES DE POPUP =====
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

function showLoadingPopup(message) {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingPopup';
    loadingDiv.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; padding: 30px; border-radius: 8px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="margin-bottom: 15px;">
                    <i class="fas fa-spinner fa-spin" style="font-size: 48px; color: #3498db;"></i>
                </div>
                <p style="margin: 0; font-size: 16px; color: #333;">${message}</p>
            </div>
        </div>
    `;
    document.body.appendChild(loadingDiv);
}

function hideLoadingPopup() {
    const loadingPopup = document.getElementById('loadingPopup');
    if (loadingPopup) {
        loadingPopup.remove();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    
    // Upload por clique
    fileInput.addEventListener('change', handleFileSelect);
    
    // Upload por drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            processarArquivo(files[0]);
        }
    });
});

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processarArquivo(file);
    }
}

function processarArquivo(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        const lines = text.split('\n');
        dadosImportados = [];
        
        for (let i = 1; i < lines.length; i++) {
            let cols;
            if (lines[i].includes('\t')) {
                cols = lines[i].split('\t');
            } else if (lines[i].includes(';')) {
                cols = lines[i].split(';');
            } else {
                cols = lines[i].split(',');
            }
            
            if (cols.length >= 4 && cols[0].trim()) {
                const descricao = cols[3] || '';
                const partes = descricao.split('|');
                let peca = 'TSP', camada = 'L3';
                
                partes.forEach(p => {
                    const parte = p.trim();
                    if (['TSP','TSA','TSB','TSC','VGA','PBS','QTE','QTD'].includes(parte)) peca = parte;
                    if (['PDE','PDD','TMD','TME','PTD','PTE'].includes(parte)) peca = parte;
                    if (['FDD','FDE','FTE','FTD'].includes(parte)) peca = parte;
                    if (['L1','L3'].includes(parte)) camada = parte;
                });
                
                const camadas_pu = {
                    'TSP': {'L3': 1}, 'TSA': {'L3': 1}, 'TSB': {'L3': 1}, 'TSC': {'L3': 1},
                    'VGA': {'L3': 1}, 'PBS': {'L3': 1}, 'QTE': {'L3': 1}, 'QTD': {'L3': 1},
                    'PDE': {'L3': 3, 'L1': 2}, 'PDD': {'L3': 3, 'L1': 2},
                    'TMD': {'L3': 3, 'L1': 2}, 'TME': {'L3': 3, 'L1': 2},
                    'PTD': {'L3': 3, 'L1': 2}, 'PTE': {'L3': 3, 'L1': 2},
                    'FDD': {'L3': 3, 'L1': 3}, 'FDE': {'L3': 3, 'L1': 3},
                    'FTE': {'L3': 3, 'L1': 3}, 'FTD': {'L3': 3, 'L1': 3}
                };
                
                let quantidade = 1;
                if (camadas_pu[peca] && camadas_pu[peca][camada]) {
                    quantidade = camadas_pu[peca][camada];
                }
                
                dadosImportados.push({
                    id: cols[0].trim(),
                    veiculo: cols[1].trim(),
                    op: cols[2].trim(),
                    peca: peca,
                    descricao: descricao.trim(),
                    camada: camada,
                    quantidade_etiquetas: quantidade
                });
            }
        }
        
        exibirDados(dadosImportados);
        showPopup(`${dadosImportados.length} itens processados!`);
    };
    reader.readAsText(file);
}

function exibirDados(dados) {
    const tabela = document.getElementById('dadosTabela');
    const card = document.getElementById('dadosCard');
    
    if (dados.length === 0) {
        showPopup('Nenhum dado encontrado no arquivo', true);
        return;
    }
    
    const rows = dados.map(item => `
        <tr>
            <td>${item.id}</td>
            <td>${item.veiculo}</td>
            <td>${item.op}</td>
            <td>${item.peca}</td>
            <td>${item.descricao || '-'}</td>
            <td>${item.camada}</td>
            <td>${item.quantidade_etiquetas}</td>
        </tr>
    `).join('');
    
    tabela.innerHTML = rows;
    card.style.display = 'block';
}

function gerarEtiquetas() {
    if (dadosImportados.length === 0) {
        showPopup('Nenhum dado para gerar etiquetas', true);
        return;
    }
    
    showLoadingPopup('Gerando etiquetas PDF...');
    
    fetch('/api/gerar-etiquetas-pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ dados: dadosImportados })
    })
    .then(response => {
        hideLoadingPopup();
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Erro ao gerar PDF');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `etiquetas_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showPopup('Etiquetas geradas com sucesso!');
    })
    .catch(error => {
        hideLoadingPopup();
        console.error('Erro ao gerar etiquetas:', error);
        showPopup('Erro ao gerar etiquetas. Tente novamente.', true);
    });
}