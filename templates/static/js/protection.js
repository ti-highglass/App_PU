// Proteções básicas contra inspeção de código
(function() {
    'use strict';
    
    // Desabilitar menu de contexto
    document.addEventListener('contextmenu', e => e.preventDefault());
    
    // Desabilitar teclas de desenvolvedor
    document.addEventListener('keydown', e => {
        // F12, Ctrl+Shift+I, Ctrl+U, Ctrl+S
        if (e.key === 'F12' || 
            (e.ctrlKey && e.shiftKey && e.key === 'I') ||
            (e.ctrlKey && (e.key === 'u' || e.key === 'U' || e.key === 's' || e.key === 'S'))) {
            e.preventDefault();
            return false;
        }
    });
    
    // Detectar DevTools
    let devtools = false;
    const threshold = 160;
    
    setInterval(() => {
        if (window.outerHeight - window.innerHeight > threshold || 
            window.outerWidth - window.innerWidth > threshold) {
            if (!devtools) {
                devtools = true;
                document.body.innerHTML = '<div style="text-align:center;margin-top:50px;font-size:24px;color:red;">Acesso não autorizado!</div>';
            }
        }
    }, 500);
})();