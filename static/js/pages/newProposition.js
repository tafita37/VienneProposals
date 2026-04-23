function clearClientReadonlyFields() {
    const typeInput = document.getElementById('clientType');
    const addressInput = document.getElementById('clientAddress');
    const phoneInput = document.getElementById('clientPhone');
    const emailInput = document.getElementById('clientEmail');
    const websiteInput = document.getElementById('clientWebsite');
    const individualSection = document.getElementById('individualInfoSection');
    const companySection = document.getElementById('companyInfoSection');

    const individualFirstNameInput = document.getElementById('individualFirstName');
    const individualLastNameInput = document.getElementById('individualLastName');
    const individualBirthDateInput = document.getElementById('individualBirthDate');
    const individualIdCardNumberInput = document.getElementById('individualIdCardNumber');

    const companyNameInput = document.getElementById('companyName');
    const companyTypeInput = document.getElementById('companyType');
    const companyTypeIdInput = document.getElementById('companyTypeId');
    const companyRegistrationNumberInput = document.getElementById('companyRegistrationNumber');
    const companyTaxIdentificationNumberInput = document.getElementById('companyTaxIdentificationNumber');
    const companyCreatedAtInput = document.getElementById('companyCreatedAt');

    if (typeInput) typeInput.value = '';
    if (addressInput) addressInput.value = '';
    if (phoneInput) phoneInput.value = '';
    if (emailInput) emailInput.value = '';
    if (websiteInput) websiteInput.value = '';

    if (individualFirstNameInput) individualFirstNameInput.value = '';
    if (individualLastNameInput) individualLastNameInput.value = '';
    if (individualBirthDateInput) individualBirthDateInput.value = '';
    if (individualIdCardNumberInput) individualIdCardNumberInput.value = '';

    if (companyNameInput) companyNameInput.value = '';
    if (companyTypeInput) companyTypeInput.value = '';
    if (companyTypeIdInput) companyTypeIdInput.value = '';
    if (companyRegistrationNumberInput) companyRegistrationNumberInput.value = '';
    if (companyTaxIdentificationNumberInput) companyTaxIdentificationNumberInput.value = '';
    if (companyCreatedAtInput) companyCreatedAtInput.value = '';

    if (individualSection) individualSection.style.display = 'none';
    if (companySection) companySection.style.display = 'none';
}

async function loadClientDetails(clientId) {
    const typeInput = document.getElementById('clientType');
    const addressInput = document.getElementById('clientAddress');
    const phoneInput = document.getElementById('clientPhone');
    const emailInput = document.getElementById('clientEmail');
    const websiteInput = document.getElementById('clientWebsite');
    const individualSection = document.getElementById('individualInfoSection');
    const companySection = document.getElementById('companyInfoSection');

    const individualFirstNameInput = document.getElementById('individualFirstName');
    const individualLastNameInput = document.getElementById('individualLastName');
    const individualBirthDateInput = document.getElementById('individualBirthDate');
    const individualIdCardNumberInput = document.getElementById('individualIdCardNumber');

    const companyNameInput = document.getElementById('companyName');
    const companyTypeInput = document.getElementById('companyType');
    const companyTypeIdInput = document.getElementById('companyTypeId');
    const companyRegistrationNumberInput = document.getElementById('companyRegistrationNumber');
    const companyTaxIdentificationNumberInput = document.getElementById('companyTaxIdentificationNumber');
    const companyCreatedAtInput = document.getElementById('companyCreatedAt');

    if (!typeInput || !addressInput || !phoneInput || !emailInput || !websiteInput) {
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

        typeInput.value = client.client_type || (client.is_company ? 'BtoB' : 'BtoC') || '';
        addressInput.value = client.address || '';
        phoneInput.value = client.phone || '';
        emailInput.value = client.email || '';
        websiteInput.value = client.website_url || '';

        const isCompany = Boolean(client.is_company);
        if (individualSection) individualSection.style.display = isCompany ? 'none' : 'block';
        if (companySection) companySection.style.display = isCompany ? 'block' : 'none';

        if (individualFirstNameInput) individualFirstNameInput.value = client?.individual?.first_name || '';
        if (individualLastNameInput) individualLastNameInput.value = client?.individual?.last_name || '';
        if (individualBirthDateInput) individualBirthDateInput.value = client?.individual?.birth_date || '';
        if (individualIdCardNumberInput) individualIdCardNumberInput.value = client?.individual?.id_card_number || '';

        if (companyNameInput) companyNameInput.value = client?.company?.name || '';
        if (companyTypeInput) companyTypeInput.value = client?.company?.company_type || '';
        if (companyTypeIdInput) companyTypeIdInput.value = String(client?.company?.company_type_id || '');
        if (companyRegistrationNumberInput) companyRegistrationNumberInput.value = client?.company?.registration_number || '';
        if (companyTaxIdentificationNumberInput) companyTaxIdentificationNumberInput.value = client?.company?.tax_identification_number || '';
        if (companyCreatedAtInput) companyCreatedAtInput.value = client?.company?.created_at || '';
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
        if (coefficientInput) coefficientInput.value = parseFloat(1).toFixed(1);
    } else {
        clearProductFields();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const clientSelect = document.getElementById('clientSelect');
    const editClientBtn = document.getElementById('editClientBtn');
    const saveClientBtn = document.getElementById('saveClientBtn');
    const dateProposalInput = document.getElementById('dateProposal');
    const expirationDateInput = document.getElementById('expirationDate');
    const includeTaxInput = document.getElementById('includeTax');
    const productCategorySelect = document.getElementById('productCategorySelect');
    const productSelect = document.getElementById('productSelect');
    const addProductBtn = document.getElementById('addProductBtn');
    const addedProductsBody = document.getElementById('addedProductsBody');
    const addedProductsTotal = document.getElementById('addedProductsTotal');
    const summaryContainer = document.getElementById('summaryContainer');
    const proposalSummaryTable = document.getElementById('proposalSummaryTable');
    const previewLinks = document.querySelectorAll('.js-preview-proposal-link');
    let isClientEditMode = false;

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

    const setClientFieldsReadOnly = (isReadOnly) => {
        const clientTypeInput = document.getElementById('clientType');
        const clientAddressInput = document.getElementById('clientAddress');
        const clientPhoneInput = document.getElementById('clientPhone');
        const clientEmailInput = document.getElementById('clientEmail');
        const clientWebsiteInput = document.getElementById('clientWebsite');

        const individualFirstNameInput = document.getElementById('individualFirstName');
        const individualLastNameInput = document.getElementById('individualLastName');
        const individualBirthDateInput = document.getElementById('individualBirthDate');
        const individualIdCardNumberInput = document.getElementById('individualIdCardNumber');

        const companyNameInput = document.getElementById('companyName');
        const companyTypeInput = document.getElementById('companyType');
        const companyRegistrationNumberInput = document.getElementById('companyRegistrationNumber');
        const companyTaxIdentificationNumberInput = document.getElementById('companyTaxIdentificationNumber');
        const companyCreatedAtInput = document.getElementById('companyCreatedAt');

        const individualSection = document.getElementById('individualInfoSection');
        const companySection = document.getElementById('companyInfoSection');

        const commonInputs = [
            clientAddressInput,
            clientPhoneInput,
            clientEmailInput,
            clientWebsiteInput,
        ];

        commonInputs.forEach((inputElement) => {
            if (!inputElement) {
                return;
            }
            inputElement.readOnly = isReadOnly;
        });

        if (clientTypeInput) {
            clientTypeInput.readOnly = true;
        }

        const isIndividualVisible = Boolean(individualSection) && individualSection.style.display !== 'none';
        const isCompanyVisible = Boolean(companySection) && companySection.style.display !== 'none';

        [individualFirstNameInput, individualLastNameInput, individualBirthDateInput, individualIdCardNumberInput].forEach((inputElement) => {
            if (!inputElement) {
                return;
            }
            inputElement.readOnly = isReadOnly || !isIndividualVisible;
        });

        [companyNameInput, companyTypeInput, companyRegistrationNumberInput, companyTaxIdentificationNumberInput, companyCreatedAtInput].forEach((inputElement) => {
            if (!inputElement) {
                return;
            }
            inputElement.readOnly = isReadOnly || !isCompanyVisible;
        });
    };

    const setClientEditMode = (enabled) => {
        isClientEditMode = enabled;
        setClientFieldsReadOnly(!enabled);

        if (editClientBtn) {
            editClientBtn.textContent = enabled ? 'Annuler' : 'Modifier';
        }

        if (saveClientBtn) {
            saveClientBtn.style.display = enabled ? '' : 'none';
        }

        if (clientSelect) {
            clientSelect.disabled = enabled;
        }
    };

    const saveClientChanges = async () => {
        const clientId = clientSelect ? Number(clientSelect.value || 0) : 0;
        if (!clientId) {
            throw new Error('Aucun client sélectionné.');
        }

        const payload = {
            client_id: clientId,
            address: document.getElementById('clientAddress')?.value || '',
            phone: document.getElementById('clientPhone')?.value || '',
            email: document.getElementById('clientEmail')?.value || '',
            website_url: document.getElementById('clientWebsite')?.value || '',
        };

        const clientType = (document.getElementById('clientType')?.value || '').trim();
        if (clientType === 'BtoB') {
            payload.company_name = document.getElementById('companyName')?.value || '';
            payload.company_type_id = document.getElementById('companyTypeId')?.value || null;
            payload.registration_number = document.getElementById('companyRegistrationNumber')?.value || '';
            payload.tax_identification_number = document.getElementById('companyTaxIdentificationNumber')?.value || '';
            payload.created_at = document.getElementById('companyCreatedAt')?.value || '';
        } else {
            payload.first_name = document.getElementById('individualFirstName')?.value || '';
            payload.last_name = document.getElementById('individualLastName')?.value || '';
            payload.birth_date = document.getElementById('individualBirthDate')?.value || '';
            payload.id_card_number = document.getElementById('individualIdCardNumber')?.value || '';
        }

        const response = await fetch('/com/api/clients/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok || !data?.success) {
            throw new Error(data?.message || 'Erreur lors de la mise à jour du client.');
        }
    };

    const toIsoDate = (dateValue) => {
        const year = dateValue.getFullYear();
        const month = String(dateValue.getMonth() + 1).padStart(2, '0');
        const day = String(dateValue.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const addDaysToIsoDate = (isoDate, dayCount) => {
        if (typeof isoDate !== 'string' || !isoDate) {
            return '';
        }

        const parsedDate = new Date(`${isoDate}T00:00:00`);
        if (Number.isNaN(parsedDate.getTime())) {
            return '';
        }

        parsedDate.setDate(parsedDate.getDate() + dayCount);
        return toIsoDate(parsedDate);
    };

    const createAddedProductRowHtml = (item) => {
        const product = item?.product || {};
        const productId = Number(product.id || 0);
        const categoryName = product.category_name || '';
        const designation = product.designation || '';
        const quantity = Number(item?.quantity || 0);
        const unitPrice = Number(product.sale_unit_price ?? product.prix_unitaire_vente ?? product.prix_unitaire ?? 0);
        const coefficient = Number(item?.coefficient || 0);
        const total = Number(product.total || (unitPrice * coefficient * quantity));

        return `
            <tr data-product-id="${productId}">
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${categoryName}</td>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${designation}</td>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${quantity}</td>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${unitPrice.toFixed(2)} €</td>
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

    const escapeHtml = (value) => String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

    const safeNumber = (value) => {
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : 0;
    };

    const normalizeProposalItem = (item) => {
        const product = item?.product || {};
        const categoryName = String(product.category_name || '').trim() || 'Non catégorisé';
        const designation = String(product.designation || '').trim();
        const quantity = Math.max(0, safeNumber(item?.quantity));
        const coefficient = Math.max(0, safeNumber(item?.coefficient));
        const saleUnitPrice = Math.max(
            0,
            safeNumber(product.sale_unit_price ?? product.prix_unitaire_vente ?? product.prix_unitaire)
        );
        const totalFromApi = safeNumber(product.total);
        const total = Math.max(0, totalFromApi || (saleUnitPrice * coefficient * quantity));

        return {
            categoryName,
            designation,
            quantity,
            coefficient,
            saleUnitPrice,
            total,
        };
    };

    const buildSummaryCategoriesFromProposal = (proposal) => {
        if (!Array.isArray(proposal)) {
            return [];
        }

        const summaryMap = new Map();

        proposal.forEach((item) => {
            const normalized = normalizeProposalItem(item);

            if (!summaryMap.has(normalized.categoryName)) {
                summaryMap.set(normalized.categoryName, {
                    name: normalized.categoryName,
                    total: 0,
                    items: [],
                });
            }

            const category = summaryMap.get(normalized.categoryName);
            category.items.push(normalized);
            category.total += normalized.total;
        });

        return Array.from(summaryMap.values());
    };

    const renderSummaryByCategory = (summaryCategories) => {
        if (!summaryContainer) {
            return;
        }

        const heading = '<h2 style="margin-bottom: 1.5rem; color: var(--text-dark);">Récapitulatif par Catégorie</h2>';

        if (!summaryCategories.length) {
            summaryContainer.innerHTML = `${heading}
                <p style="color: var(--text-light); text-align: center; padding: 2rem;">
                    Veuillez aller au
                    <a href="/com/catalog_page/" style="color: var(--accent); text-decoration: underline;">catalogue</a>
                    pour sélectionner des produits...
                </p>`;
            return;
        }

        const bodyHtml = summaryCategories.map((category) => {
            const itemsHtml = category.items.map((item) => `
                <div class="summary-item">
                    <div class="summary-item-name">${escapeHtml(item.designation)}</div>
                    <div class="summary-item-qty">${item.quantity.toFixed(2)}</div>
                    <div class="summary-item-total">${item.total.toFixed(2)} €</div>
                </div>
            `).join('');

            return `
                <div class="summary-section">
                    <div class="summary-category-title">
                        <span>${escapeHtml(category.name)}</span>
                        <span>${category.total.toFixed(2)} €</span>
                    </div>
                    ${itemsHtml}
                </div>
            `;
        }).join('');

        summaryContainer.innerHTML = `${heading}${bodyHtml}`;
    };

    const renderProposalSummaryTable = (summaryCategories) => {
        if (!proposalSummaryTable) {
            return;
        }

        if (!summaryCategories.length) {
            proposalSummaryTable.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-light);">
                        Aucun produit sélectionné
                    </td>
                </tr>
            `;
            return;
        }

        const rowsHtml = summaryCategories.map((category) => {
            const categoryRow = `
                <tr style="background: #f9f7f4; font-weight: 600;">
                    <td>${escapeHtml(category.name)}</td>
                    <td colspan="5"></td>
                </tr>
            `;

            const itemRows = category.items.map((item) => `
                <tr>
                    <td></td>
                    <td>${escapeHtml(item.designation)}</td>
                    <td>${item.quantity.toFixed(2)}</td>
                    <td>${item.saleUnitPrice.toFixed(2)} €</td>
                    <td>${item.coefficient.toFixed(2)}</td>
                    <td class="price-calculated">${item.total.toFixed(2)} €</td>
                </tr>
            `).join('');

            return `${categoryRow}${itemRows}`;
        }).join('');

        proposalSummaryTable.innerHTML = rowsHtml;
    };

    const refreshDerivedProposalViews = (proposal) => {
        const summaryCategories = buildSummaryCategoriesFromProposal(proposal);
        renderSummaryByCategory(summaryCategories);
        renderProposalSummaryTable(summaryCategories);

        const total = summaryCategories.reduce((acc, category) => acc + safeNumber(category.total), 0);
        refreshGlobalTotal(total);
    };

    const saveProposalOptions = async () => {
        const clientId = clientSelect ? clientSelect.value : '';
        const dateProposition = dateProposalInput ? dateProposalInput.value : '';
        const expirationDate = expirationDateInput ? expirationDateInput.value : '';
        
        const includeTax = includeTaxInput ? includeTaxInput.checked : true;

        const response = await fetch('/com/api/proposals/options/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                client_id: clientId || null,
                date_proposition: dateProposition || '',
                expiration_date: expirationDate || '',
                include_tax: includeTax,
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
            setClientEditMode(false);
            loadClientDetails(event.target.value);
        });

        if (clientSelect.value) {
            loadClientDetails(clientSelect.value);
        } else {
            clearClientReadonlyFields();
        }
    }

    if (editClientBtn) {
        editClientBtn.addEventListener('click', async () => {
            const hasClient = clientSelect && String(clientSelect.value || '').trim() !== '';
            if (!hasClient) {
                alert('Veuillez sélectionner un client avant de modifier ses informations.');
                return;
            }

            if (isClientEditMode) {
                setClientEditMode(false);
                await loadClientDetails(clientSelect.value);
                return;
            }

            setClientEditMode(true);
        });
    }

    if (saveClientBtn) {
        saveClientBtn.addEventListener('click', async () => {
            saveClientBtn.disabled = true;
            try {
                await saveClientChanges();
                setClientEditMode(false);
                if (clientSelect && clientSelect.value) {
                    await loadClientDetails(clientSelect.value);
                }
                alert('Client mis à jour avec succès.');
            } catch (error) {
                console.error(error);
                alert(error.message || 'Impossible de mettre à jour le client.');
            } finally {
                saveClientBtn.disabled = false;
            }
        });
    }

    if (dateProposalInput && expirationDateInput) {
        if (!dateProposalInput.value) {
            dateProposalInput.value = toIsoDate(new Date());
        }

        const getDefaultExpirationDate = () => addDaysToIsoDate(dateProposalInput.value, 30);

        const syncExpirationDateWithProposalDate = () => {
            if (expirationDateInput.dataset.userModified === '1') {
                return;
            }

            expirationDateInput.value = getDefaultExpirationDate();
        };

        const updateUserModifiedFlag = () => {
            const defaultExpirationDate = getDefaultExpirationDate();
            if (!expirationDateInput.value || expirationDateInput.value === defaultExpirationDate) {
                expirationDateInput.dataset.userModified = '0';
                return;
            }

            expirationDateInput.dataset.userModified = '1';
        };

        if (!expirationDateInput.value) {
            expirationDateInput.dataset.userModified = '0';
            syncExpirationDateWithProposalDate();
        } else {
            updateUserModifiedFlag();
        }

        dateProposalInput.addEventListener('input', syncExpirationDateWithProposalDate);
        dateProposalInput.addEventListener('change', syncExpirationDateWithProposalDate);
        expirationDateInput.addEventListener('input', updateUserModifiedFlag);
        expirationDateInput.addEventListener('change', updateUserModifiedFlag);
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

                if (Array.isArray(data?.proposal)) {
                    refreshDerivedProposalViews(data.proposal);
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
                if (Array.isArray(data?.proposal)) {
                    refreshDerivedProposalViews(data.proposal);
                } else {
                    refreshGlobalTotal(Number(data?.proposal_total));
                }
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
                const previewUrl = new URL(href, window.location.origin);
                const clientId = clientSelect ? String(clientSelect.value || '').trim() : '';
                const dateProposition = dateProposalInput ? String(dateProposalInput.value || '').trim() : '';
                const expirationDate = expirationDateInput ? String(expirationDateInput.value || '').trim() : '';
                const includeTax = includeTaxInput ? includeTaxInput.checked : true;

                if (clientId) {
                    previewUrl.searchParams.set('client_id', clientId);
                }
                if (dateProposition) {
                    previewUrl.searchParams.set('date_proposition', dateProposition);
                }
                if (expirationDate) {
                    previewUrl.searchParams.set('expiration_date', expirationDate);
                }
                previewUrl.searchParams.set('include_tva', includeTax ? '1' : '0');

                linkElement.style.pointerEvents = 'none';

                try {
                    await saveProposalOptions();
                    window.location.href = previewUrl.toString();
                } catch (error) {
                    console.error('Erreur lors de l\'enregistrement des options de proposition :', error);
                    alert('Impossible d\'enregistrer le client, la date et la date d\'expiration avant l\'aperçu.');
                } finally {
                    linkElement.style.pointerEvents = '';
                }
            });
        });
    }

    refreshAddedProductsTotal();
    setClientEditMode(false);
    try {
        const initialDataElement = document.getElementById('initial-proposal-data');
        const initialProposal = initialDataElement ? JSON.parse(initialDataElement.textContent || '[]') : [];
        refreshDerivedProposalViews(initialProposal);
    } catch (error) {
        refreshGlobalTotal(parseAmountFromText(addedProductsTotal?.textContent || '0'));
    }
});
