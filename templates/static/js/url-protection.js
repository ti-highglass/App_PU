// Proteção contra manipulação de URL
(function() {
    'use strict';
    
    // Detectar tentativas de navegação manual
    let isNavigatingProgrammatically = false;
    
    // Interceptar mudanças de URL
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function() {
        if (!isNavigatingProgrammatically) {
            // Verificar se a URL é permitida
            const newUrl = arguments[2];
            if (newUrl && !isUrlAllowed(newUrl)) {
                console.warn('Acesso negado à URL:', newUrl);
                return;
            }
        }
        return originalPushState.apply(history, arguments);
    };
    
    history.replaceState = function() {
        if (!isNavigatingProgrammatically) {
            const newUrl = arguments[2];
            if (newUrl && !isUrlAllowed(newUrl)) {
                console.warn('Acesso negado à URL:', newUrl);
                return;
            }
        }
        return originalReplaceState.apply(history, arguments);
    };
    
    // Verificar se URL é permitida baseada no setor do usuário
    function isUrlAllowed(url) {
        // URLs sempre permitidas
        const alwaysAllowed = ['/logout', '/login', '/'];
        if (alwaysAllowed.some(path => url.includes(path))) {
            return true;
        }
        
        // Obter setor do usuário (se disponível no DOM)
        const userSector = document.body.dataset.userSector;
        
        if (!userSector) return true; // Se não conseguir detectar, permitir
        
        // Regras por setor
        const sectorRules = {
            'Produção': ['/otimizadas', '/estoque', '/locais'],
            'Administrativo': ['/index', '/otimizadas', '/estoque', '/locais', '/arquivos', '/etiquetas'],
            'T.I': ['/index', '/otimizadas', '/estoque', '/locais', '/arquivos', '/etiquetas', '/register', '/saidas']
        };
        
        const allowedPaths = sectorRules[userSector] || [];
        return allowedPaths.some(path => url.includes(path));
    }
    
    // Interceptar tentativas de acesso direto via barra de endereços
    window.addEventListener('beforeunload', function() {
        isNavigatingProgrammatically = true;
    });
    
    // Verificar URL atual ao carregar a página
    document.addEventListener('DOMContentLoaded', function() {
        const currentPath = window.location.pathname;
        if (!isUrlAllowed(currentPath)) {
            console.warn('Acesso negado à página atual');
            window.location.href = '/otimizadas';
        }
    });
    
})();