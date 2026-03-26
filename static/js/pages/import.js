const fileInput = document.getElementById('fileInput');
const loadingSpinner = document.getElementById('loadingSpinner');
const uploadIcon = document.getElementById('uploadIcon');
const uploadText = document.getElementById('uploadText');
const uploadArea = document.getElementById('uploadArea');
const importMessage = document.getElementById('importMessage');
const importForm = document.getElementById('importForm');

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
    uploadText.textContent = 'Glissez-déposez votre fichier Excel ici';
    uploadArea.style.pointerEvents = 'auto';
    uploadArea.style.opacity = '1';
}

if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) {
            showMessage('error', 'Aucun fichier sélectionné.');
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
