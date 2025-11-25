document.addEventListener('DOMContentLoaded', () => {
    // Garantir que modais estejam fechados
    document.getElementById('modalCadastro').style.display = 'none';
    document.getElementById('modalEdicao').style.display = 'none';
    
    carregarUsuarios();
});

function carregarUsuarios() {
    const tbody = document.getElementById('usuarios-tbody');
    
    tbody.innerHTML = '<tr><td colspan="4" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Carregando...</td></tr>';
    
    fetch('/api/usuarios')
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(dados => {
            console.log('Dados recebidos:', dados);
            tbody.innerHTML = '';
            
            if (dados.error) {
                tbody.innerHTML = `<tr><td colspan="4" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro: ${dados.error}</td></tr>`;
                return;
            }
            
            if (dados.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="border border-gray-200 px-4 py-6 text-center text-gray-500">Nenhum usuário encontrado</td></tr>';
                return;
            }
            
            dados.forEach(user => {
                const row = tbody.insertRow();
                row.className = 'hover:bg-gray-50';
                
                [user.usuario, user.funcao, user.setor].forEach(value => {
                    const cell = row.insertCell();
                    cell.textContent = value || '-';
                    cell.className = 'border border-gray-200 px-4 py-3 text-sm text-gray-700';
                });
                
                const acaoCell = row.insertCell();
                acaoCell.className = 'border border-gray-200 px-4 py-3 text-center';
                acaoCell.innerHTML = `
                    <button onclick="resetarSenha(${user.id})" class="btn-action btn-yellow" title="Resetar Senha">
                        <i class="fas fa-key"></i>
                    </button>
                    <button onclick="abrirModalEdicao(${user.id}, '${user.usuario}', '${user.funcao}', '${user.setor}')" class="btn-action btn-blue" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="excluirUsuario(${user.id}, '${user.usuario}')" class="btn-action btn-red-action" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
            });
        })
        .catch(error => {
            console.error('Erro:', error);
            tbody.innerHTML = '<tr><td colspan="4" class="border border-gray-200 px-4 py-6 text-center text-red-500">Erro ao carregar usuários</td></tr>';
        });
}

const abrirModalCadastro = () => {
    document.getElementById('modalCadastro').style.display = 'flex';
};

const fecharModalCadastro = () => {
    document.getElementById('modalCadastro').style.display = 'none';
    document.getElementById('formCadastro').reset();
};

document.getElementById('modalCadastro').addEventListener('click', e => {
    if (e.target === e.currentTarget) fecharModalCadastro();
});

document.getElementById('formCadastro').addEventListener('submit', async e => {
    e.preventDefault();
    
    const dados = {
        username: document.getElementById('novoUsername').value,
        password: document.getElementById('novoPassword').value,
        role: document.getElementById('novoRole').value,
        setor: document.getElementById('novoSetor').value
    };
    
    try {
        const result = await fetch('/api/cadastrar-usuario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        }).then(res => res.json());
        
        showPopup(result.success ? result.message : result.message, !result.success);
        if (result.success) {
            fecharModalCadastro();
            carregarUsuarios();
        }
    } catch (error) {
        showPopup('Erro ao cadastrar usuário: ' + error.message, true);
    }
});

async function resetarSenha(userId) {
    const novaSenha = prompt('Digite a nova senha:');
    if (!novaSenha) return;
    
    try {
        const result = await fetch(`/api/resetar-senha/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ senha: novaSenha })
        }).then(res => res.json());
        
        showPopup(result.success ? result.message : result.message, !result.success);
    } catch (error) {
        showPopup('Erro ao resetar senha: ' + error.message, true);
    }
}

let usuarioEditandoId = null;

function abrirModalEdicao(userId, username, funcao, setor) {
    usuarioEditandoId = userId;
    document.getElementById('editUsername').value = username;
    document.getElementById('editRole').value = funcao;
    document.getElementById('editSetor').value = setor;
    document.getElementById('modalEdicao').style.display = 'flex';
}

const fecharModalEdicao = () => {
    document.getElementById('modalEdicao').style.display = 'none';
    document.getElementById('formEdicao').reset();
    usuarioEditandoId = null;
};

document.getElementById('modalEdicao').addEventListener('click', e => {
    if (e.target === e.currentTarget) fecharModalEdicao();
});

document.getElementById('formEdicao').addEventListener('submit', async e => {
    e.preventDefault();
    
    if (!usuarioEditandoId) return;
    
    const dados = {
        usuario: document.getElementById('editUsername').value,
        funcao: document.getElementById('editRole').value,
        setor: document.getElementById('editSetor').value
    };
    
    try {
        const result = await fetch(`/api/editar-usuario/${usuarioEditandoId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        }).then(res => res.json());
        
        showPopup(result.success ? result.message : result.message, !result.success);
        if (result.success) {
            fecharModalEdicao();
            carregarUsuarios();
        }
    } catch (error) {
        showPopup('Erro ao editar usuário: ' + error.message, true);
    }
});

async function excluirUsuario(userId, nomeUsuario) {
    if (!confirm(`Tem certeza que deseja excluir o usuário "${nomeUsuario}"?\n\nEsta ação não pode ser desfeita.`)) {
        return;
    }
    
    try {
        const result = await fetch(`/api/excluir-usuario/${userId}`, {
            method: 'DELETE'
        }).then(res => res.json());
        
        showPopup(result.success ? result.message : result.message, !result.success);
        if (result.success) carregarUsuarios();
    } catch (error) {
        showPopup('Erro ao excluir usuário: ' + error.message, true);
    }
}

let sortDirection = {};

const sortTable = (columnIndex) => {
    const table = document.getElementById('tabela-usuarios');
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
};

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