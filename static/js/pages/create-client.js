function handleSaveClient() {
	const messageEl = document.getElementById('clientMessage');
	if (messageEl) {
		messageEl.textContent = '';
		messageEl.className = 'form-message';
	}

	const name = document.getElementById('clientName')?.value.trim();
	const address = document.getElementById('clientAddress')?.value.trim();
	const phone = document.getElementById('clientPhone')?.value.trim();
	const email = document.getElementById('clientEmail')?.value.trim();

	if (!name || !address || !phone || !email) {
		if (messageEl) {
			messageEl.textContent = 'Veuillez remplir tous les champs.';
			messageEl.classList.add('error');
		}
		return;
	}

	const clients = getClients();
	clients.push({ id: generateId(), name, address, phone, email });
	saveClients(clients);

	window.location.href = 'clients.html';
}

function handleEditClient(editId) {
	if (!editId) return false;

	const client = findClient(editId);
	if (!client) return false;

	const nameEl = document.getElementById('clientName');
	const addressEl = document.getElementById('clientAddress');
	const phoneEl = document.getElementById('clientPhone');
	const emailEl = document.getElementById('clientEmail');

	if (nameEl) nameEl.value = client.name || '';
	if (addressEl) addressEl.value = client.address || '';
	if (phoneEl) phoneEl.value = client.phone || '';
	if (emailEl) emailEl.value = client.email || '';

	const saveButton = document.getElementById('saveClient');
	if (saveButton) {
		saveButton.textContent = 'Mettre à jour';
		saveButton.onclick = (e) => {
			e.preventDefault();
			updateClient(editId);
		};
	}

	return true;
}

function updateClient(clientId) {
	const messageEl = document.getElementById('clientMessage');
	if (messageEl) {
		messageEl.textContent = '';
		messageEl.className = 'form-message';
	}

	const name = document.getElementById('clientName')?.value.trim();
	const address = document.getElementById('clientAddress')?.value.trim();
	const phone = document.getElementById('clientPhone')?.value.trim();
	const email = document.getElementById('clientEmail')?.value.trim();

	if (!name || !address || !phone || !email) {
		if (messageEl) {
			messageEl.textContent = 'Veuillez remplir tous les champs.';
			messageEl.classList.add('error');
		}
		return;
	}

	const clients = getClients();
	const idx = clients.findIndex(c => c.id === clientId);
	if (idx === -1) return;

	clients[idx] = { id: clientId, name, address, phone, email };
	saveClients(clients);
	window.location.href = 'clients.html';
}

document.addEventListener('DOMContentLoaded', () => {
	const saveButton = document.getElementById('saveClient');
	if (!saveButton) return;

	const params = new URLSearchParams(window.location.search);
	const editId = params.get('edit');

	const isEdit = handleEditClient(editId);
	if (!isEdit) {
		saveButton.addEventListener('click', handleSaveClient);
	}
});
