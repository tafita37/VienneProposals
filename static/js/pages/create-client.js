document.addEventListener('DOMContentLoaded', () => {
	const saveButton = document.getElementById('saveClient');
	if (!saveButton) return;

	const params = new URLSearchParams(window.location.search);
	const editId = params.get('edit');
});
