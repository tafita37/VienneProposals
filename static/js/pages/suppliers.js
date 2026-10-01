function handleEditSupplier(id, name) {
	document.getElementById('supplierId').value = id;
	document.getElementById('supplierName').value = name;
	document.getElementById('modalTitle').textContent = 'Modifier le fournisseur';
	document.getElementById('supplierModal').dataset.editId = id;
	document.getElementById('supplierModal').style.display = 'block';
}

function closeSupplierModal() {
	document.getElementById('supplierModal').style.display = 'none';
	document.getElementById('supplierModal').dataset.editId = '';
	document.getElementById('supplierId').value = '';
	document.getElementById('supplierName').value = '';
	document.getElementById('modalTitle').textContent = 'Ajouter un fournisseur';
	document.getElementById('modalMessage').textContent = '';
	document.getElementById('modalMessage').className = 'form-message';
}

document.addEventListener('DOMContentLoaded', () => {
	const addSupplierBtn = document.getElementById('addSupplierBtn');
	const deleteModal = document.getElementById('deleteConfirmModal');
	const deleteText = document.getElementById('deleteConfirmText');
	const deleteConfirmBtn = document.getElementById('deleteConfirmBtn');
	const deleteCancelBtn = document.getElementById('deleteCancelBtn');
	const editButtons = Array.from(document.querySelectorAll('.js-edit-supplier'));
	const deleteButtons = Array.from(document.querySelectorAll('.js-delete-supplier'));

	if (addSupplierBtn) {
		addSupplierBtn.addEventListener('click', () => {
			document.getElementById('supplierModal').style.display = 'block';
		});
	}

	editButtons.forEach((button) => {
		button.addEventListener('click', () => {
			handleEditSupplier(
				button.getAttribute('data-supplier-id'),
				button.getAttribute('data-supplier-name') || ''
			);
		});
	});

	if (!deleteModal || !deleteText || !deleteConfirmBtn || !deleteCancelBtn || deleteButtons.length === 0) {
		return;
	}

	deleteModal.classList.add('hidden');
	deleteModal.style.display = 'none';
	deleteModal.setAttribute('aria-hidden', 'true');

	const closeDeleteModal = () => {
		deleteModal.classList.add('hidden');
		deleteModal.style.display = 'none';
		deleteModal.setAttribute('aria-hidden', 'true');
		deleteConfirmBtn.setAttribute('href', '#');
	};

	const openDeleteModal = (deleteUrl, supplierName) => {
		const safeName = supplierName && supplierName.trim() ? supplierName.trim() : 'ce fournisseur';
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
			const supplierName = button.getAttribute('data-supplier-name') || 'ce fournisseur';
			if (!deleteUrl) return;
			openDeleteModal(deleteUrl, supplierName);
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
});
