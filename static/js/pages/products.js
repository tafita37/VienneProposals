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
	const addProductBtn = document.getElementById('addProductBtn');
	if (addProductBtn) {
		addProductBtn.addEventListener('click', () => {
			document.getElementById('productModal').style.display = 'block';
		});
	}
});
