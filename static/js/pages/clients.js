document.addEventListener("DOMContentLoaded", () => {
	const modal = document.getElementById("deleteConfirmModal");
	const deleteText = document.getElementById("deleteConfirmText");
	const confirmBtn = document.getElementById("deleteConfirmBtn");
	const cancelBtn = document.getElementById("deleteCancelBtn");
	const deleteButtons = Array.from(document.querySelectorAll(".js-delete-client"));

	if (!modal || !deleteText || !confirmBtn || !cancelBtn || deleteButtons.length === 0) {
		return;
	}

	const closeModal = () => {
		modal.classList.add("hidden");
		modal.setAttribute("aria-hidden", "true");
		confirmBtn.setAttribute("href", "#");
	};

	const openModal = (deleteUrl, clientName) => {
		const safeName = clientName && clientName.trim() ? clientName.trim() : "ce client";
		deleteText.textContent = `Voulez-vous vraiment supprimer ${safeName} ?`;
		confirmBtn.setAttribute("href", deleteUrl);
		modal.classList.remove("hidden");
		modal.setAttribute("aria-hidden", "false");
	};

	deleteButtons.forEach((button) => {
		button.addEventListener("click", (event) => {
			event.preventDefault();
			const deleteUrl = button.getAttribute("href");
			const clientName = button.getAttribute("data-client-name") || "ce client";
			if (!deleteUrl) return;
			openModal(deleteUrl, clientName);
		});
	});

	cancelBtn.addEventListener("click", closeModal);

	modal.addEventListener("click", (event) => {
		const target = event.target;
		if (!(target instanceof HTMLElement)) return;
		if (target.dataset.closeDeleteModal === "true") {
			closeModal();
		}
	});

	document.addEventListener("keydown", (event) => {
		if (event.key === "Escape" && !modal.classList.contains("hidden")) {
			closeModal();
		}
	});
});
