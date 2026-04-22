const fileInput = document.getElementById('fileInput');
const loadingSpinner = document.getElementById('loadingSpinner');
const uploadIcon = document.getElementById('uploadIcon');
const uploadText = document.getElementById('uploadText');
const uploadArea = document.getElementById('uploadArea');
const importMessage = document.getElementById('importMessage');
const importForm = document.getElementById('importForm');
const categoryModeInputs = document.querySelectorAll('input[name="category_mode"]');
const existingCategoryGroup = document.getElementById('existingCategoryGroup');
const existingCategorySelect = document.getElementById('existingCategorySelect');
const reloadCategoriesBtn = document.getElementById('reloadCategoriesBtn');
const newCategoryGroup = document.getElementById('newCategoryGroup');
const newCategoryNameInput = document.getElementById('newCategoryName');
const productModeStep = document.getElementById('productModeStep');
const productModeInputs = document.querySelectorAll('input[name="product_mode"]');
const IMPORT_CATEGORIES_API_URL = '/admin/import/api/categories/';

function showMessage(type, message) {
    importMessage.textContent = message;
    importMessage.className = `form-message ${type === 'success' ? 'success' : 'error'}`;
}

function clearMessage() {
    importMessage.textContent = '';
    importMessage.className = 'form-message';
}

function showLoading() {
    loadingSpinner.style.display = 'block';
    uploadIcon.style.display = 'none';
    uploadText.textContent = 'Importation en cours...';
    uploadArea.style.pointerEvents = 'none';
    uploadArea.style.opacity = '0.7';
    clearMessage();
}

function hideLoading() {
    loadingSpinner.style.display = 'none';
    uploadIcon.style.display = 'block';
    const isExistingMode = getSelectedCategoryMode() === 'existing';
    uploadText.textContent = isExistingMode
        ? '3. Importez ensuite votre fichier Excel'
        : '2. Importez ensuite votre fichier Excel';
    uploadArea.style.pointerEvents = 'auto';
    uploadArea.style.opacity = '1';
}

function getSelectedCategoryMode() {
    const checkedInput = document.querySelector('input[name="category_mode"]:checked');
    return checkedInput ? checkedInput.value : 'existing';
}

function syncCategoryModeUI() {
    const mode = getSelectedCategoryMode();
    const isExistingMode = mode === 'existing';

    if (existingCategoryGroup) {
        existingCategoryGroup.style.display = isExistingMode ? 'block' : 'none';
    }
    if (newCategoryGroup) {
        newCategoryGroup.style.display = isExistingMode ? 'none' : 'block';
    }
    if (existingCategorySelect) {
        existingCategorySelect.required = isExistingMode;
    }
    if (newCategoryNameInput) {
        newCategoryNameInput.required = !isExistingMode;
    }

    if (productModeStep) {
        productModeStep.style.display = isExistingMode ? 'block' : 'none';
    }
    if (productModeInputs.length) {
        productModeInputs.forEach((input) => {
            input.disabled = !isExistingMode;
        });
    }
    if (!isExistingMode) {
        const newProductMode = document.querySelector('input[name="product_mode"][value="new"]');
        if (newProductMode) {
            newProductMode.checked = true;
        }
    }

    if (uploadText) {
        uploadText.textContent = isExistingMode
            ? '3. Importez ensuite votre fichier Excel'
            : '2. Importez ensuite votre fichier Excel';
    }
}

async function loadExistingCategories() {
    if (!existingCategorySelect) {
        return;
    }

    const currentSelection = existingCategorySelect.value;
    existingCategorySelect.disabled = true;
    existingCategorySelect.innerHTML = '<option value="">Chargement des catégories...</option>';

    try {
        const response = await fetch(IMPORT_CATEGORIES_API_URL, {
            method: 'GET',
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error('HTTP ' + response.status);
        }

        const data = await response.json();
        const validOptions = Array.isArray(data.categories)
            ? data.categories.filter((category) => category && category.id && category.name)
            : [];

        if (!validOptions.length) {
            existingCategorySelect.innerHTML = '<option value="">Aucune catégorie disponible</option>';
            showMessage('error', 'Aucune catégorie existante trouvée. Choisissez "Nouvelle catégorie".');
            return;
        }

        existingCategorySelect.innerHTML = '<option value="">-- Choisir une catégorie --</option>';
        validOptions.forEach((category) => {
            const newOption = document.createElement('option');
            newOption.value = String(category.id);
            newOption.textContent = String(category.name).trim();
            existingCategorySelect.appendChild(newOption);
        });

        if (currentSelection) {
            existingCategorySelect.value = currentSelection;
        }
        clearMessage();
    } catch (error) {
        existingCategorySelect.innerHTML = '<option value="">Erreur de chargement des catégories</option>';
        showMessage('error', 'Erreur de chargement des catégories existantes. Réessayez.');
    } finally {
        existingCategorySelect.disabled = false;
    }
}

function validateCategoryFields() {
    const mode = getSelectedCategoryMode();

    if (mode === 'existing') {
        if (!existingCategorySelect || !existingCategorySelect.value) {
            showMessage('error', 'Sélectionnez une catégorie existante avant d\'importer le fichier.');
            return false;
        }
        return true;
    }

    return true;
}

if (categoryModeInputs.length) {
    categoryModeInputs.forEach((input) => {
        input.addEventListener('change', () => {
            syncCategoryModeUI();
            clearMessage();
        });
    });
}

if (reloadCategoriesBtn) {
    reloadCategoriesBtn.addEventListener('click', () => {
        loadExistingCategories();
    });
}

syncCategoryModeUI();
loadExistingCategories();

if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) {
            showMessage('error', 'Aucun fichier sélectionné.');
            return;
        }

        if (!validateCategoryFields()) {
            fileInput.value = '';
            return;
        }

        if (!/\.(xlsx|xlsm)$/i.test(file.name)) {
            showMessage('error', 'Format non supporté. Utilisez un fichier .xlsx ou .xlsm.');
            fileInput.value = '';
            return;
        }

        showLoading();
        if (importForm) {
            importForm.submit();
        }
    });
}
