// ===== DONNÉES CATALOGUE =====
const defaultCategories = [
    { code: 'portes', name: 'Portes intérieures' },
    { code: 'panneaux', name: 'Panneaux sandwich' },
    { code: 'peinture', name: 'Peinture' },
    { code: 'electricite', name: 'Électricité' },
    { code: 'quincaillerie', name: 'Quincaillerie' }
];

const defaultProducts = [
    { id: 1, category: 'portes', name: 'Porte battante XL - Finition Chêne', unit: 'pce', price: 450, coefficient: 1 },
    { id: 2, category: 'portes', name: 'Porte battante XL - Finition Blanc', unit: 'pce', price: 420, coefficient: 1 },
    { id: 3, category: 'portes', name: 'Porte coulissante - Finition Chêne', unit: 'pce', price: 680, coefficient: 1 },
    { id: 4, category: 'portes', name: 'Porte coulissante - Finition Blanc', unit: 'pce', price: 620, coefficient: 1 },
    { id: 5, category: 'panneaux', name: 'Panneau cloisonnage 4cm - Blanc', unit: 'm²', price: 85, coefficient: 1 },
    { id: 6, category: 'panneaux', name: 'Panneau cloisonnage 6cm - Blanc', unit: 'm²', price: 105, coefficient: 1 },
    { id: 7, category: 'panneaux', name: 'Panneau cloisonnage 4cm - Gris', unit: 'm²', price: 90, coefficient: 1 },
    { id: 8, category: 'peinture', name: 'Peinture murs - Gris clair (200L)', unit: 'fût', price: 180, coefficient: 1 },
    { id: 9, category: 'peinture', name: 'Peinture murs - Blanc pur (200L)', unit: 'fût', price: 165, coefficient: 1 },
    { id: 10, category: 'peinture', name: 'Peinture trim - Gris anthracite (5L)', unit: 'pot', price: 45, coefficient: 1 },
    { id: 11, category: 'electricite', name: 'Goulotte électrique 40x40', unit: 'm', price: 12, coefficient: 1 },
    { id: 12, category: 'electricite', name: 'Prise double - Blanc', unit: 'pce', price: 22, coefficient: 1 },
    { id: 13, category: 'electricite', name: 'Interrupteur simple - Blanc', unit: 'pce', price: 18, coefficient: 1 },
    { id: 14, category: 'quincaillerie', name: 'Poignée chrome XXL', unit: 'pce', price: 35, coefficient: 1 },
    { id: 15, category: 'quincaillerie', name: 'Charnière acier inox', unit: 'pce', price: 8, coefficient: 1 },
];

let selectedProducts = {};

// ===== UTILITAIRES =====
function formatPrice(price) {
    return price.toFixed(2).replace('.', ',') + '€';
}

function setActiveNav(sectionId) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').includes(sectionId)) {
            link.classList.add('active');
        }
    });
}

// ===== AUTHENTIFICATION =====
function getUsers() {
    const raw = localStorage.getItem('users');
    try {
        return raw ? JSON.parse(raw) : [];
    } catch (err) {
        return [];
    }
}

function saveUsers(users) {
    localStorage.setItem('users', JSON.stringify(users));
}

function findUser(email) {
    if (!email) return null;
    return getUsers().find(u => u.email.toLowerCase() === email.toLowerCase());
}

function ensureDemoUser() {
    if (findUser('demo@vienne.fr')) return;

    const users = getUsers();
    users.push({
        name: 'Demo',
        email: 'demo@vienne.fr',
        password: 'demo123'
    });
    saveUsers(users);
}

function saveClients(clients) {
    localStorage.setItem('clients', JSON.stringify(clients));
}

function generateId() {
    return 'c_' + Math.random().toString(16).slice(2) + Date.now();
}

function getProducts() {
    const raw = localStorage.getItem('products');
    try {
        return raw ? JSON.parse(raw) : [];
    } catch (err) {
        return [];
    }
}

function saveProducts(products) {
    localStorage.setItem('products', JSON.stringify(products));
}

function ensureDefaultProducts() {
    saveProducts(defaultProducts);
}

function getCatalogData() {
    return getProducts();
}

String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
};

// ===== TOGGLE SIDEBAR =====
function setOverlayVisibility(overlay, isVisible) {
    if (!overlay) return;
    overlay.classList.toggle('visible', isVisible);
}

function closeUserMenu() {
    const userMenu = document.getElementById('sidebarLogoutMenu');
    const userTrigger = document.getElementById('userMenuTrigger');
    if (!userMenu || !userTrigger) return;

    userMenu.hidden = true;
    userTrigger.setAttribute('aria-expanded', 'false');
}

function syncSidebarUserMenu() {
    const sidebar = document.querySelector('.sidebar');
    const logoutButton = document.getElementById('sidebarLogoutBtn');
    const userTrigger = document.getElementById('userMenuTrigger');

    if (!sidebar || !logoutButton || !userTrigger) return;

    const isCollapsedDesktop = window.innerWidth > 768 && sidebar.classList.contains('collapsed');
    const isMobileMenuMode = window.innerWidth <= 768;
    const useAvatarMenu = isCollapsedDesktop || isMobileMenuMode;

    logoutButton.style.display = useAvatarMenu ? 'none' : '';
    userTrigger.setAttribute('aria-expanded', 'false');

    if (!useAvatarMenu) {
        closeUserMenu();
    }
}

function initSidebarUserMenu() {
    const userTrigger = document.getElementById('userMenuTrigger');
    const userMenu = document.getElementById('sidebarLogoutMenu');

    if (!userTrigger || !userMenu || userTrigger.dataset.menuReady === 'true') return;

    userTrigger.dataset.menuReady = 'true';

    userTrigger.addEventListener('click', (event) => {
        const sidebar = document.querySelector('.sidebar');
        const isCollapsedDesktop = sidebar && window.innerWidth > 768 && sidebar.classList.contains('collapsed');
        const isMobileMenuMode = window.innerWidth <= 768;
        const canOpenMenu = isCollapsedDesktop || isMobileMenuMode;

        if (!canOpenMenu) return;

        event.preventDefault();
        event.stopPropagation();

        const isOpen = !userMenu.hidden;
        userMenu.hidden = isOpen;
        userTrigger.setAttribute('aria-expanded', String(!isOpen));
    });

    userTrigger.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        userTrigger.click();
    });

    document.addEventListener('click', (event) => {
        if (userMenu.hidden) return;
        if (userMenu.contains(event.target) || userTrigger.contains(event.target)) return;
        closeUserMenu();
    });
}

function initMobileSidebarScrollFallback() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar || sidebar.dataset.scrollFallbackReady === 'true') return;

    sidebar.dataset.scrollFallbackReady = 'true';

    sidebar.addEventListener('wheel', (event) => {
        if (window.innerWidth > 768 || !sidebar.classList.contains('mobile-visible')) return;
        sidebar.scrollTop += event.deltaY;
        event.preventDefault();
    }, { passive: false });

    let touchStartY = 0;

    sidebar.addEventListener('touchstart', (event) => {
        if (window.innerWidth > 768 || !sidebar.classList.contains('mobile-visible')) return;
        touchStartY = event.touches[0].clientY;
    }, { passive: true });

    sidebar.addEventListener('touchmove', (event) => {
        if (window.innerWidth > 768 || !sidebar.classList.contains('mobile-visible')) return;
        const touchY = event.touches[0].clientY;
        const deltaY = touchStartY - touchY;
        sidebar.scrollTop += deltaY;
        touchStartY = touchY;
        event.preventDefault();
    }, { passive: false });
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    if (!sidebar) return;

    if (window.innerWidth <= 768) {
        // Mode mobile
        sidebar.classList.toggle('mobile-visible');
        setOverlayVisibility(overlay, sidebar.classList.contains('mobile-visible'));
        // Enlever 'collapsed' si présent
        sidebar.classList.remove('collapsed');
    } else {
        // Mode desktop
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        setOverlayVisibility(overlay, false);
    }

    syncSidebarUserMenu();
}

function closeMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    if (!sidebar) return;

    sidebar.classList.remove('mobile-visible');
    setOverlayVisibility(overlay, false);
}

// Fermer la sidebar si on clique sur un lien (optionnel)
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function() {
        if (window.innerWidth <= 768) {
            closeMobileSidebar();
        }
    });
});

// Au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const savedState = localStorage.getItem('sidebarCollapsed');

    if (!sidebar) return;
    
    // Ne pas appliquer sur mobile
    if (window.innerWidth > 768 && savedState === 'true') {
        sidebar.classList.add('collapsed');
    }

    syncSidebarUserMenu();
});

// Gérer le redimensionnement
window.addEventListener('resize', function() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    if (!sidebar) return;
    
    if (window.innerWidth <= 768) {
        // Passage en mode mobile
        sidebar.classList.remove('collapsed');
        sidebar.classList.remove('mobile-visible');
        setOverlayVisibility(overlay, false);
    } else {
        // Passage en mode desktop
        sidebar.classList.remove('mobile-visible');
        setOverlayVisibility(overlay, false);
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        } else {
            sidebar.classList.remove('collapsed');
        }
    }

    syncSidebarUserMenu();
});

// ===== INITIALISATION =====
document.addEventListener('DOMContentLoaded', () => {
    ensureDemoUser();
    ensureDefaultProducts();
    initSidebarUserMenu();
    initMobileSidebarScrollFallback();

    // Récupérer les produits sélectionnés depuis le localStorage
    const saved = localStorage.getItem('selectedProducts');
    if (saved) {
        selectedProducts = JSON.parse(saved);
    }

    // Mettre à jour le nom d'utilisateur
    const userName = localStorage.getItem('userName');
    if (userName) {
        const userNameElements = document.querySelectorAll('.user-name');
        userNameElements.forEach(el => el.textContent = userName);
    }

    // Déterminer la page active pour le nav
    const currentPage = window.location.pathname;
    
    setActiveNav(currentPage);
    
    // Restaurer l'état de la sidebar
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    const sidebar = document.querySelector('.sidebar');
    if (sidebarCollapsed && sidebar) {
        sidebar.classList.add('collapsed');
    }

    syncSidebarUserMenu();
});
