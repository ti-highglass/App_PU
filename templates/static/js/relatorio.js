let dadosRelatorio = [];
let ordemAtual = { campo: 'total_enviado', crescente: false };

document.addEventListener('DOMContentLoaded', function() {
    carregarRelatorio();
});

async function carregarRelatorio() {
    const loading = document.getElementById('loading');
    const tabela = document.getElementById('tabelaRelatorio');
    const mensagemVazia = document.getElementById('mensagemVazia');
    
    loading.classList.remove('hidden');
    tabela.innerHTML = '';
    mensagemVazia.classList.add('hidden');
    
    try {
        const response = await fetch('/api/relatorio-controle');
        const dados = await response.json();
        
        if (response.ok) {
            dadosRelatorio = dados;
            renderizarTabela(dados);
            atualizarResumo(dados);
        } else {
            throw new Error(dados.error || 'Erro ao carregar dados');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarNotificacao('Erro ao carregar relatório: ' + error.message, 'error');
        mensagemVazia.classList.remove('hidden');
    } finally {
        loading.classList.add('hidden');
    }
}

function renderizarTabela(dados) {
    const tabela = document.getElementById('tabelaRelatorio');
    const mensagemVazia = document.getElementById('mensagemVazia');
    
    if (!dados || dados.length === 0) {
        mensagemVazia.classList.remove('hidden');
        return;
    }
    
    // Calcular total para percentuais
    const totalGeral = dados.reduce((sum, item) => sum + item.total_enviado, 0);
    const maiorValor = Math.max(...dados.map(item => item.total_enviado));
    
    tabela.innerHTML = dados.map(item => {
        return `
            <tr class="hover:bg-gray-50">
                <td class="border border-gray-200 px-6 py-4 text-base font-medium text-gray-800">
                    ${item.usuario}
                </td>
                <td class="border border-gray-200 px-6 py-4 text-base font-semibold text-blue-700">
                    ${item.hoje.toLocaleString()} peças
                </td>
                <td class="border border-gray-200 px-6 py-4 text-base font-semibold text-gray-900">
                    ${item.total_enviado.toLocaleString()} peças
                </td>
            </tr>
        `;
    }).join('');
}

function atualizarResumo(dados) {
    const totalUsuarios = dados.length;
    const totalPecas = dados.reduce((sum, item) => sum + item.total_enviado, 0);
    const mediaPorUsuario = totalUsuarios > 0 ? Math.round(totalPecas / totalUsuarios) : 0;
    
    document.getElementById('totalUsuarios').textContent = totalUsuarios;
    document.getElementById('totalPecas').textContent = totalPecas.toLocaleString();
    document.getElementById('mediaPorUsuario').textContent = mediaPorUsuario.toLocaleString();
}

function ordenarTabela(campo) {
    if (ordemAtual.campo === campo) {
        ordemAtual.crescente = !ordemAtual.crescente;
    } else {
        ordemAtual.campo = campo;
        ordemAtual.crescente = campo === 'usuario';
    }
    
    const dadosOrdenados = [...dadosRelatorio].sort((a, b) => {
        let valorA = a[campo];
        let valorB = b[campo];
        
        if (typeof valorA === 'string') {
            valorA = valorA.toLowerCase();
            valorB = valorB.toLowerCase();
        }
        
        if (ordemAtual.crescente) {
            return valorA > valorB ? 1 : -1;
        } else {
            return valorA < valorB ? 1 : -1;
        }
    });
    
    renderizarTabela(dadosOrdenados);
    atualizarIconesOrdenacao();
}

function atualizarIconesOrdenacao() {
    // Resetar todos os ícones
    document.querySelectorAll('th i').forEach(icon => {
        icon.className = 'fas fa-sort ml-1 text-gray-400';
    });
    
    // Atualizar ícone da coluna atual
    const th = document.querySelector(`th[onclick="ordenarTabela('${ordemAtual.campo}')"] i`);
    if (th) {
        th.className = `fas fa-sort-${ordemAtual.crescente ? 'up' : 'down'} ml-1 text-blue-600`;
    }
}

function mostrarNotificacao(mensagem, tipo = 'info') {
    // Criar elemento de notificação
    const notificacao = document.createElement('div');
    notificacao.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`;
    
    const cores = {
        'success': 'bg-green-500 text-white',
        'error': 'bg-red-500 text-white',
        'warning': 'bg-yellow-500 text-white',
        'info': 'bg-blue-500 text-white'
    };
    
    notificacao.className += ` ${cores[tipo] || cores.info}`;
    
    const icones = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    
    notificacao.innerHTML = `
        <div class="flex items-center">
            <i class="${icones[tipo] || icones.info} mr-2"></i>
            <span>${mensagem}</span>
        </div>
    `;
    
    document.body.appendChild(notificacao);
    
    // Animar entrada
    setTimeout(() => {
        notificacao.classList.remove('translate-x-full');
    }, 100);
    
    // Remover após 5 segundos
    setTimeout(() => {
        notificacao.classList.add('translate-x-full');
        setTimeout(() => {
            document.body.removeChild(notificacao);
        }, 300);
    }, 5000);
}