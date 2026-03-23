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

function clearClientReadonlyFields() {
    const addressInput = document.getElementById('clientAddress');
    const phoneInput = document.getElementById('clientPhone');
    const emailInput = document.getElementById('clientEmail');

    if (addressInput) addressInput.value = '';
    if (phoneInput) phoneInput.value = '';
    if (emailInput) emailInput.value = '';
}

async function loadClientDetails(clientId) {
    const addressInput = document.getElementById('clientAddress');
    const phoneInput = document.getElementById('clientPhone');
    const emailInput = document.getElementById('clientEmail');

    if (!addressInput || !phoneInput || !emailInput) {
        return;
    }

    if (!clientId) {
        clearClientReadonlyFields();
        return;
    }

    try {
        const response = await fetch(`/com/api/clients/${clientId}/`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error('Erreur lors de la récupération du client');
        }

        const data = await response.json();
        const client = data?.client;

        if (!client) {
            clearClientReadonlyFields();
            return;
        }

        addressInput.value = client.address || '';
        phoneInput.value = client.phone || '';
        emailInput.value = client.email || '';
    } catch (error) {
        console.error(error);
        clearClientReadonlyFields();
    }
}

async function loadProductsByCategory(categoryId) {
    const productSelect = document.getElementById('productSelect');
    
    if (!productSelect) {
        return;
    }

    if (!categoryId) {
        productSelect.innerHTML = '<option value="">Sélectionner</option>';
        clearProductFields();
        return;
    }

    try {
        const response = await fetch(`/com/api/products/?category_id=${categoryId}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error('Erreur lors de la récupération des produits');
        }

        const data = await response.json();
        const products = data?.products || [];

        productSelect.innerHTML = '<option value="">Sélectionner</option>';
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = product.designation;
            option.dataset.unitPrice = product.sale_unit_price;
            option.dataset.coefficient = product.coefficient;
            option.dataset.unitName = product.unit_name;
            productSelect.appendChild(option);
        });

        clearProductFields();
    } catch (error) {
        console.error(error);
        productSelect.innerHTML = '<option value="">Sélectionner</option>';
        clearProductFields();
    }
}

function clearProductFields() {
    const unitPriceInput = document.getElementById('productUnitPrice');
    const coefficientInput = document.getElementById('productCoefficient');
    const quantityInput = document.getElementById('productQuantity');

    if (unitPriceInput) unitPriceInput.value = '0.00';
    if (coefficientInput) coefficientInput.value = '1';
    if (quantityInput) quantityInput.value = '1';
}

function fillProductFields(productId) {
    const productSelect = document.getElementById('productSelect');
    const unitPriceInput = document.getElementById('productUnitPrice');
    const coefficientInput = document.getElementById('productCoefficient');

    if (!productSelect || !productId) {
        clearProductFields();
        return;
    }

    const selectedOption = productSelect.options[productSelect.selectedIndex];
    
    if (selectedOption && selectedOption.dataset.unitPrice) {
        if (unitPriceInput) unitPriceInput.value = parseFloat(selectedOption.dataset.unitPrice).toFixed(2);
        if (coefficientInput) coefficientInput.value = parseFloat(selectedOption.dataset.coefficient || 1).toFixed(1);
    } else {
        clearProductFields();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const clientSelect = document.getElementById('clientSelect');
    const dateProposalInput = document.getElementById('dateProposal');
    const productCategorySelect = document.getElementById('productCategorySelect');
    const productSelect = document.getElementById('productSelect');
    const addProductBtn = document.getElementById('addProductBtn');
    const addedProductsBody = document.getElementById('addedProductsBody');
    const addedProductsTotal = document.getElementById('addedProductsTotal');
    const previewLinks = document.querySelectorAll('.js-preview-proposal-link');

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

    const createAddedProductRowHtml = (item) => {
        const product = item?.product || {};
        const productId = Number(product.id || 0);
        const categoryName = product.category_name || '';
        const designation = product.designation || '';
        const quantity = Number(item?.quantity || 0);
        const unitPrice = Number(product.prix_unitaire || 0);
        const coefficient = Number(item?.coefficient || 0);
        const total = Number(product.total || (unitPrice * coefficient * quantity));

        return `
            <tr data-product-id="${productId}">
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${categoryName}</td>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${designation}</td>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${quantity}</td>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${unitPrice.toFixed(2)} €</td>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${coefficient.toFixed(2)}</td>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border); font-weight: 600; color: var(--accent);">${total.toFixed(2)} €</td>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                    <button type="button" data-action="remove-product" data-product-id="${productId}" style="background: none; border: none; color: var(--danger); cursor: pointer; font-size: 1.2rem;">🗑️</button>
                </td>
            </tr>
        `;
    };

    const upsertAddedProductRow = (item) => {
        if (!addedProductsBody || !item?.product?.id) {
            return;
        }

        const productId = Number(item.product.id);
        const existingRow = addedProductsBody.querySelector(`tr[data-product-id="${productId}"]`);
        const rowHtml = createAddedProductRowHtml(item);

        if (existingRow) {
            existingRow.outerHTML = rowHtml;
            return;
        }

        addedProductsBody.insertAdjacentHTML('beforeend', rowHtml);
    };

    const parseAmountFromText = (value) => {
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

    const refreshAddedProductsTotal = () => {
        if (!addedProductsBody || !addedProductsTotal) {
            return;
        }

        let total = 0;
        const rows = addedProductsBody.querySelectorAll('tr');

        rows.forEach((row) => {
            const totalCell = row.children[5];
            if (!totalCell) {
                return;
            }

            total += parseAmountFromText(totalCell.textContent || '0');
        });

        addedProductsTotal.textContent = `${total.toFixed(2)} €`;
    };

    const refreshGlobalTotal = (total) => {
        const totalAmount = document.getElementById('totalAmount');
        if (!totalAmount) {
            return;
        }

        if (Number.isFinite(total)) {
            totalAmount.textContent = `${total.toFixed(2)} €`;
            return;
        }

        totalAmount.textContent = addedProductsTotal ? addedProductsTotal.textContent : '0.00 €';
    };

    const saveProposalOptions = async () => {
        const clientId = clientSelect ? clientSelect.value : '';
        const dateProposition = dateProposalInput ? dateProposalInput.value : '';

        const response = await fetch('/com/api/proposals/options/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                client_id: clientId || null,
                date_proposition: dateProposition || '',
            }),
        });

        if (!response.ok) {
            let errorMessage = `Réponse HTTP invalide: ${response.status}`;
            try {
                const errorPayload = await response.json();
                if (errorPayload?.message) {
                    errorMessage = errorPayload.message;
                }
            } catch (parseError) {
                // No JSON payload available
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        if (!data?.success) {
            throw new Error(data?.message || 'Erreur lors de l\'enregistrement des options.');
        }
    };

    // Client selection
    if (clientSelect) {
        clientSelect.addEventListener('change', (event) => {
            loadClientDetails(event.target.value);
        });

        if (clientSelect.value) {
            loadClientDetails(clientSelect.value);
        } else {
            clearClientReadonlyFields();
        }
    }

    // Category selection
    if (productCategorySelect) {
        productCategorySelect.addEventListener('change', (event) => {
            loadProductsByCategory(event.target.value);
        });
    }

    // Product selection
    if (productSelect) {
        productSelect.addEventListener('change', (event) => {
            fillProductFields(event.target.value);
        });
    }

    // Add product button
    if (addProductBtn) {
        addProductBtn.addEventListener('click', async () => {
            const productId = document.getElementById('productSelect').value;
            const quantity = parseFloat(document.getElementById('productQuantity').value) || 0;
            const coefficient = parseFloat(document.getElementById('productCoefficient').value) || 1;

            if (!productId || quantity <= 0) {
                alert('Veuillez sélectionner un produit et entrer une quantité valide.');
                return;
            }

            try {
                const response = await fetch('/com/api/proposals/selected-products/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({
                        selected_products: [
                            {
                                product_id: Number(productId),
                                coefficient,
                                quantity,
                            },
                        ],
                    }),
                });

                if (!response.ok) {
                    throw new Error(`Réponse HTTP invalide: ${response.status}`);
                }

                const data = await response.json();
                if (!data?.success) {
                    throw new Error(data?.message || 'Erreur lors de l\'enregistrement.');
                }

                const updatedProposalItem = Array.isArray(data?.proposal)
                    ? data.proposal.find((item) => Number(item?.product?.id) === Number(productId))
                    : null;

                if (updatedProposalItem) {
                    upsertAddedProductRow(updatedProposalItem);
                    refreshAddedProductsTotal();
                }
            } catch (error) {
                console.error('Erreur lors de l\'ajout du produit :', error);
                alert('Erreur lors de l\'ajout du produit.');
                return;
            }

            // Clear form
            document.getElementById('productCategorySelect').value = '';
            document.getElementById('productSelect').innerHTML = '<option value="">Sélectionner</option>';
            clearProductFields();
        });
    }

    if (addedProductsBody) {
        addedProductsBody.addEventListener('click', async (event) => {
            const targetElement = event.target instanceof Element ? event.target : event.target?.parentElement;
            const removeButton = targetElement?.closest('button[data-action="remove-product"]');
            if (!removeButton) {
                return;
            }

            const row = removeButton.closest('tr[data-product-id]');
            const productId = Number(removeButton.dataset.productId || row?.dataset.productId || 0);

            if (!productId) {
                return;
            }

            removeButton.disabled = true;

            try {
                const response = await fetch('/com/api/proposals/remove-product/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({ product_id: productId }),
                });

                if (!response.ok) {
                    let errorMessage = `Réponse HTTP invalide: ${response.status}`;
                    try {
                        const errorPayload = await response.json();
                        if (errorPayload?.message) {
                            errorMessage = errorPayload.message;
                        }
                    } catch (parseError) {
                        // No JSON payload available
                    }
                    throw new Error(errorMessage);
                }

                const data = await response.json();
                if (!data?.success) {
                    throw new Error(data?.message || 'Erreur lors de la suppression.');
                }

                if (row) {
                    row.remove();
                }

                refreshAddedProductsTotal();
                refreshGlobalTotal(Number(data?.proposal_total));
            } catch (error) {
                console.error('Erreur lors de la suppression du produit :', error);
                alert('Erreur lors de la suppression du produit.');
            } finally {
                removeButton.disabled = false;
            }
        });
    }

    if (previewLinks.length > 0) {
        previewLinks.forEach((linkElement) => {
            linkElement.addEventListener('click', async (event) => {
                event.preventDefault();

                const href = linkElement.getAttribute('href') || '/com/preview_proposition_page/';
                linkElement.style.pointerEvents = 'none';

                try {
                    await saveProposalOptions();
                    window.location.href = href;
                } catch (error) {
                    console.error('Erreur lors de l\'enregistrement des options de proposition :', error);
                    alert('Impossible d\'enregistrer le client et la date avant l\'aperçu.');
                } finally {
                    linkElement.style.pointerEvents = '';
                }
            });
        });
    }

    refreshAddedProductsTotal();
    refreshGlobalTotal(parseAmountFromText(addedProductsTotal?.textContent || '0'));
});
