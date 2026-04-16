function handleEditProduct(id, designation, categoryIds, unit, purchasePrice, salePrice) {
	document.getElementById('productIdInput').value = id || '';
	document.getElementById('productName').value = designation || '';
	setSelectedCategories(document.getElementById('productCategory'), categoryIds);
	document.getElementById('productUnit').value = unit.id || '';

	purchasePrice = Number(purchasePrice || 0);
	salePrice = Number(salePrice || 0);

	document.getElementById('productPurchasePrice').value = purchasePrice || '';
	document.getElementById('productSalePrice').value = salePrice || '';

	if (purchasePrice > 0 && salePrice >= 0) {
		document.getElementById('coefficient').value = formatCoefficient(salePrice / purchasePrice);
	} else {
		document.getElementById('coefficient').value = '';
	}

	document.getElementById('productModalTitle').textContent = 'Modifier le produit';
	document.getElementById('productModal').dataset.editId = id;
	document.getElementById('productModal').style.display = 'block';
}

function closeProductModal() {
	document.getElementById('productModal').style.display = 'none';
	document.getElementById('productModal').dataset.editId = '';
	document.getElementById('productName').value = '';
	document.getElementById('productUnit').value = '';
	document.getElementById('productPurchasePrice').value = '';
	document.getElementById('coefficient').value = '';
	document.getElementById('productSalePrice').value = '';
	document.getElementById('productModalTitle').textContent = 'Ajouter un produit';

	const modalMessage = document.getElementById('productModalMessage');
	if (modalMessage) {
		modalMessage.textContent = '';
		modalMessage.className = 'form-message';
	}

	setSelectedCategories(document.getElementById('productCategory'), []);
}

function parseNumber(inputValue) {
	if (inputValue === null || inputValue === undefined) return NaN;
	const normalized = String(inputValue).replace(',', '.').trim();
	if (normalized === '') return NaN;
	return Number(normalized);
}

function formatCoefficient(value) {
	if (!Number.isFinite(value)) return '';
	const rounded = Math.round(value * 100) / 100;
	return rounded.toFixed(2).replace(/\.0+$/, '').replace(/(\.\d)0$/, '$1');
}

function parseCategoryIds(rawCategoryIds) {
	if (Array.isArray(rawCategoryIds)) {
		return rawCategoryIds.map((value) => String(value)).filter((value) => value);
	}

	if (typeof rawCategoryIds !== 'string') {
		return [];
	}

	return rawCategoryIds
		.split(',')
		.map((value) => value.trim())
		.filter((value) => value);
}

function setSelectedCategories(selectElement, categoryIds) {
	if (!selectElement) {
		return;
	}

	const selectedCategoryIds = new Set(parseCategoryIds(categoryIds));
	Array.from(selectElement.querySelectorAll('input[type="checkbox"][name="category_ids"]')).forEach((input) => {
		input.checked = selectedCategoryIds.has(String(input.value));
	});

	Array.from(selectElement.querySelectorAll('.category-chip')).forEach((chip) => {
		const checkbox = chip.querySelector('input[type="checkbox"][name="category_ids"]');
		chip.classList.toggle('is-selected', Boolean(checkbox && checkbox.checked));
	});
}

function bindPriceCoefficientSync() {
	const purchaseInput = document.getElementById('productPurchasePrice');
	const coefficientInput = document.getElementById('coefficient');
	const saleInput = document.getElementById('productSalePrice');

	if (!purchaseInput || !coefficientInput || !saleInput) return;

	let lastEditedTarget = 'coefficient';

	const updateSaleFromCoefficient = () => {
		const purchase = parseNumber(purchaseInput.value);
		const coefficient = parseNumber(coefficientInput.value);

		if (!Number.isFinite(purchase) || !Number.isFinite(coefficient)) {
			return;
		}

		const sale = purchase * coefficient;
		saleInput.value = (Math.round(sale * 100) / 100).toFixed(2);
	};

	const updateCoefficientFromSale = () => {
		const purchase = parseNumber(purchaseInput.value);
		const sale = parseNumber(saleInput.value);

		if (!Number.isFinite(purchase) || purchase <= 0 || !Number.isFinite(sale)) {
			return;
		}

		const coefficient = sale / purchase;
		coefficientInput.value = formatCoefficient(coefficient);
	};

	coefficientInput.addEventListener('input', () => {
		lastEditedTarget = 'coefficient';
		updateSaleFromCoefficient();
	});

	saleInput.addEventListener('input', () => {
		lastEditedTarget = 'sale';
		updateCoefficientFromSale();
	});

	purchaseInput.addEventListener('input', () => {
		if (lastEditedTarget === 'sale') {
			updateCoefficientFromSale();
			return;
		}

		updateSaleFromCoefficient();
	});
}

document.addEventListener('DOMContentLoaded', () => {
	const addProductBtn = document.getElementById('addProductBtn');
	const deleteModal = document.getElementById('deleteConfirmModal');
	const deleteText = document.getElementById('deleteConfirmText');
	const deleteConfirmBtn = document.getElementById('deleteConfirmBtn');
	const deleteCancelBtn = document.getElementById('deleteCancelBtn');
	const categoryFilter = document.getElementById('categoryFilter');
	const searchFilter = document.getElementById('searchFilter');
	const productsTableBody = document.getElementById('productsTableBody');
	const productsMessage = document.getElementById('productsMessage');

	if (addProductBtn) {
		addProductBtn.addEventListener('click', () => {
			document.getElementById('productModal').style.display = 'block';
		});
	}

	const categoryPicker = document.getElementById('productCategory');
	if (categoryPicker) {
		categoryPicker.addEventListener('change', () => {
			setSelectedCategories(categoryPicker, Array.from(categoryPicker.querySelectorAll('input[type="checkbox"][name="category_ids"]:checked')).map((input) => input.value));
		});
		setSelectedCategories(categoryPicker, []);
	}

	const euroFormatter = new Intl.NumberFormat('fr-FR', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	});

	const apiUrl = '/admin/product/api/products/';
	const deleteBaseUrl = '/com/product/delete/?id=';

	const setMessage = (message, type = 'info') => {
		if (!productsMessage) return;
		productsMessage.textContent = message || '';
		productsMessage.className = 'form-message';
		if (message) {
			productsMessage.classList.add(type);
		}
	};

	const openDeleteModal = (deleteUrl, productName) => {
		const safeName = productName && productName.trim() ? productName.trim() : 'ce produit';
		deleteText.textContent = `Voulez-vous vraiment supprimer ${safeName} ?`;
		deleteConfirmBtn.setAttribute('href', deleteUrl);
		deleteModal.classList.remove('hidden');
		deleteModal.style.display = 'flex';
		deleteModal.setAttribute('aria-hidden', 'false');
	};

	const bindDeleteButtons = (scope = document) => {
		Array.from(scope.querySelectorAll('.js-delete-product')).forEach((button) => {
			button.addEventListener('click', (event) => {
				event.preventDefault();
				const deleteUrl = button.getAttribute('href');
				const productName = button.getAttribute('data-product-name') || 'ce produit';
				if (!deleteUrl) return;
				openDeleteModal(deleteUrl, productName);
			});
		});
	};

	const attachRowEvents = (row) => {
		const editButton = row.querySelector('[data-edit-product="true"]');
		if (!editButton) return;

		editButton.addEventListener('click', () => {
			const categoryIds = parseCategoryIds(editButton.dataset.productCategoryIds || '');
			handleEditProduct(
				editButton.dataset.productId,
				editButton.dataset.productDesignation,
				categoryIds,
				{
					id: editButton.dataset.productUnitId,
					name: editButton.dataset.productUnitName,
				},
				editButton.dataset.productPurchasePrice,
				editButton.dataset.productSalePrice,
			);
		});
	};

	const escapeHtml = (value) =>
		String(value ?? '')
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#39;');

	const createRow = (product) => {
		const categoryNames = product.category_names || product.category_name || 'Non catégorisé';
		const categoryIds = Array.isArray(product.category_ids) ? product.category_ids : parseCategoryIds(product.category_ids || '');
		const row = document.createElement('tr');
		row.innerHTML = `
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${escapeHtml(product.designation)}</td>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${escapeHtml(categoryNames)}</td>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${escapeHtml(product.unit_name)}</td>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${euroFormatter.format(Number(product.purchase_unit_price || 0))} €</td>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${euroFormatter.format(Number(product.sale_unit_price || 0))} €</td>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
				<button
					type="button"
					class="btn btn-secondary"
					style="margin-right: 0.5rem;"
					data-edit-product="true"
					data-product-id="${escapeHtml(product.id)}"
					data-product-designation="${escapeHtml(product.designation)}"
					data-product-category-ids="${escapeHtml(categoryIds.join(','))}"
					data-product-category-names="${escapeHtml(categoryNames)}"
					data-product-unit-id="${escapeHtml(product.unit_id)}"
					data-product-unit-name="${escapeHtml(product.unit_name)}"
					data-product-purchase-price="${escapeHtml(product.purchase_unit_price)}"
					data-product-sale-price="${escapeHtml(product.sale_unit_price)}"
				>✏️</button>
				<a
					class="btn btn-secondary js-delete-product"
					style="background: var(--warning);"
					href="${deleteBaseUrl}${encodeURIComponent(product.id || '')}"
					data-product-name="${escapeHtml(product.designation)}"
				>🗑️</a>
			</td>
		`;

		attachRowEvents(row);
		return row;
	};

	const renderProducts = (products) => {
		if (!productsTableBody) return;

		productsTableBody.innerHTML = '';

		if (!Array.isArray(products) || products.length === 0) {
			const emptyRow = document.createElement('tr');
			emptyRow.innerHTML = '<td colspan="6" style="padding: 1rem; text-align: center; color: var(--text-light);">Aucun produit ne correspond aux filtres.</td>';
			productsTableBody.appendChild(emptyRow);
			return;
		}

		products.forEach((product) => {
			productsTableBody.appendChild(createRow(product));
		});

		bindDeleteButtons(productsTableBody);
	};

	const fetchProducts = () => {
		if (!categoryFilter || !searchFilter || !productsTableBody) return;

		const params = new URLSearchParams();
		const nom = searchFilter.value.trim();
		const categoryId = categoryFilter.value.trim();

		if (nom) params.append('nom', nom);
		if (categoryId) params.append('category_id', categoryId);

		setMessage('Chargement des produits...', 'warning');

		fetch(`${apiUrl}?${params.toString()}`)
			.then((response) => {
				if (!response.ok) {
					throw new Error(`Réponse HTTP invalide: ${response.status}`);
				}
				return response.json();
			})
			.then((data) => {
				const products = Array.isArray(data && data.products) ? data.products : [];
				renderProducts(products);
				setMessage(products.length ? '' : 'Aucun produit ne correspond aux filtres.', 'warning');
			})
			.catch((error) => {
				console.error('Erreur lors du chargement des produits:', error);
				setMessage('Impossible de charger les produits filtrés.', 'error');
			});
	};

	if (deleteModal && deleteText && deleteConfirmBtn && deleteCancelBtn) {
		deleteModal.classList.add('hidden');
		deleteModal.style.display = 'none';
		deleteModal.setAttribute('aria-hidden', 'true');

		const closeDeleteModal = () => {
			deleteModal.classList.add('hidden');
			deleteModal.style.display = 'none';
			deleteModal.setAttribute('aria-hidden', 'true');
			deleteConfirmBtn.setAttribute('href', '#');
		};

		deleteCancelBtn.addEventListener('click', closeDeleteModal);

		deleteModal.addEventListener('click', (event) => {
			const target = event.target;
			if (!(target instanceof HTMLElement)) return;
			if (target.dataset.closeDeleteModal === 'true') {
				closeDeleteModal();
			}
		});

		document.addEventListener('keydown', (event) => {
			if (event.key === 'Escape' && !deleteModal.classList.contains('hidden')) {
				closeDeleteModal();
			}
		});
	}

	if (productsTableBody) {
		Array.from(productsTableBody.querySelectorAll('tr')).forEach(attachRowEvents);
	}

	bindDeleteButtons();
	bindPriceCoefficientSync();

	if (categoryFilter) {
		categoryFilter.addEventListener('change', fetchProducts);
	}

	if (searchFilter) {
		let searchTimeout;
		searchFilter.addEventListener('input', () => {
			window.clearTimeout(searchTimeout);
			searchTimeout = window.setTimeout(fetchProducts, 250);
		});
	}

	if (categoryFilter || searchFilter) {
		fetchProducts();
	}
});
