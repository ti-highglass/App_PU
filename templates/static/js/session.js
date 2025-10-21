// Sistema de logout automático por inatividade
let inactivityTimer;
const INACTIVITY_TIME = 15 * 60 * 1000; // 15 minutos em millisegundos

function resetTimer() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
        alert('Sessão expirada por inatividade. Você será redirecionado para o login.');
        window.location.href = '/logout';
    }, INACTIVITY_TIME);
}

// Eventos que resetam o timer
const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

// Adicionar listeners para todos os eventos
events.forEach(event => {
    document.addEventListener(event, resetTimer, true);
});

// Iniciar o timer quando a página carregar
document.addEventListener('DOMContentLoaded', resetTimer);