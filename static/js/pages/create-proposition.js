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

document.addEventListener('DOMContentLoaded', () => {
    const clientSelect = document.getElementById('clientSelect');
    if (clientSelect) {
        populateClientSelect('clientSelect', selectedId => {
            fillClientDetails(selectedId);
        });

        const urlParams = new URLSearchParams(window.location.search);
        const selectedId = urlParams.get('clientId');
        if (selectedId) {
            clientSelect.value = selectedId;
            fillClientDetails(selectedId);
        } else {
            const clients = getClients();
            if (clients.length === 1) {
                clientSelect.value = clients[0].id;
                fillClientDetails(clients[0].id);
            }
        }
    }

    renderSummary();
    renderProposalTable();
});

window.addEventListener('storage', () => {
    renderSummary();
    renderProposalTable();
});
