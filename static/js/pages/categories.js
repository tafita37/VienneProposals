

function handleEditCategory(id, name) {
	document.getElementById('categoryId').value = id;
	document.getElementById('categoryName').value = name;
	document.getElementById('modalTitle').textContent = 'Modifier la catégorie';
	document.getElementById('categoryModal').dataset.editId = id;
	document.getElementById('categoryModal').style.display = 'block';
}

function closeCategoryModal() {
	document.getElementById('categoryModal').style.display = 'none';
	document.getElementById('categoryModal').dataset.editId = '';
	document.getElementById('categoryCode').value = '';
	document.getElementById('categoryName').value = '';
	document.getElementById('modalTitle').textContent = 'Ajouter une catégorie';
	document.getElementById('modalMessage').textContent = '';
	document.getElementById('modalMessage').className = 'form-message';
}

document.addEventListener('DOMContentLoaded', () => {
	const addCategoryBtn = document.getElementById('addCategoryBtn');
	const deleteModal = document.getElementById('deleteConfirmModal');
	const deleteText = document.getElementById('deleteConfirmText');
	const deleteConfirmBtn = document.getElementById('deleteConfirmBtn');
	const deleteCancelBtn = document.getElementById('deleteCancelBtn');
	const deleteButtons = Array.from(document.querySelectorAll('.js-delete-category'));

	if (addCategoryBtn) {
		addCategoryBtn.addEventListener('click', () => {
			document.getElementById('categoryModal').style.display = 'block';
		});
	}

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

	const openDeleteModal = (deleteUrl, categoryName) => {
		const safeName = categoryName && categoryName.trim() ? categoryName.trim() : 'cette catégorie';
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
			const categoryName = button.getAttribute('data-category-name') || 'cette catégorie';
			if (!deleteUrl) return;
			openDeleteModal(deleteUrl, categoryName);
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
