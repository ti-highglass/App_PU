let dadosOriginais = [];
let abaAtiva = 'premontagem';

document.addEventListener('DOMContentLoaded', function() {
    // Restaurar aba ativa do localStorage
    const abaArmazenada = localStorage.getItem('dashboardAbaAtiva');
    if (abaArmazenada && (abaArmazenada === 'premontagem' || abaArmazenada === 'criticas')) {
        abaAtiva = abaArmazenada;
        trocarAba(abaAtiva);
    }
    
    carregarDados();
    configurarPesquisa();
    
    // Auto-refresh a cada 5 minutos
    setInterval(carregarDados, 300000);
});

function trocarAba(aba) {
    // Remover classe active de todas as abas
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Ativar aba selecionada
    document.getElementById(`tab${aba.charAt(0).toUpperCase() + aba.slice(1)}`).classList.add('active');
    document.getElementById(`aba${aba.charAt(0).toUpperCase() + aba.slice(1)}`).classList.add('active');
    
    abaAtiva = aba;
    
    // Salvar aba ativa no localStorage
    localStorage.setItem('dashboardAbaAtiva', aba);
    
    // Reaplicar filtro se existir
    const campoPesquisa = document.getElementById('campoPesquisa');
    if (campoPesquisa && campoPesquisa.value.trim()) {
        filtrarPecas(campoPesquisa.value.trim());
    }
}

function configurarPesquisa() {
    const campoPesquisa = document.getElementById('campoPesquisa');
    const limparPesquisa = document.getElementById('limparPesquisa');
    
    campoPesquisa.addEventListener('input', function() {
        const termo = this.value.trim();
        if (termo) {
            limparPesquisa.style.display = 'block';
            filtrarPecas(termo);
        } else {
            limparPesquisa.style.display = 'none';
            mostrarTodasPecas();
        }
    });
    
    limparPesquisa.addEventListener('click', function() {
        campoPesquisa.value = '';
        this.style.display = 'none';
        mostrarTodasPecas();
    });
}

function filtrarPecas(termo) {
    const termoLower = termo.toLowerCase();
    const abaAtual = document.querySelector('.tab-content.active');
    const todasLinhas = abaAtual.querySelectorAll('.peca-linha');
    let contadores = { aviso: 0, forno: 0, critico: 0 };
    
    todasLinhas.forEach(linha => {
        const texto = linha.textContent.toLowerCase();
        const visivel = texto.includes(termoLower);
        
        if (visivel) {
            linha.classList.remove('hidden');
            // Contar por status
            if (linha.classList.contains('border-yellow-500')) contadores.aviso++;
            else if (linha.classList.contains('border-purple-500')) contadores.forno++;
            else if (linha.classList.contains('border-red-500')) contadores.critico++;
        } else {
            linha.classList.add('hidden');
        }
    });
    
    atualizarContadoresFiltrados(contadores);
}

function mostrarTodasPecas() {
    const abaAtual = document.querySelector('.tab-content.active');
    const todasLinhas = abaAtual.querySelectorAll('.peca-linha');
    todasLinhas.forEach(linha => linha.classList.remove('hidden'));
    atualizarContadores(dadosOriginais);
}

function atualizarContadoresFiltrados(contadores) {
    if (abaAtiva === 'premontagem') {
        const total = contadores.aviso;
        document.getElementById('totalPecas').innerHTML = `<i class="fas fa-box mr-2"></i>${total} peça${total !== 1 ? 's' : ''}`;
        document.getElementById('contadorAviso').textContent = contadores.aviso;
    } else if (abaAtiva === 'criticas') {
        const total = contadores.forno + contadores.critico;
        document.getElementById('totalPecas').innerHTML = `<i class="fas fa-box mr-2"></i>${total} peça${total !== 1 ? 's' : ''}`;
        document.getElementById('contadorForno').textContent = contadores.forno;
        document.getElementById('contadorCritico').textContent = contadores.critico;
    }
}

async function carregarDados() {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const refreshIcon = document.getElementById('refreshIcon');
    
    // Show loading only on first load
    if (!dadosOriginais.length) {
        loadingSpinner.style.display = 'block';
    }
    refreshIcon.classList.add('fa-spin');
    
    try {
        const response = await fetch('/api/dashboard-producao', {
            method: 'GET',
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const dados = await response.json();
        
        if (dados.error) {
            throw new Error(dados.error);
        }
        
        dadosOriginais = dados;
        renderizarDashboard(dados);
        atualizarContadores(dados);
        atualizarUltimaAtualizacao();
        
        // Reaplicar filtro se existir
        const campoPesquisa = document.getElementById('campoPesquisa');
        if (campoPesquisa?.value.trim()) {
            filtrarPecas(campoPesquisa.value.trim());
        }
        
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        mostrarErro('Erro ao carregar dados do dashboard');
    } finally {
        loadingSpinner.style.display = 'none';
        refreshIcon.classList.remove('fa-spin');
    }
}

function renderizarDashboard(dados) {
    const pecasAviso1 = document.getElementById('pecasAviso1');
    const pecasAviso2 = document.getElementById('pecasAviso2');
    const pecasAviso3 = document.getElementById('pecasAviso3');
    const pecasAviso4 = document.getElementById('pecasAviso4');
    const pecasForno1 = document.getElementById('pecasForno1');
    const pecasForno2 = document.getElementById('pecasForno2');
    const pecasForno3 = document.getElementById('pecasForno3');
    const pecasCritico = document.getElementById('pecasCritico');
    
    // Limpar colunas
    pecasAviso1.innerHTML = '';
    pecasAviso2.innerHTML = '';
    pecasAviso3.innerHTML = '';
    pecasAviso4.innerHTML = '';
    pecasForno1.innerHTML = '';
    pecasForno2.innerHTML = '';
    pecasForno3.innerHTML = '';
    pecasCritico.innerHTML = '';
    
    // Separar peças por status
    let aviso = dados.filter(item => item.status === 'aviso');
    let forno = dados.filter(item => item.status === 'forno');
    let critico = dados.filter(item => item.status === 'critico');
    
    // Ordenar por peça+OP e depois por tempo (mais antigo primeiro)
    aviso = ordenarPecas(aviso);
    forno = ordenarPecas(forno);
    critico = ordenarPecas(critico);
    
    // Dividir pré-montagem em quatro colunas
    const quartoAviso = Math.ceil(aviso.length / 4);
    const aviso1 = aviso.slice(0, quartoAviso);
    const aviso2 = aviso.slice(quartoAviso, quartoAviso * 2);
    const aviso3 = aviso.slice(quartoAviso * 2, quartoAviso * 3);
    const aviso4 = aviso.slice(quartoAviso * 3);
    
    // Dividir forno em três colunas
    const tercoForno = Math.ceil(forno.length / 3);
    const forno1 = forno.slice(0, tercoForno);
    const forno2 = forno.slice(tercoForno, tercoForno * 2);
    const forno3 = forno.slice(tercoForno * 2);
    
    // Renderizar cada categoria
    renderizarPecas(aviso1, pecasAviso1);
    renderizarPecas(aviso2, pecasAviso2);
    renderizarPecas(aviso3, pecasAviso3);
    renderizarPecas(aviso4, pecasAviso4);
    renderizarPecas(forno1, pecasForno1);
    renderizarPecas(forno2, pecasForno2);
    renderizarPecas(forno3, pecasForno3);
    renderizarPecas(critico, pecasCritico);
}

function ordenarPecas(pecas) {
    const prioridadeOrdem = { 'RNC': 0, 'ALTA': 1, 'NORMAL': 2, 'BAIXA': 3 };
    
    return pecas.sort((a, b) => {
        // Primeiro por prioridade
        const prioA = prioridadeOrdem[a.prioridade] ?? 2;
        const prioB = prioridadeOrdem[b.prioridade] ?? 2;
        
        if (prioA !== prioB) {
            return prioA - prioB;
        }
        
        // Depois por peça+OP
        const pecaOpA = `${a.peca}-${a.op}`;
        const pecaOpB = `${b.peca}-${b.op}`;
        
        return pecaOpA.localeCompare(pecaOpB);
    });
}

function renderizarPecas(pecas, container) {
    if (pecas.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-check-circle"></i><br>Nenhuma peça</div>';
        return;
    }
    
    // Use DocumentFragment for better performance
    const fragment = document.createDocumentFragment();
    
    pecas.forEach(peca => {
        const card = document.createElement('div');
        card.className = 'peca-linha';
        
        // Build class list efficiently
        const classes = ['peca-linha'];
        if (peca.status === 'critico') {
            classes.push('border-red-500');
        } else if (peca.status === 'aviso') {
            classes.push('border-yellow-500');
            if (peca.prioridade === 'ALTA') {
                classes.push('peca-prioridade-alta');
            }
        } else if (peca.status === 'forno') {
            classes.push('border-purple-500');
            if (peca.prioridade === 'ALTA') {
                classes.push('peca-prioridade-alta');
            }
        }
        card.className = classes.join(' ');
        
        // Build HTML more efficiently
        const quantidadeBadge = peca.quantidade > 1 ? `<span class="quantidade-badge">${peca.quantidade}x</span>` : '';
        
        if (peca.status === 'aviso' || peca.status === 'forno') {
            card.innerHTML = `<div class="peca-content"><div class="peca-info"><span class="peca-nome">${peca.peca} - ${peca.op}</span>${quantidadeBadge}</div><span class="peca-local"><i class="fas fa-map-marker-alt"></i> ${peca.local}</span></div>`;
        } else {
            card.innerHTML = `<div class="peca-content"><div class="peca-info"><span class="peca-nome">${peca.peca} - ${peca.op}</span>${quantidadeBadge}</div><div style="display: flex; align-items: center; gap: 1rem;"><span class="peca-local"><i class="fas fa-map-marker-alt"></i> ${peca.local}</span><span class="peca-etapa">${peca.etapa}</span></div></div>`;
        }
        
        card.addEventListener('click', () => mostrarDetalhes(peca));
        fragment.appendChild(card);
    });
    
    container.appendChild(fragment);
}

function atualizarContadores(dados) {
    const aviso = dados.filter(item => item.status === 'aviso').length;
    const forno = dados.filter(item => item.status === 'forno').length;
    const critico = dados.filter(item => item.status === 'critico').length;
    const total = aviso + forno + critico;
    
    // Atualizar contador geral
    document.getElementById('totalPecas').innerHTML = `<i class="fas fa-box mr-2"></i>${total} peça${total !== 1 ? 's' : ''}`;
    
    // Atualizar contadores das seções
    document.getElementById('contadorAviso').textContent = aviso;
    document.getElementById('contadorForno').textContent = forno;
    document.getElementById('contadorCritico').textContent = critico;
    
    // Atualizar contadores das abas
    document.getElementById('tabCounterPremontagem').textContent = aviso;
    document.getElementById('tabCounterCriticas').textContent = forno + critico;
}

function atualizarUltimaAtualizacao() {
    const agora = new Date();
    const horario = agora.toLocaleTimeString('pt-BR');
    document.getElementById('ultimaAtualizacao').innerHTML = `<i class="fas fa-clock mr-2"></i>Atualizado às ${horario}`;
}

function mostrarDetalhes(peca) {
    const detalhes = `
        OP: ${peca.op}
        Peça: ${peca.peca}
        Projeto: ${peca.projeto}
        Veículo: ${peca.veiculo}
        ${peca.quantidade > 1 ? `Quantidade: ${peca.quantidade} camadas` : ''}
        Local: ${peca.local}
        Etapa Atual: ${peca.etapa}
        Prioridade: ${peca.prioridade}
        ${peca.tempo ? `Tempo: ${peca.tempo}` : ''}
    `;
    
    alert(detalhes);
}

function mostrarErro(mensagem) {
    const statusBoard = document.getElementById('statusBoard');
    statusBoard.innerHTML = `
        <div class="col-span-full text-center py-20">
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg inline-block">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                ${mensagem}
            </div>
        </div>
    `;
}

// Função para gerar relatório
async function gerarRelatorio() {
    if (!dadosOriginais || dadosOriginais.length === 0) {
        alert('Nenhum dado disponível para gerar relatório');
        return;
    }
    
    try {
        const response = await fetch('/api/gerar-relatorio-dashboard', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dados: dadosOriginais })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao gerar relatório');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio_dashboard_${new Date().toISOString().slice(0, 10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        console.error('Erro ao gerar relatório:', error);
        alert('Erro ao gerar relatório');
    }
}

// Função para notificação sonora (opcional)
function tocarAlerta() {
    try {
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
        audio.play();
    } catch (e) {
        // Ignorar erro de áudio
    }
}