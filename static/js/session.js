// Sistema de logout automático por inatividade
let inactivityTimer;
const INACTIVITY_TIME = 6000 * 60 * 1000; // 60 minutos em milissegundos

const triggerDashboardLogout = () => {
    const logoutUrl = window.ACOMP_CORTE_LOGOUT_URL;
    if (!logoutUrl) {
        return Promise.resolve();
    }

    return new Promise((resolve) => {
        try {
            const beacon = new Image();
            beacon.onload = () => resolve();
            beacon.onerror = () => resolve();
            const separator = logoutUrl.includes('?') ? '&' : '?';
            beacon.src = `${logoutUrl}${separator}_=${Date.now()}`;
            setTimeout(resolve, 1500);
        } catch (error) {
            resolve();
        }
    });
};

const executeLogout = async () => {
    try {
        await triggerDashboardLogout();
    } catch (error) {
        console.warn('Falha ao notificar logout do acompanhamento de corte:', error);
    } finally {
        window.location.href = '/logout';
    }
};

function resetTimer() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
        alert('Sessão expirada por inatividade. Você será redirecionado para o login.');
        executeLogout();
    }, INACTIVITY_TIME);
}

// Eventos que resetam o timer
const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

// Adicionar listeners para todos os eventos
events.forEach(event => {
    document.addEventListener(event, resetTimer, true);
});

// Iniciar o timer quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    resetTimer();
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', (event) => {
            event.preventDefault();
            executeLogout();
        });
    }
});
