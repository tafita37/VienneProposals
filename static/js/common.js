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
        if (link.getAttribute('href').includes(sectionId + '.html')) {
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

function getClients() {
    const raw = localStorage.getItem('clients');
    try {
        return raw ? JSON.parse(raw) : [];
    } catch (err) {
        return [];
    }
}

function saveClients(clients) {
    localStorage.setItem('clients', JSON.stringify(clients));
}

function generateId() {
    return 'c_' + Math.random().toString(16).slice(2) + Date.now();
}

function findClient(id) {
    if (!id) return null;
    return getClients().find(c => c.id === id);
}

function ensureDemoClient() {
    if (getClients().length > 0) return;

    const clients = [
        {
            id: generateId(),
            name: 'Magasin Concept Store',
            address: '12 Rue de la Paix, 75000 Paris',
            phone: '01 23 45 67 89',
            email: 'contact@conceptstore.fr'
        }
    ];
    saveClients(clients);
}
function getCategories() {
    const raw = localStorage.getItem('categories');
    try {
        return raw ? JSON.parse(raw) : [];
    } catch (err) {
        return [];
    }
}

function saveCategories(categories) {
    localStorage.setItem('categories', JSON.stringify(categories));
}

function ensureDefaultCategories() {
    if (getCategories().length > 0) return;

    saveCategories(defaultCategories);
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
    if (getProducts().length > 0) return;

    saveProducts(defaultProducts);
}

function getCategoryLabel(categoryCode) {
    const categories = getCategories();
    const category = categories.find(c => c.code === categoryCode);
    return category ? category.name : categoryCode;
}

function getCatalogData() {
    return getProducts();
}
function populateClientSelect(selectId, onChange) {
    const select = document.getElementById(selectId);
    if (!select) return;

    const clients = getClients();
    select.innerHTML = '<option value="">Sélectionner un client</option>' +
        clients.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

    if (typeof onChange === 'function') {
        select.addEventListener('change', () => onChange(select.value));
    }
}

function fillClientDetails(clientId) {
    const client = findClient(clientId);
    const address = document.getElementById('clientAddress');
    const phone = document.getElementById('clientPhone');
    const email = document.getElementById('clientEmail');

    if (!address || !phone || !email) return;

    if (!client) {
        address.value = '';
        phone.value = '';
        email.value = '';
        return;
    }

    address.value = client.address || '';
    phone.value = client.phone || '';
    email.value = client.email || '';
}

function handleSaveClient() {
    const messageEl = document.getElementById('clientMessage');
    if (messageEl) {
        messageEl.textContent = '';
        messageEl.className = 'form-message';
    }

    const name = document.getElementById('clientName')?.value.trim();
    const address = document.getElementById('clientAddress')?.value.trim();
    const phone = document.getElementById('clientPhone')?.value.trim();
    const email = document.getElementById('clientEmail')?.value.trim();

    if (!name || !address || !phone || !email) {
        if (messageEl) {
            messageEl.textContent = 'Veuillez remplir tous les champs.';
            messageEl.classList.add('error');
        }
        return;
    }

    const clients = getClients();
    clients.push({ id: generateId(), name, address, phone, email });
    saveClients(clients);

    window.location.href = 'clients.html';
}

function handleDeleteClient(clientId) {
    const clients = getClients().filter(c => c.id !== clientId);
    saveClients(clients);

    const messageEl = document.getElementById('clientsMessage');
    if (messageEl) {
        messageEl.textContent = 'Client supprimé.';
        messageEl.classList.add('success');
    }

    renderClientsTable();
}

function renderClientsTable() {
    const tbody = document.querySelector('#clientsTable tbody');
    if (!tbody) return;

    const clients = getClients();
    if (clients.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:2rem; color: var(--text-light);">Aucun client disponible. Ajoutez-en un.</td></tr>`;
        return;
    }

    tbody.innerHTML = clients.map(client => `
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${client.name}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${client.email}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${client.phone}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${client.address}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                <button class="btn btn-secondary" style="margin-right: 0.5rem;" onclick="location.href='create-client.html?edit=${client.id}'">✏️</button>
                <button class="btn btn-secondary" style="background: var(--warning);" onclick="handleDeleteClient('${client.id}')">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function handleEditClient(editId) {
    if (!editId) return false;

    const client = findClient(editId);
    if (!client) return false;

    const nameEl = document.getElementById('clientName');
    const addressEl = document.getElementById('clientAddress');
    const phoneEl = document.getElementById('clientPhone');
    const emailEl = document.getElementById('clientEmail');

    if (nameEl) nameEl.value = client.name || '';
    if (addressEl) addressEl.value = client.address || '';
    if (phoneEl) phoneEl.value = client.phone || '';
    if (emailEl) emailEl.value = client.email || '';

    const saveButton = document.getElementById('saveClient');
    if (saveButton) {
        saveButton.textContent = 'Mettre à jour';
        saveButton.onclick = (e) => {
            e.preventDefault();
            updateClient(editId);
        };
    }

    return true;
}

function updateClient(clientId) {
    const messageEl = document.getElementById('clientMessage');
    if (messageEl) {
        messageEl.textContent = '';
        messageEl.className = 'form-message';
    }

    const name = document.getElementById('clientName')?.value.trim();
    const address = document.getElementById('clientAddress')?.value.trim();
    const phone = document.getElementById('clientPhone')?.value.trim();
    const email = document.getElementById('clientEmail')?.value.trim();

    if (!name || !address || !phone || !email) {
        if (messageEl) {
            messageEl.textContent = 'Veuillez remplir tous les champs.';
            messageEl.classList.add('error');
        }
        return;
    }

    const clients = getClients();
    const idx = clients.findIndex(c => c.id === clientId);
    if (idx === -1) return;

    clients[idx] = { id: clientId, name, address, phone, email };
    saveClients(clients);
    window.location.href = 'clients.html';
}

// ===== GESTION CATÉGORIES =====
function handleSaveCategory() {
    const messageEl = document.getElementById('modalMessage');
    if (messageEl) {
        messageEl.textContent = '';
        messageEl.className = 'form-message';
    }

    const code = document.getElementById('categoryCode')?.value.trim();
    const name = document.getElementById('categoryName')?.value.trim();

    if (!code || !name) {
        if (messageEl) {
            messageEl.textContent = 'Veuillez remplir tous les champs.';
            messageEl.classList.add('error');
        }
        return;
    }

    const categories = getCategories();
    const existing = categories.find(c => c.code === code);

    if (existing && !document.getElementById('categoryModal').dataset.editId) {
        if (messageEl) {
            messageEl.textContent = 'Une catégorie avec ce code existe déjà.';
            messageEl.classList.add('error');
        }
        return;
    }

    if (document.getElementById('categoryModal').dataset.editId) {
        // Mise à jour
        const editId = document.getElementById('categoryModal').dataset.editId;
        const idx = categories.findIndex(c => c.code === editId);
        if (idx !== -1) {
            categories[idx] = { code, name };
            saveCategories(categories);
            closeCategoryModal();
            renderCategoriesTable();
        }
    } else {
        // Création
        categories.push({ code, name });
        saveCategories(categories);
        closeCategoryModal();
        renderCategoriesTable();
    }
}

function handleEditCategory(code) {
    const categories = getCategories();
    const category = categories.find(c => c.code === code);
    if (!category) return;

    document.getElementById('categoryCode').value = category.code;
    document.getElementById('categoryName').value = category.name;
    document.getElementById('modalTitle').textContent = 'Modifier la catégorie';
    document.getElementById('categoryModal').dataset.editId = code;
    document.getElementById('categoryModal').style.display = 'block';
}

function handleDeleteCategory(code) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette catégorie ?')) return;

    const categories = getCategories().filter(c => c.code !== code);
    saveCategories(categories);

    const messageEl = document.getElementById('categoriesMessage');
    if (messageEl) {
        messageEl.textContent = 'Catégorie supprimée.';
        messageEl.classList.add('success');
    }

    renderCategoriesTable();
}

function renderCategoriesTable() {
    const tbody = document.querySelector('#categoriesTable tbody');
    if (!tbody) return;

    const categories = getCategories();
    if (categories.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; padding:2rem; color: var(--text-light);">Aucune catégorie disponible. Ajoutez-en une.</td></tr>`;
        return;
    }

    tbody.innerHTML = categories.map(category => `
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${category.code}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${category.name}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                <button class="btn btn-secondary" style="margin-right: 0.5rem;" onclick="handleEditCategory('${category.code}')">✏️</button>
                <button class="btn btn-secondary" style="background: var(--warning);" onclick="handleDeleteCategory('${category.code}')">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function closeCategoryModal() {
    document.getElementById('categoryModal').style.display = 'none';
    document.getElementById('categoryModal').dataset.editId = '';
    document.getElementById('categoryCode').value = '';
    document.getElementById('categoryName').value = '';
    document.getElementById('modalTitle').textContent = 'Ajouter une catégorie';
    document.getElementById('modalMessage').textContent = '';
    document.getElementById('modalMessage').className = 'form-message';
}

// ===== GESTION PRODUITS =====
function handleSaveProduct() {
    const messageEl = document.getElementById('productModalMessage');
    if (messageEl) {
        messageEl.textContent = '';
        messageEl.className = 'form-message';
    }

    const name = document.getElementById('productName')?.value.trim();
    const category = document.getElementById('productCategory')?.value;
    const unit = document.getElementById('productUnit')?.value;
    const price = parseFloat(document.getElementById('productPrice')?.value);

    if (!name || !category || !unit || isNaN(price) || price < 0) {
        if (messageEl) {
            messageEl.textContent = 'Veuillez remplir tous les champs correctement.';
            messageEl.classList.add('error');
        }
        return;
    }

    const products = getProducts();

    if (document.getElementById('productModal').dataset.editId) {
        // Mise à jour
        const editId = parseInt(document.getElementById('productModal').dataset.editId);
        const idx = products.findIndex(p => p.id === editId);
        if (idx !== -1) {
            products[idx] = { ...products[idx], name, category, unit, price };
            saveProducts(products);
            closeProductModal();
            renderProductsTable();
        }
    } else {
        // Création
        const newId = Math.max(...products.map(p => p.id), 0) + 1;
        products.push({ id: newId, name, category, unit, price, coefficient: 1 });
        saveProducts(products);
        closeProductModal();
        renderProductsTable();
    }
}

function handleEditProduct(id) {
    const products = getProducts();
    const product = products.find(p => p.id === id);
    if (!product) return;

    document.getElementById('productName').value = product.name;
    document.getElementById('productCategory').value = product.category;
    document.getElementById('productUnit').value = product.unit;
    document.getElementById('productPrice').value = product.price;
    document.getElementById('productModalTitle').textContent = 'Modifier le produit';
    document.getElementById('productModal').dataset.editId = id;
    document.getElementById('productModal').style.display = 'block';
}

function handleDeleteProduct(id) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce produit ?')) return;

    const products = getProducts().filter(p => p.id !== id);
    saveProducts(products);

    const messageEl = document.getElementById('productsMessage');
    if (messageEl) {
        messageEl.textContent = 'Produit supprimé.';
        messageEl.classList.add('success');
    }

    renderProductsTable();
}

function renderProductsTable() {
    const tbody = document.querySelector('#productsTable tbody');
    if (!tbody) return;

    const products = getProducts();
    if (products.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:2rem; color: var(--text-light);">Aucun produit disponible. Ajoutez-en un.</td></tr>`;
        return;
    }

    tbody.innerHTML = products.map(product => `
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${product.name}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${getCategoryLabel(product.category)}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${product.unit}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${formatPrice(product.price)}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                <button class="btn btn-secondary" style="margin-right: 0.5rem;" onclick="handleEditProduct(${product.id})">✏️</button>
                <button class="btn btn-secondary" style="background: var(--warning);" onclick="handleDeleteProduct(${product.id})">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function populateCategorySelect(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    const categories = getCategories();
    select.innerHTML = '<option value="">Sélectionner une catégorie</option>' +
        categories.map(c => `<option value="${c.code}">${c.name}</option>`).join('');
}

function closeProductModal() {
    document.getElementById('productModal').style.display = 'none';
    document.getElementById('productModal').dataset.editId = '';
    document.getElementById('productName').value = '';
    document.getElementById('productCategory').value = '';
    document.getElementById('productUnit').value = '';
    document.getElementById('productPrice').value = '';
    document.getElementById('productModalTitle').textContent = 'Ajouter un produit';
    document.getElementById('productModalMessage').textContent = '';
    document.getElementById('productModalMessage').className = 'form-message';
}

function handleLogin(e) {
    e.preventDefault();
    const messageEl = document.getElementById('loginMessage');
    if (messageEl) {
        messageEl.textContent = '';
        messageEl.className = 'form-message';
    }

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const user = findUser(username);

    if (!user || user.password !== password) {
        if (messageEl) {
            messageEl.textContent = 'Identifiant ou mot de passe incorrect.';
            messageEl.classList.add('error');
        }
        return;
    }

    localStorage.setItem('userLogged', 'true');
    localStorage.setItem('userName', (user.name || user.email.split('@')[0]).capitalize());
    window.location.href = 'dashboard.html';
}

function handleRegister(e) {
    e.preventDefault();
    const messageEl = document.getElementById('registerMessage');
    if (messageEl) {
        messageEl.textContent = '';
        messageEl.className = 'form-message';
    }

    const name = document.getElementById('registerName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const confirm = document.getElementById('registerConfirm').value;

    if (!name || !email || !password || !confirm) {
        if (messageEl) {
            messageEl.textContent = 'Veuillez remplir tous les champs.';
            messageEl.classList.add('error');
        }
        return;
    }

    if (password !== confirm) {
        if (messageEl) {
            messageEl.textContent = 'Les mots de passe ne correspondent pas.';
            messageEl.classList.add('error');
        }
        return;
    }

    if (findUser(email)) {
        if (messageEl) {
            messageEl.textContent = 'Un compte existe déjà pour cet e-mail.';
            messageEl.classList.add('error');
        }
        return;
    }

    const users = getUsers();
    users.push({ name, email: email.toLowerCase(), password });
    saveUsers(users);

    localStorage.setItem('userLogged', 'true');
    localStorage.setItem('userName', name.capitalize());
    window.location.href = 'dashboard.html';
}

function handleLogout() {
    if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
        localStorage.removeItem('userLogged');
        localStorage.removeItem('userName');
        window.location.href = 'login.html';
    }
}

function checkAuth() {
    const isLogged = localStorage.getItem('userLogged');
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    const openPages = ['login.html', 'register.html'];

    if (!isLogged && !openPages.includes(currentPage)) {
        window.location.href = 'login.html';
        return;
    }

    if (isLogged && openPages.includes(currentPage)) {
        window.location.href = 'dashboard.html';
    }
}

// ===== GESTION SÉLECTION PRODUITS =====

function updateProductSelection(productId) {
    const quantityInput = document.querySelector(`[data-product-id="${productId}"].input-quantity`);
    if (!quantityInput) return;

    const qty = parseInt(quantityInput.value) || 0;

    if (qty > 0) {
        selectedProducts[productId] = qty;
    } else {
        delete selectedProducts[productId];
    }

    updatePrice();
    localStorage.setItem('selectedProducts', JSON.stringify(selectedProducts));
}

function updateProductCoefficient(productId) {
    updatePrice();
    localStorage.setItem('selectedProducts', JSON.stringify(selectedProducts));
}

function updatePrice() {
    const rows = document.querySelectorAll('[data-product-id]');
    rows.forEach(row => {
        const productId = row.dataset.productId;
        const product = getCatalogData().find(p => p.id == productId);
        if (!product) return;

        const quantityInput = row.querySelector('.input-quantity');
        const coefficientInput = row.querySelector('.input-coefficient');
        const priceCell = row.querySelector('.price-calculated');

        if (quantityInput && coefficientInput && priceCell) {
            const qty = parseInt(quantityInput.value) || 0;
            const coefficient = parseFloat(coefficientInput.value) || 1;
            const total = product.price * coefficient * qty;
            priceCell.textContent = formatPrice(total);
        }
    });
}

function filterCatalogue() {
    const categoryFilter = document.getElementById('categoryFilter')?.value || '';
    const searchFilter = document.getElementById('searchFilter')?.value.toLowerCase() || '';

    document.querySelectorAll('[data-product-id]').forEach(row => {
        const productId = row.dataset.productId;
        const product = getCatalogData().find(p => p.id == productId);

        const matchCategory = !categoryFilter || product.category === categoryFilter;
        const matchSearch = !searchFilter || product.name.toLowerCase().includes(searchFilter);

        row.style.display = matchCategory && matchSearch ? '' : 'none';
    });
}

function renderCatalogue() {
    const tbody = document.getElementById('catalogueTable');
    if (!tbody) return;

    tbody.innerHTML = getCatalogData().map(product => `
        <tr data-product-id="${product.id}">
            <td>${product.name}</td>
            <td>
                <span style="background: rgba(13, 115, 119, 0.1); padding: 0.3rem 0.6rem; border-radius: 4px; font-size: 0.85rem;">
                    ${getCategoryLabel(product.category)}
                </span>
            </td>
            <td>${product.unit}</td>
            <td>${formatPrice(product.price)}</td>
            <td>
                <input type="number" class="input-coefficient" value="${product.coefficient}" min="0.1" step="0.1" data-product-id="${product.id}" onchange="updatePrice()">
            </td>
            <td>
                <input type="number" class="input-quantity" value="0" min="0" data-product-id="${product.id}" onchange="updateProductSelection(${product.id})">
            </td>
            <td>
                <span class="price-calculated" data-product-id="${product.id}">0€</span>
            </td>
        </tr>
    `).join('');

    updatePrice();
}

function calculateTotal() {
    let total = 0;
    let totalByCategory = {};

    Object.entries(selectedProducts).forEach(([productId, qty]) => {
        const product = getCatalogData().find(p => p.id == productId);
        if (!product) return;

        const coefficientInput = document.querySelector(`[data-product-id="${productId}"].input-coefficient`);
        const coefficient = coefficientInput ? parseFloat(coefficientInput.value) || 1 : 1;
        const price = product.price * coefficient * qty;

        total += price;

        if (!totalByCategory[product.category]) {
            totalByCategory[product.category] = [];
        }
        totalByCategory[product.category].push({
            name: product.name,
            qty: qty,
            unitPrice: product.price * coefficient,
            total: price
        });
    });

    return { total, totalByCategory };
}

function renderSummary() {
    const summaryContainer = document.getElementById('summaryContainer');
    if (!summaryContainer) return;

    const { total, totalByCategory } = calculateTotal();

    if (Object.keys(selectedProducts).length === 0) {
        summaryContainer.innerHTML = '<h2 style="margin-bottom: 1.5rem; color: var(--text-dark);">Récapitulatif par Catégorie</h2><p style="color: var(--text-light); text-align: center; padding: 2rem;">Sélectionnez des produits du catalogue pour les ajouter à la proposition...</p>';
    } else {
        let summaryHTML = '<h2 style="margin-bottom: 1.5rem; color: var(--text-dark);">Récapitulatif par Catégorie</h2>';
        Object.entries(totalByCategory).forEach(([category, items]) => {
            const categoryTotal = items.reduce((sum, item) => sum + item.total, 0);
            summaryHTML += `
                <div class="summary-section">
                    <div class="summary-category-title">
                        <span>${getCategoryLabel(category)}</span>
                        <span>${formatPrice(categoryTotal)}</span>
                    </div>
                    ${items.map(item => `
                        <div class="summary-item">
                            <div class="summary-item-name">${item.name}</div>
                            <div class="summary-item-qty">${item.qty}</div>
                            <div class="summary-item-total">${formatPrice(item.total)}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        });
        summaryContainer.innerHTML = summaryHTML;
    }

    const totalElement = document.getElementById('totalAmount');
    if (totalElement) {
        totalElement.textContent = formatPrice(total);
    }
}

function renderProposalTable() {
    const tbody = document.getElementById('proposalSummaryTable');
    if (!tbody) return;

    if (Object.keys(selectedProducts).length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-light);">Aucun produit sélectionné</td></tr>';
        return;
    }

    let html = '';
    let lastCategory = '';

    Object.entries(selectedProducts).forEach(([productId, qty]) => {
        const product = getCatalogData().find(p => p.id == productId);
        if (!product) return;

        const coefficientInput = document.querySelector(`[data-product-id="${productId}"].input-coefficient`);
        const coefficient = coefficientInput ? parseFloat(coefficientInput.value) || 1 : 1;
        const unitPrice = product.price * coefficient;
        const total = unitPrice * qty;

        if (product.category !== lastCategory) {
            html += `<tr style="background: #f9f7f4; font-weight: 600;"><td>${getCategoryLabel(product.category)}</td><td colspan="5"></td></tr>`;
            lastCategory = product.category;
        }

        html += `
            <tr>
                <td></td>
                <td>${product.name}</td>
                <td>${qty}</td>
                <td>${formatPrice(unitPrice)}</td>
                <td>${coefficient.toFixed(2)}</td>
                <td class="price-calculated">${formatPrice(total)}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
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
    ensureDemoClient();
    ensureDefaultCategories();
    ensureDefaultProducts();
    checkAuth();
    initSidebarUserMenu();
    initMobileSidebarScrollFallback();

    // Récupérer les produits sélectionnés depuis le localStorage
    const saved = localStorage.getItem('selectedProducts');
    if (saved) {
        selectedProducts = JSON.parse(saved);
    }

    // Si on est sur la page de création de proposition, charger la liste des clients
    const clientSelect = document.getElementById('clientSelect');
    if (clientSelect) {
        populateClientSelect('clientSelect', selectedId => {
            fillClientDetails(selectedId);
        });

        // Pré-remplir si un client est déjà sélectionné (dans l'URL)
        const urlParams = new URLSearchParams(window.location.search);
        const selectedId = urlParams.get('clientId');
        if (selectedId) {
            clientSelect.value = selectedId;
            fillClientDetails(selectedId);
        } else {
            // Si un seul client existe, le sélectionner automatiquement
            const clients = getClients();
            if (clients.length === 1) {
                clientSelect.value = clients[0].id;
                fillClientDetails(clients[0].id);
            }
        }
    }

    // Rendu de la liste des clients
    if (document.getElementById('clientsTable')) {
        renderClientsTable();
    }

    // Page création client
    const saveButton = document.getElementById('saveClient');
    if (saveButton) {
        const params = new URLSearchParams(window.location.search);
        const editId = params.get('edit');

        const isEdit = handleEditClient(editId);
        if (!isEdit) {
            saveButton.addEventListener('click', handleSaveClient);
        }
    }

    // Page catégories
    if (document.getElementById('categoriesTable')) {
        renderCategoriesTable();
    }

    const addCategoryBtn = document.getElementById('addCategoryBtn');
    if (addCategoryBtn) {
        addCategoryBtn.addEventListener('click', () => {
            document.getElementById('categoryModal').style.display = 'block';
        });
    }

    const saveCategoryBtn = document.getElementById('saveCategoryBtn');
    if (saveCategoryBtn) {
        saveCategoryBtn.addEventListener('click', handleSaveCategory);
    }

    // Page produits
    if (document.getElementById('productsTable')) {
        renderProductsTable();
    }

    const addProductBtn = document.getElementById('addProductBtn');
    if (addProductBtn) {
        addProductBtn.addEventListener('click', () => {
            populateCategorySelect('productCategory');
            document.getElementById('productModal').style.display = 'block';
        });
    }

    const saveProductBtn = document.getElementById('saveProductBtn');
    if (saveProductBtn) {
        saveProductBtn.addEventListener('click', handleSaveProduct);
    }

    // Pré-charger les produits si on est sur la page catalogue
    if (document.getElementById('catalogueTable')) {
        renderCatalogue();
    }

    // Mettre à jour le nom d'utilisateur
    const userName = localStorage.getItem('userName');
    if (userName) {
        const userNameElements = document.querySelectorAll('.user-name');
        userNameElements.forEach(el => el.textContent = userName);
    }

    // Déterminer la page active pour le nav
    const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
    setActiveNav(currentPage.replace('.html', ''));
    
    // Restaurer l'état de la sidebar
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    const sidebar = document.querySelector('.sidebar');
    if (sidebarCollapsed && sidebar) {
        sidebar.classList.add('collapsed');
    }

    syncSidebarUserMenu();
});
