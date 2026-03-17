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
		const editId = parseInt(document.getElementById('productModal').dataset.editId);
		const idx = products.findIndex(p => p.id === editId);
		if (idx !== -1) {
			products[idx] = { ...products[idx], name, category, unit, price };
			saveProducts(products);
			closeProductModal();
			renderProductsTable();
		}
	} else {
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

document.addEventListener('DOMContentLoaded', () => {
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
});
