function handleDeleteClient(clientId) {
	const clients = getClients().filter(c => c.id !== clientId);
	saveClients(clients);

	const messageEl = document.getElementById('clientsMessage');
	if (messageEl) {
		messageEl.textContent = 'Client supprimé.';
		messageEl.classList.add('success');
	}

	renderClientsTable();
}

function renderClientsTable() {
	const tbody = document.querySelector('#clientsTable tbody');
	if (!tbody) return;

	const clients = getClients();
	if (clients.length === 0) {
		tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:2rem; color: var(--text-light);">Aucun client disponible. Ajoutez-en un.</td></tr>`;
		return;
	}

	tbody.innerHTML = clients.map(client => `
		<tr>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${client.name}</td>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${client.email}</td>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${client.phone}</td>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">${client.address}</td>
			<td style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
				<button class="btn btn-secondary" style="margin-right: 0.5rem;" onclick="location.href='create-client.html?edit=${client.id}'">✏️</button>
				<button class="btn btn-secondary" style="background: var(--warning);" onclick="handleDeleteClient('${client.id}')">🗑️</button>
			</td>
		</tr>
	`).join('');
}

document.addEventListener('DOMContentLoaded', () => {
	if (document.getElementById('clientsTable')) {
		renderClientsTable();
	}
});
