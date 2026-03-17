function handleRegister(e) {
	e.preventDefault();
	const messageEl = document.getElementById('registerMessage');
	if (messageEl) {
		messageEl.textContent = '';
		messageEl.className = 'form-message';
	}

	const name = document.getElementById('registerName').value.trim();
	const email = document.getElementById('registerEmail').value.trim();
	const password = document.getElementById('registerPassword').value;
	const confirm = document.getElementById('registerConfirm').value;

	if (!name || !email || !password || !confirm) {
		if (messageEl) {
			messageEl.textContent = 'Veuillez remplir tous les champs.';
			messageEl.classList.add('error');
		}
		return;
	}

	if (password !== confirm) {
		if (messageEl) {
			messageEl.textContent = 'Les mots de passe ne correspondent pas.';
			messageEl.classList.add('error');
		}
		return;
	}

	if (findUser(email)) {
		if (messageEl) {
			messageEl.textContent = 'Un compte existe déjà pour cet e-mail.';
			messageEl.classList.add('error');
		}
		return;
	}

	const users = getUsers();
	users.push({ name, email: email.toLowerCase(), password });
	saveUsers(users);

	localStorage.setItem('userLogged', 'true');
	localStorage.setItem('userName', name.capitalize());
	window.location.href = 'dashboard.html';
}
