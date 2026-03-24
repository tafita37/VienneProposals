document.addEventListener("DOMContentLoaded", () => {
  const saveButton = document.getElementById("saveClient");
  const prevStepButton = document.getElementById("prevStep");
  const nextStepButton = document.getElementById("nextStep");
  const clientTypeSelect = document.getElementById("clientType");
  const individualSection = document.getElementById("individualSection");
  const companySection = document.getElementById("companySection");
  const stepElements = Array.from(document.querySelectorAll(".wizard-step"));
  const stepIndicators = Array.from(
    document.querySelectorAll("[data-step-indicator]"),
  );
  const summaryIndividualSection = document.getElementById(
    "summaryIndividualSection",
  );
  const summaryCompanySection = document.getElementById(
    "summaryCompanySection",
  );

  const summaryMappings = [
    { sourceId: "clientAddress", targetId: "summaryClientAddress" },
    { sourceId: "clientPhone", targetId: "summaryClientPhone" },
    { sourceId: "clientEmail", targetId: "summaryClientEmail" },
    { sourceId: "clientWebsite", targetId: "summaryClientWebsite" },
    { sourceId: "individualFirstName", targetId: "summaryIndividualFirstName" },
    { sourceId: "individualLastName", targetId: "summaryIndividualLastName" },
    { sourceId: "individualBirthDate", targetId: "summaryIndividualBirthDate" },
    {
      sourceId: "individualIdCardNumber",
      targetId: "summaryIndividualIdCardNumber",
    },
    { sourceId: "companyName", targetId: "summaryCompanyName" },
    { sourceId: "companyType", targetId: "summaryCompanyType" },
    {
      sourceId: "companyRegistrationNumber",
      targetId: "summaryCompanyRegistrationNumber",
    },
    {
      sourceId: "companyTaxIdentificationNumber",
      targetId: "summaryCompanyTaxIdentificationNumber",
    },
    { sourceId: "companyCreatedAt", targetId: "summaryCompanyCreatedAt" },
  ];

  if (
    !saveButton ||
    !prevStepButton ||
    !nextStepButton ||
    !clientTypeSelect ||
    !individualSection ||
    !companySection ||
    stepElements.length === 0
  )
    return;

  const params = new URLSearchParams(window.location.search);
  const editId = params.get("edit");
  let currentStep = 1;
  const totalSteps = stepElements.length;

  const toggleSectionRequirements = (section, isVisible, activeStep) => {
    const conditionalFields = section.querySelectorAll(
      '[data-required-when-visible="true"]',
    );
    conditionalFields.forEach((field) => {
      field.required = isVisible && activeStep === 2;
    });
  };

  const isFieldVisible = (field) => {
    if (field.closest(".hidden")) return false;
    const step = field.closest(".wizard-step");
    return !!step && step.classList.contains("active");
  };

  const validateCurrentStep = () => {
    const step = stepElements.find(
      (item) => Number(item.dataset.step) === currentStep,
    );
    if (!step) return false;

    const fields = step.querySelectorAll("input, select, textarea");
    for (const field of fields) {
      if (!isFieldVisible(field)) continue;
      if (!field.checkValidity()) {
        field.reportValidity();
        return false;
      }
    }

    return true;
  };

  const updateClientTypeSections = () => {
    const selectedType = clientTypeSelect.value;
    const isCompany = selectedType === "1";
    const isIndividual = selectedType === "0";

    individualSection.classList.toggle("hidden", !isIndividual);
    companySection.classList.toggle("hidden", !isCompany);

    toggleSectionRequirements(individualSection, isIndividual, currentStep);
    toggleSectionRequirements(companySection, isCompany, currentStep);
  };

  const getFieldValue = (field) => {
    if (!field) return "-";
    const value = field.value ? field.value.trim() : "";
    return value || "-";
  };

  const updateSummary = () => {
    summaryMappings.forEach(({ sourceId, targetId }) => {
      const sourceField = document.getElementById(sourceId);
      const targetField = document.getElementById(targetId);
      if (!targetField) return;

      if (sourceField.id === "companyType") {
        const selectedOption = sourceField.options[sourceField.selectedIndex];
        const optionLabel = selectedOption
          ? selectedOption.textContent.trim()
          : "";
        targetField.textContent = sourceField.value ? optionLabel || "-" : "-";
      } else if (sourceField.id == "clientWebsite") {
        const value = getFieldValue(sourceField);
        if (value !== "-") {
          targetField.innerHTML = `<a href="${value}" target="_blank">${value}</a>`;
        } else {
          targetField.innerHTML = "-";
        }
      } else {
        targetField.textContent = getFieldValue(sourceField);
      }
    });

    if (summaryIndividualSection && summaryCompanySection) {
      const selectedType = clientTypeSelect.value;

      summaryIndividualSection.classList.toggle(
        "hidden",
        selectedType !== "0",
      );
      summaryCompanySection.classList.toggle(
        "hidden",
        selectedType !== "1",
      );
    }
  };

  const renderStep = () => {
    stepElements.forEach((step) => {
      const stepNumber = Number(step.dataset.step);
      step.classList.toggle("active", stepNumber === currentStep);
    });

    stepIndicators.forEach((indicator) => {
      const stepNumber = Number(indicator.dataset.stepIndicator);
      indicator.classList.toggle("active", stepNumber === currentStep);
      indicator.classList.toggle("done", stepNumber < currentStep);
    });

    prevStepButton.classList.toggle("hidden", currentStep === 1);
    nextStepButton.classList.toggle("hidden", currentStep === totalSteps);

    updateClientTypeSections();
    updateSummary();
  };

  prevStepButton.addEventListener("click", () => {
    if (currentStep > 1) {
      currentStep -= 1;
      renderStep();
    }
  });

  nextStepButton.addEventListener("click", () => {
    if (!validateCurrentStep()) return;

    if (currentStep < totalSteps) {
      currentStep += 1;
      renderStep();
    }
  });

  clientTypeSelect.addEventListener("change", updateClientTypeSections);
  summaryMappings.forEach(({ sourceId }) => {
    const sourceField = document.getElementById(sourceId);
    if (!sourceField) return;
    sourceField.addEventListener("input", updateSummary);
    sourceField.addEventListener("change", updateSummary);
  });
  clientTypeSelect.addEventListener("change", updateSummary);
  renderStep();
});
