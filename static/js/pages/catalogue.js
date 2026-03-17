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

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('catalogueTable')) {
        renderCatalogue();
    }
});
