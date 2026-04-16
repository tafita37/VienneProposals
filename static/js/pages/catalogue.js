document.addEventListener('DOMContentLoaded', () => {
    const categoryFilter = document.getElementById('categoryFilter');
    const searchFilter = document.getElementById('searchFilter');
    const catalogueTable = document.getElementById('catalogueTable');
    const createProposalBtn = document.getElementById('createProposalBtn');

    if (!categoryFilter || !searchFilter || !catalogueTable || !createProposalBtn) {
        return;
    }

    let searchTimeout;
    const euroFormatter = new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });

    const parseNumber = (value) => {
        if (typeof value !== 'string') {
            return 0;
        }

        const normalized = value
            .replace(/€/g, '')
            .replace(/\s/g, '')
            .replace(',', '.');

        const parsed = parseFloat(normalized);
        return Number.isFinite(parsed) ? parsed : 0;
    };

    const getCsrfToken = () => {
        const cookies = document.cookie ? document.cookie.split(';') : [];
        for (const cookieEntry of cookies) {
            const cookie = cookieEntry.trim();
            if (cookie.startsWith('csrftoken=')) {
                return decodeURIComponent(cookie.substring('csrftoken='.length));
            }
        }
        return '';
    };

    const updateRowTotal = (row) => {
        const unitPriceCell = row.children[3];
        const coefficientInput = row.querySelector('.input-coefficient');
        const quantityInput = row.querySelector('.input-quantity');
        const totalCell = row.querySelector('.total-cell');

        if (!unitPriceCell || !coefficientInput || !quantityInput || !totalCell) {
            return;
        }

        const unitPrice = parseNumber(unitPriceCell.textContent || '0');
        const coefficient = Math.max(0, parseFloat(coefficientInput.value) || 0);
        const quantity = Math.max(0, parseFloat(quantityInput.value) || 0);
        const total = Math.max(0, unitPrice * coefficient * quantity);

        totalCell.textContent = `${euroFormatter.format(total)} €`;
    };

    const attachRowEvents = (row) => {
        const coefficientInput = row.querySelector('.input-coefficient');
        const quantityInput = row.querySelector('.input-quantity');

        if (!coefficientInput || !quantityInput) {
            return;
        }

        coefficientInput.addEventListener('input', () => updateRowTotal(row));
        quantityInput.addEventListener('input', () => updateRowTotal(row));

        updateRowTotal(row);
    };

    const fetchProducts = () => {
        const nom = searchFilter.value.trim();
        const category_id = categoryFilter.value.trim();

        const params = new URLSearchParams();
        if (nom) params.append('nom', nom);
        if (category_id) params.append('category_id', category_id);

        fetch(`/com/api/products/?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Réponse HTTP invalide: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const products = Array.isArray(data?.products) ? data.products : [];
                renderProducts(products);
            })
            .catch(error => console.error('Erreur lors du chargement des produits:', error));
    };

    const renderProducts = (products) => {
        if (!Array.isArray(products)) {
            return;
        }

        catalogueTable.innerHTML = '';

        products.forEach(product => {
            const categoryName = product.category_names || product.category_name || 'Non catégorisé';
            const row = document.createElement('tr');
            row.setAttribute('data-category-id', product.category_id);
            row.setAttribute('data-product-id', product.id);
            row.innerHTML = `
                <td>${product.designation}</td>
                <td>${categoryName}</td>
                <td>${product.unit_name}</td>
                <td>${euroFormatter.format(product.sale_unit_price)} €</td>
                <td><input type="number" class="input-coefficient" value="1" min="0.1" step="0.1"></td>
                <td><input type="number" class="input-quantity" value="${product.quantity || 0}" min="0"></td>
                <td class="total-cell">0 €</td>
            `;
            catalogueTable.appendChild(row);
            attachRowEvents(row);
        });
    };

    const getSelectedProductsPayload = () => {
        return Array.from(catalogueTable.querySelectorAll('tr'))
            .map((row) => {
                const coefficientInput = row.querySelector('.input-coefficient');
                const quantityInput = row.querySelector('.input-quantity');
                const coefficient = Math.max(0, parseFloat(coefficientInput?.value) || 0);
                const quantity = Math.max(0, parseFloat(quantityInput?.value) || 0);
                const productId = parseInt(row.getAttribute('data-product-id'), 10);

                if (!Number.isInteger(productId) || productId <= 0 || quantity <= 0) {
                    return null;
                }

                return {
                    product_id: productId,
                    coefficient,
                    quantity,
                };
            })
            .filter((item) => item !== null);
    };

    Array.from(catalogueTable.querySelectorAll('tr')).forEach(attachRowEvents);

    categoryFilter.addEventListener('change', fetchProducts);

    searchFilter.addEventListener('input', () => {
        window.clearTimeout(searchTimeout);
        searchTimeout = window.setTimeout(fetchProducts, 300);
    });

    createProposalBtn.addEventListener('click', (event) => {
        event.preventDefault();

        const selectedProducts = getSelectedProductsPayload();
        if (selectedProducts.length === 0) {
            window.alert('Sélectionnez au moins un produit avec une quantité supérieure à 0.');
            return;
        }

        fetch('/com/api/proposals/selected-products/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                selected_products: selectedProducts,
                product_ids: selectedProducts.map((item) => item.product_id),
            }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Réponse HTTP invalide: ${response.status}`);
                }
                return response.json();
            })
            .then(() => {
                window.location.href = createProposalBtn.getAttribute('href') || '/com/new_proposition_page/';
            })
            .catch((error) => {
                console.error('Erreur lors de l\'envoi des produits:', error);
                window.alert('Erreur lors de la création de la proposition.');
            });
    });
});
