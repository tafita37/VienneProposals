// Création d'un type d'entreprise depuis les formulaires client (création / modification)
function getCsrfToken() {
  const cookie = document.cookie
    .split(";")
    .map((entry) => entry.trim())
    .find((entry) => entry.startsWith("csrftoken="));
  return cookie ? decodeURIComponent(cookie.substring("csrftoken=".length)) : "";
}

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("companyTypeModal");
  const form = document.getElementById("companyTypeForm");
  const nameInput = document.getElementById("companyTypeName");
  const message = document.getElementById("companyTypeModalMessage");
  const saveButton = document.getElementById("saveCompanyTypeBtn");
  const openButton = document.getElementById("addCompanyTypeBtn");
  const companyTypeSelect = document.getElementById("companyType");

  if (!modal || !form || !nameInput || !message || !saveButton || !openButton || !companyTypeSelect)
    return;

  const setMessage = (text, type) => {
    message.textContent = text || "";
    message.className = "form-message";
    if (text && type) message.classList.add(type);
  };

  const openModal = () => {
    nameInput.value = "";
    setMessage("");
    modal.style.display = "block";
    modal.setAttribute("aria-hidden", "false");
    nameInput.focus();
  };

  const closeModal = () => {
    modal.style.display = "none";
    modal.setAttribute("aria-hidden", "true");
    openButton.focus();
  };

  const isOpen = () => modal.style.display !== "none";

  openButton.addEventListener("click", openModal);

  modal.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    // Clic sur le fond sombre ou sur un bouton de fermeture
    if (target === modal || target.dataset.closeCompanyTypeModal === "true") {
      closeModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && isOpen()) closeModal();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = nameInput.value.trim();
    if (!name) {
      setMessage("Le nom du type d'entreprise est obligatoire.", "error");
      nameInput.focus();
      return;
    }

    const body = new FormData();
    body.append("name", name);

    saveButton.disabled = true;
    try {
      const response = await fetch(modal.dataset.saveUrl, {
        method: "POST",
        headers: { "X-CSRFToken": getCsrfToken(), Accept: "application/json" },
        body,
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok || !payload?.success) {
        throw new Error(payload?.message || `Réponse HTTP invalide: ${response.status}`);
      }

      const { id, name: createdName } = payload.company_type;
      companyTypeSelect.add(new Option(createdName, id, true, true));
      // Rafraîchit le récapitulatif de l'étape 3
      companyTypeSelect.dispatchEvent(new Event("change"));
      closeModal();
    } catch (error) {
      setMessage(error.message, "error");
    } finally {
      saveButton.disabled = false;
    }
  });
});
