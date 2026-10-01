const euroFormatter = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function parseNumber(value) {
  if (value === null || value === undefined) return NaN;
  const normalized = String(value).replace(",", ".").trim();
  return normalized === "" ? NaN : Number(normalized);
}

function roundTo2(value) {
  return Math.round(value * 100) / 100;
}

function formatCoefficient(value) {
  if (!Number.isFinite(value)) return "";
  return roundTo2(value)
    .toFixed(2)
    .replace(/\.0+$/, "")
    .replace(/(\.\d)0$/, "$1");
}

function getCsrfToken() {
  const cookie = document.cookie
    .split(";")
    .map((entry) => entry.trim())
    .find((entry) => entry.startsWith("csrftoken="));
  return cookie ? decodeURIComponent(cookie.substring("csrftoken=".length)) : "";
}

function setMessage(element, message, type = "info") {
  if (!element) return;
  element.textContent = message || "";
  element.classList.remove("info", "success", "warning", "error");
  if (message) element.classList.add(type);
}

function showOverlay(element, display = "flex") {
  element.classList.remove("hidden");
  element.style.display = display;
  element.setAttribute("aria-hidden", "false");
}

function hideOverlay(element) {
  element.classList.add("hidden");
  element.style.display = "none";
  element.setAttribute("aria-hidden", "true");
}

async function postJson(url, body, headers) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "X-CSRFToken": getCsrfToken(), Accept: "application/json", ...headers },
    body,
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok || !payload?.success) {
    throw new Error(payload?.message || `Réponse HTTP invalide: ${response.status}`);
  }
  return payload;
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("productsTable");
  if (!table) return;

  const urls = {
    products: table.dataset.apiUrl,
    delete: table.dataset.deleteUrl,
    explanation: table.dataset.explanationUrl,
    coefficient: table.dataset.coefficientUrl,
  };
  const tableBody = document.getElementById("productsTableBody");
  const rowTemplate = document.getElementById("productRowTemplate");
  const productsMessage = document.getElementById("productsMessage");
  const productsById = new Map();

  // ────────── Rendu du tableau ──────────

  const fillExplanation = (explanationRow, explanation) => {
    const text = explanationRow.querySelector('[data-role="explanation-text"]');
    text.textContent = explanation || "Aucune explication";
    text.classList.toggle("is-empty", !explanation);
    explanationRow.querySelector('[data-role="explanation-input"]').value = explanation || "";
  };

  const createProductRows = (product) => {
    const fragment = rowTemplate.content.cloneNode(true);
    const [productRow, explanationRow] = fragment.querySelectorAll("tr");
    const cells = {
      designation: product.designation,
      categories: product.category_names || "Non catégorisé",
      unit: product.unit_name,
      supplier: product.supplier_name || "Non renseigné",
      purchasePrice: `${euroFormatter.format(product.purchase_unit_price)} €`,
      salePrice: `${euroFormatter.format(product.sale_unit_price)} €`,
    };

    Object.entries(cells).forEach(([field, value]) => {
      productRow.querySelector(`[data-field="${field}"]`).textContent = value;
    });
    productRow.dataset.productId = product.id;
    explanationRow.dataset.productId = product.id;
    fillExplanation(explanationRow, product.explanation);
    return fragment;
  };

  const renderProducts = (products) => {
    productsById.clear();
    tableBody.replaceChildren();

    if (products.length === 0) {
      const emptyRow = tableBody.insertRow();
      const cell = emptyRow.insertCell();
      cell.colSpan = 7;
      cell.className = "products-empty";
      cell.textContent = "Aucun produit ne correspond aux filtres.";
      return;
    }

    products.forEach((product) => {
      productsById.set(String(product.id), product);
      tableBody.appendChild(createProductRows(product));
    });
  };

  // ────────── Filtres ──────────

  const categoryFilter = document.getElementById("categoryFilter");
  const searchFilter = document.getElementById("searchFilter");

  const fetchProducts = async () => {
    const params = new URLSearchParams();
    const nom = searchFilter.value.trim();
    const categoryId = categoryFilter.value;
    if (nom) params.append("nom", nom);
    if (categoryId) params.append("category_id", categoryId);

    setMessage(productsMessage, "Chargement des produits...", "warning");
    try {
      const response = await fetch(`${urls.products}?${params}`);
      if (!response.ok) throw new Error(`Réponse HTTP invalide: ${response.status}`);
      const data = await response.json();
      renderProducts(Array.isArray(data?.products) ? data.products : []);
      setMessage(productsMessage, "");
    } catch (error) {
      console.error("Erreur lors du chargement des produits :", error);
      setMessage(productsMessage, "Impossible de charger les produits filtrés.", "error");
    }
  };

  let searchTimeout;
  searchFilter.addEventListener("input", () => {
    window.clearTimeout(searchTimeout);
    searchTimeout = window.setTimeout(fetchProducts, 250);
  });
  categoryFilter.addEventListener("change", fetchProducts);

  // ────────── Modal d'ajout / modification ──────────

  const productModal = document.getElementById("productModal");
  const productForm = document.getElementById("productForm");
  const productModalTitle = document.getElementById("productModalTitle");
  const categoryPicker = document.getElementById("productCategory");
  const fields = {
    id: document.getElementById("productIdInput"),
    designation: document.getElementById("productName"),
    unit: document.getElementById("productUnit"),
    supplier: document.getElementById("productSupplier"),
    purchasePrice: document.getElementById("productPurchasePrice"),
    coefficient: document.getElementById("coefficient"),
    salePrice: document.getElementById("productSalePrice"),
  };
  const globalCoefficientValue = document.getElementById("globalCoefficientValue");

  const getGlobalCoefficient = () => {
    const value = parseNumber(globalCoefficientValue.textContent);
    return Number.isFinite(value) ? value : 1.3;
  };

  const syncCategoryChips = () => {
    categoryPicker.querySelectorAll(".category-chip").forEach((chip) => {
      chip.classList.toggle("is-selected", chip.querySelector("input").checked);
    });
  };

  const setSelectedCategories = (categoryIds) => {
    const selectedIds = new Set(categoryIds.map(String));
    categoryPicker.querySelectorAll('input[name="category_ids"]').forEach((input) => {
      input.checked = selectedIds.has(input.value);
    });
    syncCategoryChips();
  };

  const openProductModal = (product = null) => {
    productForm.reset();
    fields.id.value = product?.id ?? "";
    fields.designation.value = product?.designation ?? "";
    fields.unit.value = product?.unit_id ?? "";
    fields.supplier.value = product?.supplier_id ?? "";
    setSelectedCategories(product?.category_ids ?? []);

    if (product) {
      fields.purchasePrice.value = product.purchase_unit_price;
      fields.salePrice.value = product.sale_unit_price;
      fields.coefficient.value =
        product.purchase_unit_price > 0
          ? formatCoefficient(product.sale_unit_price / product.purchase_unit_price)
          : "";
    } else {
      fields.coefficient.value = formatCoefficient(getGlobalCoefficient());
    }

    productModalTitle.textContent = product ? "Modifier le produit" : "Ajouter un produit";
    productModal.style.display = "block";
  };

  const closeProductModal = () => {
    productModal.style.display = "none";
    productForm.reset();
    fields.id.value = "";
    setSelectedCategories([]);
  };

  document.getElementById("addProductBtn").addEventListener("click", () => openProductModal());
  productModal.querySelectorAll('[data-close-product-modal="true"]').forEach((button) => {
    button.addEventListener("click", closeProductModal);
  });
  categoryPicker.addEventListener("change", syncCategoryChips);

  // Prix de vente = prix d'achat × coefficient, recalculé dans le sens du dernier champ saisi
  let lastPricingInput = "coefficient";

  const updateSaleFromCoefficient = () => {
    const purchase = parseNumber(fields.purchasePrice.value);
    const coefficient = parseNumber(fields.coefficient.value);
    if (Number.isFinite(purchase) && Number.isFinite(coefficient)) {
      fields.salePrice.value = roundTo2(purchase * coefficient).toFixed(2);
    }
  };

  const updateCoefficientFromSale = () => {
    const purchase = parseNumber(fields.purchasePrice.value);
    const sale = parseNumber(fields.salePrice.value);
    if (Number.isFinite(purchase) && purchase > 0 && Number.isFinite(sale)) {
      fields.coefficient.value = formatCoefficient(sale / purchase);
    }
  };

  fields.coefficient.addEventListener("input", () => {
    lastPricingInput = "coefficient";
    updateSaleFromCoefficient();
  });
  fields.salePrice.addEventListener("input", () => {
    lastPricingInput = "sale";
    updateCoefficientFromSale();
  });
  fields.purchasePrice.addEventListener("input", () => {
    if (lastPricingInput === "sale") updateCoefficientFromSale();
    else updateSaleFromCoefficient();
  });

  // ────────── Suppression ──────────

  const deleteModal = document.getElementById("deleteConfirmModal");
  const deleteText = document.getElementById("deleteConfirmText");
  const deleteConfirmBtn = document.getElementById("deleteConfirmBtn");

  const openDeleteModal = (product) => {
    deleteText.textContent = `Voulez-vous vraiment supprimer ${product.designation} ?`;
    deleteConfirmBtn.href = `${urls.delete}?id=${encodeURIComponent(product.id)}`;
    showOverlay(deleteModal);
  };

  const closeDeleteModal = () => {
    hideOverlay(deleteModal);
    deleteConfirmBtn.setAttribute("href", "#");
  };

  deleteModal.addEventListener("click", (event) => {
    if (event.target.closest('[data-close-delete-modal="true"]')) closeDeleteModal();
  });

  // ────────── Explication ──────────

  const setExplanationEditing = (explanationRow, isEditing) => {
    explanationRow.querySelector('[data-role="explanation-view"]').hidden = isEditing;
    explanationRow.querySelector('[data-role="explanation-edit"]').hidden = !isEditing;
  };

  const saveExplanation = async (explanationRow, button) => {
    const product = productsById.get(explanationRow.dataset.productId);
    const input = explanationRow.querySelector('[data-role="explanation-input"]');
    const explanation = input.value.trim();

    button.disabled = true;
    try {
      await postJson(
        urls.explanation,
        JSON.stringify({ product_id: product.id, explanation }),
        { "Content-Type": "application/json" },
      );
      product.explanation = explanation;
      fillExplanation(explanationRow, explanation);
      setExplanationEditing(explanationRow, false);
    } catch (error) {
      console.error("Erreur lors de la modification de l'explication :", error);
      alert("Erreur lors de la modification de l'explication.");
    } finally {
      button.disabled = false;
    }
  };

  // ────────── Actions des lignes (délégation) ──────────

  tableBody.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;

    const row = button.closest("tr[data-product-id]");
    const product = productsById.get(row?.dataset.productId);
    if (!product) return;

    switch (button.dataset.action) {
      case "edit-product":
        openProductModal(product);
        break;
      case "delete-product":
        openDeleteModal(product);
        break;
      case "edit-explanation": {
        setExplanationEditing(row, true);
        const input = row.querySelector('[data-role="explanation-input"]');
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
        break;
      }
      case "cancel-explanation":
        fillExplanation(row, product.explanation);
        setExplanationEditing(row, false);
        break;
      case "save-explanation":
        saveExplanation(row, button);
        break;
    }
  });

  // ────────── Coefficient global ──────────

  const coefficientModal = document.getElementById("globalCoefficientModal");
  const coefficientForm = document.getElementById("globalCoefficientForm");
  const coefficientInput = document.getElementById("globalCoefficientInput");
  const coefficientMessage = document.getElementById("globalCoefficientMessage");
  const coefficientModalMessage = document.getElementById("globalCoefficientModalMessage");

  const openCoefficientModal = () => {
    coefficientInput.value = getGlobalCoefficient().toFixed(2);
    setMessage(coefficientModalMessage, "");
    showOverlay(coefficientModal);
    window.setTimeout(() => coefficientInput.focus(), 0);
  };

  const closeCoefficientModal = () => {
    hideOverlay(coefficientModal);
    setMessage(coefficientModalMessage, "");
  };

  const applyGlobalCoefficient = async () => {
    const coefficient = parseNumber(coefficientInput.value);
    if (!Number.isFinite(coefficient) || coefficient <= 0) {
      setMessage(coefficientModalMessage, "Veuillez saisir un coefficient supérieur à 0.", "error");
      return;
    }

    try {
      const payload = await postJson(
        urls.coefficient,
        new URLSearchParams({ coefficient: String(coefficient) }),
      );
      const formatted = euroFormatter.format(parseNumber(payload.coefficient ?? coefficient));
      globalCoefficientValue.textContent = formatted;
      setMessage(
        coefficientMessage,
        payload.message || `Coefficient modifié avec succès : ${formatted}.`,
        "success",
      );
      closeCoefficientModal();
      // Les prix de vente de tous les produits ont été recalculés côté serveur
      fetchProducts();
    } catch (error) {
      setMessage(
        coefficientModalMessage,
        error.message || "Erreur lors de la modification du coefficient.",
        "error",
      );
    }
  };

  document.getElementById("editGlobalCoefficientBtn").addEventListener("click", openCoefficientModal);
  coefficientModal.addEventListener("click", (event) => {
    if (event.target.closest('[data-close-coefficient-modal="true"]')) closeCoefficientModal();
  });
  coefficientForm.addEventListener("submit", (event) => {
    event.preventDefault();
    applyGlobalCoefficient();
  });

  // ────────── Échap ferme la fenêtre ouverte ──────────

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if (!deleteModal.classList.contains("hidden")) closeDeleteModal();
    if (!coefficientModal.classList.contains("hidden")) closeCoefficientModal();
    if (productModal.style.display === "block") closeProductModal();
  });

  renderProducts(JSON.parse(document.getElementById("productsData").textContent));
});
