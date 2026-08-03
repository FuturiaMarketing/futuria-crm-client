(() => {
  "use strict";

  const form = document.getElementById("credential-form");
  const accountInput = document.getElementById("account-link");
  const keyInput = document.getElementById("private-key");
  const accountError = document.getElementById("account-error");
  const keyError = document.getElementById("key-error");
  const formError = document.getElementById("form-error");
  const accountCard = document.getElementById("account-card");
  const accountKicker = document.getElementById("account-kicker");
  const accountName = document.getElementById("account-name");
  const statusPill = document.getElementById("status-pill");
  const submitButton = document.getElementById("submit-button");
  const submitLabel = document.getElementById("submit-label");
  const visibilityToggle = document.getElementById("visibility-toggle");
  const successState = document.getElementById("success-state");
  const successAccount = document.getElementById("success-account");
  const cancelButton = document.getElementById("cancel-button");
  const closeButton = document.getElementById("close-button");
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
  const previewMode = document.querySelector('meta[name="preview-mode"]').content === "true";

  if (previewMode) document.getElementById("preview-banner").hidden = false;

  document.querySelectorAll("#guide-accordion details").forEach((detail) => {
    detail.addEventListener("toggle", () => {
      if (!detail.open) return;
      document.querySelectorAll("#guide-accordion details").forEach((other) => {
        if (other !== detail) other.open = false;
      });
    });
  });

  function parseLocation(value) {
    const input = value.trim();
    if (/^[A-Za-z0-9_-]{6,128}$/.test(input)) return input;
    let parsed;
    try {
      parsed = new URL(input);
    } catch {
      throw new Error("Incolla il link completo del tuo account Futuria CRM.");
    }
    if (parsed.protocol !== "https:" || parsed.hostname !== "app.futuriamarketing.com") {
      throw new Error("Il link deve appartenere a Futuria CRM.");
    }
    const match = parsed.pathname.match(/\/(?:v2\/)?location\/([A-Za-z0-9_-]{6,128})(?:\/|$)/);
    if (!match) throw new Error("Non trovo l’account nel link. Copia di nuovo l’indirizzo.");
    return match[1];
  }

  function resetErrors() {
    accountError.textContent = "";
    keyError.textContent = "";
    formError.textContent = "";
    accountInput.closest(".field-group").classList.remove("has-error");
    keyInput.closest(".field-group").classList.remove("has-error");
  }

  function updateAccountPreview() {
    try {
      const location = parseLocation(accountInput.value);
      accountCard.classList.add("is-ready");
      accountKicker.textContent = "Account rilevato";
      accountName.textContent = `ID ••••${location.slice(-4)}`;
      statusPill.textContent = "Pronto";
      accountError.textContent = "";
      accountInput.closest(".field-group").classList.remove("has-error");
    } catch {
      accountCard.classList.remove("is-ready", "is-success");
      accountKicker.textContent = "In attesa del link";
      accountName.textContent = "Il tuo account Futuria CRM";
      statusPill.textContent = "Da verificare";
    }
  }

  accountInput.addEventListener("input", updateAccountPreview);

  visibilityToggle.addEventListener("click", () => {
    const showing = keyInput.type === "text";
    keyInput.type = showing ? "password" : "text";
    visibilityToggle.textContent = showing ? "Mostra" : "Nascondi";
    visibilityToggle.setAttribute("aria-pressed", String(!showing));
    keyInput.focus();
  });

  function validate() {
    resetErrors();
    let valid = true;
    try {
      parseLocation(accountInput.value);
    } catch (error) {
      accountError.textContent = error.message;
      accountInput.closest(".field-group").classList.add("has-error");
      valid = false;
    }
    if (!/^pit-[A-Za-z0-9._-]{6,2048}$/.test(keyInput.value.trim())) {
      keyError.textContent = "Copia di nuovo la chiave privata completa: deve iniziare con pit-.";
      keyInput.closest(".field-group").classList.add("has-error");
      valid = false;
    }
    return valid;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validate()) return;

    submitButton.disabled = true;
    submitLabel.textContent = "Verifico e collego…";
    const privateKey = keyInput.value.trim();
    keyInput.value = "";

    try {
      const response = await fetch("connect", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-Futuria-CSRF": csrfToken,
        },
        body: JSON.stringify({
          accountLink: accountInput.value.trim(),
          privateKey,
        }),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.message || "Collegamento non riuscito.");

      accountCard.classList.add("is-success");
      accountKicker.textContent = "Account collegato";
      accountName.textContent = result.accountName;
      statusPill.textContent = result.preview ? "Anteprima" : "Collegato";
      successAccount.textContent = result.accountName;
      form.hidden = true;
      successState.hidden = false;
      successState.focus();
    } catch (error) {
      formError.textContent = error.message || "Collegamento non riuscito.";
      keyInput.focus();
    } finally {
      submitButton.disabled = false;
      submitLabel.textContent = "Conferma e collega";
    }
  });

  function closeWindow() {
    keyInput.value = "";
    window.close();
    setTimeout(() => {
      if (!window.closed) window.history.back();
    }, 120);
  }

  cancelButton.addEventListener("click", closeWindow);
  closeButton.addEventListener("click", closeWindow);
  window.addEventListener("pagehide", () => { keyInput.value = ""; });
})();
