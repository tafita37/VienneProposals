function handleLogin(e) {
	e.preventDefault();
	const messageEl = document.getElementById('loginMessage');
	if (messageEl) {
		messageEl.textContent = '';
		messageEl.className = 'form-message';
	}

	const username = document.getElementById('username').value.trim();
	const password = document.getElementById('password').value;
	const user = findUser(username);

	if (!user || user.password !== password) {
		if (messageEl) {
			messageEl.textContent = 'Identifiant ou mot de passe incorrect.';
			messageEl.classList.add('error');
		}
		return;
	}

	localStorage.setItem('userLogged', 'true');
	localStorage.setItem('userName', (user.name || user.email.split('@')[0]).capitalize());
	window.location.href = 'dashboard.html';
}
