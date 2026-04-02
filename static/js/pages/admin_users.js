document.addEventListener('DOMContentLoaded', () => {
    const deleteModal = document.getElementById('deleteConfirmModal');
    const deleteText = document.getElementById('deleteConfirmText');
    const deleteConfirmBtn = document.getElementById('deleteConfirmBtn');
    const deleteCancelBtn = document.getElementById('deleteCancelBtn');
    const deleteButtons = Array.from(document.querySelectorAll('.js-delete-user'));

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

    const openDeleteModal = (deleteUrl, userName) => {
        const safeName = userName && userName !== '' ? userName : 'cet utilisateur';
        deleteText.textContent = `Voulez-vous vraiment desactiver ${safeName} ?`;
        deleteConfirmBtn.setAttribute('href', deleteUrl);
        deleteModal.classList.remove('hidden');
        deleteModal.style.display = 'flex';
        deleteModal.setAttribute('aria-hidden', 'false');
    };

    deleteButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            const deleteUrl = button.getAttribute('href');
            const userName = button.getAttribute('data-user-name') || 'cet utilisateur';
            if (!deleteUrl) return;
            openDeleteModal(deleteUrl, userName);
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
