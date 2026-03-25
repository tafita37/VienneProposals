function handleEditProduct(id, designation, category, unit, purchasePrice, salePrice) {

	document.getElementById('productIdInput').value = id || '';
	document.getElementById('productName').value = designation || '';
	document.getElementById('productCategory').value = category.id || '';
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
	document.getElementById('productCategory').value = '';
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
	const deleteButtons = Array.from(document.querySelectorAll('.js-delete-product'));

	if (addProductBtn) {
		addProductBtn.addEventListener('click', () => {
			document.getElementById('productModal').style.display = 'block';
		});
	}

	if (deleteModal && deleteText && deleteConfirmBtn && deleteCancelBtn && deleteButtons.length > 0) {
		deleteModal.classList.add('hidden');
		deleteModal.style.display = 'none';
		deleteModal.setAttribute('aria-hidden', 'true');

		const closeDeleteModal = () => {
			deleteModal.classList.add('hidden');
			deleteModal.style.display = 'none';
			deleteModal.setAttribute('aria-hidden', 'true');
			deleteConfirmBtn.setAttribute('href', '#');
		};

		const openDeleteModal = (deleteUrl, productName) => {
			const safeName = productName && productName.trim() ? productName.trim() : 'ce produit';
			deleteText.textContent = `Voulez-vous vraiment supprimer ${safeName} ?`;
			deleteConfirmBtn.setAttribute('href', deleteUrl);
			deleteModal.classList.remove('hidden');
			deleteModal.style.display = 'flex';
			deleteModal.setAttribute('aria-hidden', 'false');
		};

		deleteButtons.forEach((button) => {
			button.addEventListener('click', (event) => {
				event.preventDefault();
				const deleteUrl = button.getAttribute('href');
				const productName = button.getAttribute('data-product-name') || 'ce produit';
				if (!deleteUrl) return;
				openDeleteModal(deleteUrl, productName);
			});
		});

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

	bindPriceCoefficientSync();
});
