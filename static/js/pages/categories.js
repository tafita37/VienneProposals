function handleSaveCategory() {
	const messageEl = document.getElementById('modalMessage');
	if (messageEl) {
		messageEl.textContent = '';
		messageEl.className = 'form-message';
	}

	const code = document.getElementById('categoryCode')?.value.trim();
	const name = document.getElementById('categoryName')?.value.trim();

	if (!code || !name) {
		if (messageEl) {
			messageEl.textContent = 'Veuillez remplir tous les champs.';
			messageEl.classList.add('error');
		}
		return;
	}

	const categories = getCategories();
	const existing = categories.find(c => c.code === code);

	if (existing && !document.getElementById('categoryModal').dataset.editId) {
		if (messageEl) {
			messageEl.textContent = 'Une catégorie avec ce code existe déjà.';
			messageEl.classList.add('error');
		}
		return;
	}

	if (document.getElementById('categoryModal').dataset.editId) {
		const editId = document.getElementById('categoryModal').dataset.editId;
		const idx = categories.findIndex(c => c.code === editId);
		if (idx !== -1) {
			categories[idx] = { code, name };
			saveCategories(categories);
			closeCategoryModal();
			renderCategoriesTable();
		}
	} else {
		categories.push({ code, name });
		saveCategories(categories);
		closeCategoryModal();
		renderCategoriesTable();
	}
}

function handleEditCategory(code) {
	const categories = getCategories();
	const category = categories.find(c => c.code === code);
	if (!category) return;

	document.getElementById('categoryCode').value = category.code;
	document.getElementById('categoryName').value = category.name;
	document.getElementById('modalTitle').textContent = 'Modifier la catégorie';
	document.getElementById('categoryModal').dataset.editId = code;
	document.getElementById('categoryModal').style.display = 'block';
}

function handleDeleteCategory(code) {
	if (!confirm('Êtes-vous sûr de vouloir supprimer cette catégorie ?')) return;

	const categories = getCategories().filter(c => c.code !== code);
	saveCategories(categories);

	const messageEl = document.getElementById('categoriesMessage');
	if (messageEl) {
		messageEl.textContent = 'Catégorie supprimée.';
		messageEl.classList.add('success');
	}

	renderCategoriesTable();
}

function renderCategoriesTable() {
	const tbody = document.querySelector('#categoriesTable tbody');
	if (!tbody) return;

	const categories = getCategories();
	if (categories.length === 0) {
		tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; padding:2rem; color: var(--text-light);">Aucune catégorie disponible. Ajoutez-en une.</td></tr>`;
		return;
	}

	tbody.innerHTML = categories.map(category => `
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${category.code}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${category.name}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                <button class="btn btn-secondary" style="margin-right: 0.5rem;" onclick="handleEditCategory('${category.code}')">✏️</button>
                <button class="btn btn-secondary" style="background: var(--warning);" onclick="handleDeleteCategory('${category.code}')">🗑️</button>
            </td>
        </tr>
    `).join('');
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
	if (document.getElementById('categoriesTable')) {
		renderCategoriesTable();
	}

	const addCategoryBtn = document.getElementById('addCategoryBtn');
	if (addCategoryBtn) {
		addCategoryBtn.addEventListener('click', () => {
			document.getElementById('categoryModal').style.display = 'block';
		});
	}

	const saveCategoryBtn = document.getElementById('saveCategoryBtn');
	if (saveCategoryBtn) {
		saveCategoryBtn.addEventListener('click', handleSaveCategory);
	}
});
