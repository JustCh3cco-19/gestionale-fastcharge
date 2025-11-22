function resolveApiBaseUrl() {
  const override = window.API_BASE_URL || window.__API_BASE_URL__;
  if (override) return override.replace(/\/+$/, '');

  const { origin, protocol, hostname, port } = window.location;
  if (protocol === 'file:') {
    return 'http://localhost:5000/api';
  }

  const baseOrigin = port === '8080'
    ? `${protocol}//${hostname}:5000`
    : origin;

  return `${baseOrigin.replace(/\/$/, '')}/api`;
}

// URL base per le API del backend
const API_BASE_URL = resolveApiBaseUrl();

const POPUP_VISIBLE_CLASS = 'visible';
let popupOverlay = null;
let popupMessageEl = null;
let popupTimeoutId = null;

async function safeJson(response) {
  try {
    return await response.json();
  } catch (error) {
    return {};
  }
}

function ensurePopupElements() {
  if (popupOverlay) return;

  popupOverlay = document.createElement('div');
  popupOverlay.id = 'popup-overlay';
  popupOverlay.className = 'popup-overlay';
  popupOverlay.innerHTML = `
    <div class="popup">
      <div class="popup__icon" aria-hidden="true"></div>
      <p class="popup__message"></p>
      <button type="button" class="popup__close">Chiudi</button>
    </div>
  `;
  popupMessageEl = popupOverlay.querySelector('.popup__message');
  const closeButton = popupOverlay.querySelector('.popup__close');

  popupOverlay.addEventListener('click', (event) => {
    if (event.target === popupOverlay) {
      hidePopup();
    }
  });
  closeButton.addEventListener('click', hidePopup);

  document.body.appendChild(popupOverlay);
}

function hidePopup() {
  if (!popupOverlay) return;
  popupOverlay.classList.remove(POPUP_VISIBLE_CLASS, 'success', 'error', 'info');
  document.body.classList.remove('popup-open');
  if (popupTimeoutId) {
    clearTimeout(popupTimeoutId);
    popupTimeoutId = null;
  }
}

function showPopup(message, type = 'info', autoClose = true) {
  ensurePopupElements();
  popupOverlay.classList.remove('success', 'error', 'info');
  popupOverlay.classList.add(type, POPUP_VISIBLE_CLASS);
  popupMessageEl.textContent = message;
  document.body.classList.add('popup-open');

  if (popupTimeoutId) {
    clearTimeout(popupTimeoutId);
    popupTimeoutId = null;
  }

  if (autoClose && type === 'success') {
    popupTimeoutId = setTimeout(hidePopup, 2000);
  }
}

window.hidePopup = hidePopup;
window.showPopup = showPopup;

function forceLogoutAndRedirect(message) {
  localStorage.removeItem('token');
  showPopup(message || 'Sessione scaduta. Effettua nuovamente il login.', 'error', false);
  setTimeout(() => {
    window.location.href = 'index.html';
  }, 1200);
}

function isValidUsername(username) {
  return /^[A-Za-z0-9_.-]{3,64}$/.test(username);
}

function isPasswordStrong(password) {
  return password.length >= 8 && /[A-Z]/.test(password) && /[a-z]/.test(password) && /[0-9]/.test(password);
}

function formatNumber(value) {
  const formatter = new Intl.NumberFormat('it-IT');
  return formatter.format(Number(value) || 0);
}

function parseDateParts(value) {
  if (!value) return null;
  const trimmed = String(value).trim();
  const ddmmyyyy = /^(\d{2})[\/\-](\d{2})[\/\-](\d{4})$/;
  const yyyymmdd = /^(\d{4})[\/\-](\d{2})[\/\-](\d{2})$/;
  let match = trimmed.match(ddmmyyyy);
  if (match) {
    const [, dd, mm, yyyy] = match;
    return { day: dd, month: mm, year: yyyy };
  }
  match = trimmed.match(yyyymmdd);
  if (match) {
    const [, yyyy, mm, dd] = match;
    return { day: dd, month: mm, year: yyyy };
  }
  return null;
}

function toDdMmYyyy(parts) {
  if (!parts) return '';
  const { day, month, year } = parts;
  return `${day.padStart(2, '0')}/${month.padStart(2, '0')}/${year}`;
}

function formatDateForDisplay(value) {
  const parts = parseDateParts(value);
  return parts ? toDdMmYyyy(parts) : '';
}

function toBackendDate(value) {
  const parts = parseDateParts(value);
  if (parts) return toDdMmYyyy(parts);
  // fallback: try Date parsing
  const date = new Date(value);
  if (!Number.isNaN(date.getTime())) {
    const dd = String(date.getDate()).padStart(2, '0');
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const yyyy = String(date.getFullYear());
    return `${dd}/${mm}/${yyyy}`;
  }
  return '';
}

function toInputDateValue(value) {
  const parts = parseDateParts(value);
  if (!parts) return '';
  const { day, month, year } = parts;
  return `${day.padStart(2, '0')}/${month.padStart(2, '0')}/${year}`;
}

function updateInventoryStats(items) {
  const totalItemsEl = document.getElementById('stat-items');
  const totalQuantityEl = document.getElementById('stat-quantity');
  const locationsEl = document.getElementById('stat-locations');
  const updatedEl = document.getElementById('stat-updated');

  if (!totalItemsEl || !totalQuantityEl || !locationsEl || !updatedEl) {
    return;
  }

  const totalItems = items.length;
  const totalQuantity = items.reduce((acc, item) => acc + (item.quantita || 0), 0);
  const uniqueLocations = new Set(items.filter((item) => item.locazione).map((item) => item.locazione.trim()));

  totalItemsEl.textContent = formatNumber(totalItems);
  totalQuantityEl.textContent = formatNumber(totalQuantity);
  locationsEl.textContent = formatNumber(uniqueLocations.size);
  updatedEl.textContent = new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
}

async function openAttachmentFile(fileToken, suggestedName, kind) {
  const token = localStorage.getItem('token');
  if (!token) {
    showPopup('Sessione scaduta. Effettua nuovamente il login.', 'error', false);
    window.location.href = 'index.html';
    return;
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/files/${fileToken}`, {
      headers: { Authorization: 'Bearer ' + token }
    });
  } catch (error) {
    console.error(error);
    forceLogoutAndRedirect('Sessione scaduta o server offline. Accedi di nuovo.');
    return;
  }

  if (!response.ok) {
    const data = await safeJson(response);
    showPopup(data.message || 'File non disponibile', 'error', false);
    return;
  }

  const blob = await response.blob();
  const contentType = response.headers.get('Content-Type') || '';
  const url = window.URL.createObjectURL(blob);
  const previewable = contentType.startsWith('image/') || contentType === 'application/pdf';

  const filename = suggestedName || `allegato.${kind === 'pdf' ? 'pdf' : kind === 'image' ? 'png' : 'bin'}`;

  if (previewable) {
    const previewWindow = window.open(url, '_blank');
    if (!previewWindow) {
      triggerDownload(url, filename);
    } else {
      setTimeout(() => window.URL.revokeObjectURL(url), 4000);
    }
  } else {
    triggerDownload(url, filename);
  }
}

function triggerDownload(url, filename) {
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => window.URL.revokeObjectURL(url), 1500);
}

// --- LOGIN (index.html) ---
if (document.getElementById('form-login')) {
  document.getElementById('form-login').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      const data = await safeJson(response);
      if (response.ok) {
        localStorage.setItem('token', data.token);
        window.location.href = "inventory.html";
      } else {
        const messageDiv = document.getElementById('message');
        if (messageDiv) messageDiv.textContent = '';
        showPopup(data.message || 'Credenziali non valide', 'error', false);
      }
    } catch (error) {
      console.error(error);
      showPopup('Impossibile contattare il server. Riprova più tardi.', 'error', false);
    }
  });
}

// --- REGISTRAZIONE (register.html) ---
if (document.getElementById('form-register')) {
  const registerForm = document.getElementById('form-register');
  const usernameInput = document.getElementById('register-username');
  const passwordInput = document.getElementById('register-password');
  const confirmInput = document.getElementById('register-confirm-password');
  const usernameFeedbackEl = document.getElementById('username-feedback');
  const passwordFeedbackEl = document.getElementById('password-feedback');
  const passwordMatchEl = document.getElementById('password-match-feedback');
  let usernameCheckTimeout = null;

  const setHint = (el, message, isOk) => {
    if (!el) return;
    el.textContent = message || '';
    el.classList.remove('hint-ok', 'hint-error');
    if (!message) return;
    el.classList.add(isOk ? 'hint-ok' : 'hint-error');
  };

  const refreshPasswordHints = () => {
    const pwd = passwordInput ? passwordInput.value : '';
    const confirm = confirmInput ? confirmInput.value : '';

    if (!pwd) {
      setHint(passwordFeedbackEl, '', false);
    } else if (isPasswordStrong(pwd)) {
      setHint(passwordFeedbackEl, 'Password valida', true);
    } else {
      setHint(passwordFeedbackEl, 'Serve almeno 1 maiuscola, 1 minuscola e 1 numero (min 8 caratteri)', false);
    }

    if (!confirm) {
      setHint(passwordMatchEl, '', false);
    } else if (pwd === confirm) {
      setHint(passwordMatchEl, 'Le password coincidono', true);
    } else {
      setHint(passwordMatchEl, 'Le password non coincidono', false);
    }
  };

  passwordInput?.addEventListener('input', refreshPasswordHints);
  confirmInput?.addEventListener('input', refreshPasswordHints);
  refreshPasswordHints();

  const checkUsernameAvailability = async () => {
    if (!usernameInput) return;
    const username = usernameInput.value.trim();
    if (!username) {
      setHint(usernameFeedbackEl, '', false);
      return;
    }
    if (!isValidUsername(username)) {
      setHint(usernameFeedbackEl, 'Username non valido', false);
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/username-available?username=${encodeURIComponent(username)}`);
      const data = await safeJson(response);
      if (!response.ok) {
        setHint(usernameFeedbackEl, data.message || 'Impossibile verificare', false);
        return;
      }
      if (data.available) {
        setHint(usernameFeedbackEl, 'Username disponibile', true);
      } else {
        setHint(usernameFeedbackEl, 'Username già in uso', false);
      }
    } catch (error) {
      console.error(error);
      setHint(usernameFeedbackEl, 'Impossibile verificare', false);
    }
  };

  usernameInput?.addEventListener('input', () => {
    if (usernameCheckTimeout) clearTimeout(usernameCheckTimeout);
    usernameCheckTimeout = setTimeout(checkUsernameAvailability, 450);
  });
  usernameInput?.addEventListener('blur', () => {
    if (usernameCheckTimeout) clearTimeout(usernameCheckTimeout);
    checkUsernameAvailability();
  });

  registerForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;

    if (!isValidUsername(username)) {
      showPopup('Username non valido. Usa 3-64 caratteri alfanumerici, ".", "-" o "_".', 'error', false);
      return;
    }
    if (!isPasswordStrong(password)) {
      showPopup('Password troppo debole. Usa almeno 8 caratteri con maiuscole, minuscole e numeri.', 'error', false);
      return;
    }
    if (password !== confirmPassword) {
      showPopup('Le password non coincidono.', 'error', false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, confirm_password: confirmPassword })
      });
      const data = await safeJson(response);
      if (response.ok) {
        showPopup(data.message || 'Registrazione completata', 'success');
        document.getElementById('form-register').reset();
        setTimeout(() => {
          window.location.href = "index.html";
        }, 2200);
      } else {
        showPopup(data.message || 'Registrazione non riuscita', 'error', false);
      }
    } catch (error) {
      console.error(error);
      showPopup('Impossibile contattare il server. Riprova più tardi.', 'error', false);
    }
  });
}

// --- RESET PASSWORD (reset_password.html) ---
if (document.getElementById('form-reset')) {
  document.getElementById('form-reset').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('reset-username').value;
    const newPassword = document.getElementById('reset-password').value;
    const confirmPassword = document.getElementById('reset-confirm-password').value;

    if (!isValidUsername(username)) {
      showPopup('Username non valido. Usa 3-64 caratteri alfanumerici, ".", "-" o "_".', 'error', false);
      return;
    }
    if (!isPasswordStrong(newPassword)) {
      showPopup('Password troppo debole. Usa almeno 8 caratteri con maiuscole, minuscole e numeri.', 'error', false);
      return;
    }
    if (newPassword !== confirmPassword) {
      showPopup('Le password non coincidono.', 'error', false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      });
      const data = await safeJson(response);
      if (response.ok) {
        showPopup(data.message || 'Password reimpostata', 'success');
        document.getElementById('form-reset').reset();
        setTimeout(() => {
          window.location.href = "index.html";
        }, 2000);
      } else {
        showPopup(data.message || 'Impossibile reimpostare la password', 'error', false);
      }
    } catch (error) {
      console.error(error);
      showPopup('Impossibile contattare il server. Riprova più tardi.', 'error', false);
    }
  });
}

// --- Toggle del filtro in inventory.html ---
(function initFilterToggle() {
  const toggleButton = document.getElementById('toggle-filter');
  const filterPanel = document.getElementById('filter-container');
  if (!toggleButton || !filterPanel) return;
  filterPanel.classList.remove('is-open');
  toggleButton.addEventListener('click', function() {
    filterPanel.classList.toggle('is-open');
    const expanded = filterPanel.classList.contains('is-open');
    this.textContent = expanded ? 'Nascondi filtri' : 'Mostra filtri';
    this.setAttribute('aria-expanded', expanded ? 'true' : 'false');
  });
})();

// --- Funzione per costruire la vista cartella (tree view) ---
function buildTreeView(items) {
  // Raggruppa gli articoli per locazione
  const groups = {};
  items.forEach(item => {
    const location = item.locazione || "Senza locazione";
    if (!groups[location]) {
      groups[location] = [];
    }
    groups[location].push(item);
  });

  const root = document.getElementById("tree-view-root");
  if (!root) return;
  root.innerHTML = "";

  // Crea un <li> per ogni gruppo di locazione
  for (const locationName in groups) {
    const locItem = document.createElement("li");

    const header = document.createElement('div');
    header.className = 'tree-location';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.gap = '8px';

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.textContent = '▶';
    toggle.className = 'btn btn-ghost btn-small';
    toggle.style.padding = '4px 10px';
    toggle.style.fontSize = '12px';

    const title = document.createElement('span');
    title.textContent = locationName;
    title.style.flex = '1';

    const qrButton = document.createElement('button');
    qrButton.type = 'button';
    qrButton.className = 'btn btn-secondary btn-small';
    qrButton.textContent = 'QR area';
    qrButton.addEventListener('click', (event) => {
      event.stopPropagation();
      generateAreaQr(locationName);
    });

    header.appendChild(toggle);
    header.appendChild(title);
    header.appendChild(qrButton);
    locItem.appendChild(header);

    const articleList = document.createElement("ul");
    groups[locationName].forEach(article => {
      const articleLi = document.createElement("li");
      articleLi.textContent = `${article.codice_articolo} - ${article.descrizione || ""}`;
      articleList.appendChild(articleLi);
    });

    locItem.appendChild(articleList);
    locItem.addEventListener("click", function(e) {
      if (e.target === qrButton) return;
      e.stopPropagation();
      this.classList.toggle("expanded");
      toggle.textContent = this.classList.contains('expanded') ? '▼' : '▶';
    });
    root.appendChild(locItem);
  }
}

function generateAreaQr(locationName) {
  const baseUrl = `${window.location.origin}/inventory.html?locazione=${encodeURIComponent(locationName)}`;
  if (typeof qrcode === 'undefined') {
    showPopup('Generatore QR non disponibile offline.', 'error', false);
    return;
  }
  try {
    const qr = qrcode(0, 'M');
    qr.addData(baseUrl);
    qr.make();
    const dataUrl = qr.createDataURL(6, 2);
    const qrWindow = window.open('', '_blank');
    if (!qrWindow) {
      showPopup('Impossibile aprire il QR. Controlla il blocco popup.', 'error', false);
      return;
    }
    qrWindow.document.write(`<title>QR ${locationName}</title><img alt="QR ${locationName}" src="${dataUrl}" /><p>${locationName}</p><p style="font-size:12px;">Link: ${baseUrl}</p>`);
    qrWindow.document.close();
  } catch (error) {
    console.error(error);
    showPopup('Impossibile generare il QR in locale.', 'error', false);
  }
}

// --- Gestione della vista tabellare (inventory.html) ---
if (document.getElementById('inventory-table')) {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = 'index.html';
  }

  const inventoryTable = document.getElementById('inventory-table');
  const inventoryBody = inventoryTable.querySelector('tbody');
  const urlParams = new URLSearchParams(window.location.search);

  inventoryBody.addEventListener('click', (event) => {
    const attachmentTrigger = event.target.closest('[data-action="open-attachment"]');
    if (attachmentTrigger) {
      event.preventDefault();
      openAttachmentFile(
        attachmentTrigger.dataset.token,
        attachmentTrigger.dataset.filename,
        attachmentTrigger.dataset.kind
      );
      return;
    }
  });

  async function fetchInventory(queryParams = '') {
    let response;
    try {
      response = await fetch(`${API_BASE_URL}/inventory${queryParams}`, {
        headers: { Authorization: 'Bearer ' + token }
      });
    } catch (error) {
      console.error(error);
      forceLogoutAndRedirect('Sessione scaduta o server non raggiungibile. Effettua di nuovo il login.');
      return;
    }
    if (!response.ok) {
      if (response.status === 401) {
        showPopup('Sessione scaduta, effettua di nuovo il login.', 'error', false);
        localStorage.removeItem('token');
        window.location.href = 'index.html';
        return;
      }
      const errorData = await safeJson(response);
      showPopup(errorData.message || "Errore nel caricamento dell'inventario", 'error', false);
      return;
    }
    const items = await safeJson(response);
    renderInventoryRows(items);
    updateInventoryStats(items);
  }

  function createAttachmentButton(attachment) {
    const button = document.createElement('button');
    button.className = 'btn btn-ghost btn-small';
    button.type = 'button';
    button.dataset.action = 'open-attachment';
    button.dataset.token = attachment.token;
    button.dataset.filename = attachment.suggested_filename || '';
    button.dataset.kind = attachment.kind || 'file';
    let label = 'Apri file';
    if (attachment.kind === 'pdf') {
      label = 'Apri PDF';
    } else if (attachment.kind === 'image') {
      label = 'Apri immagine';
    }
    button.textContent = label;
    return button;
  }

  function renderInventoryRows(items) {
    inventoryBody.innerHTML = '';
    if (!items.length) {
      const emptyRow = document.createElement('tr');
      const emptyCell = document.createElement('td');
      emptyCell.colSpan = 10;
      emptyCell.className = 'table-empty';
      emptyCell.textContent = 'Nessun articolo trovato';
      emptyRow.appendChild(emptyCell);
      inventoryBody.appendChild(emptyRow);
      return;
    }

    items.forEach((item) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${item.codice_articolo || ''}</td>
        <td>${item.descrizione || ''}</td>
        <td>${item.unita_misura || ''}</td>
        <td>${item.quantita || 0}</td>
        <td>${item.locazione || ''}</td>
        <td class="cell-attachment"></td>
        <td>${formatDateForDisplay(item.data_ingresso)}</td>
        <td>${item.created_by || ''}</td>
        <td>${item.modified_by || ''}</td>
        <td class="cell-actions"></td>
      `;

      const attachmentCell = row.querySelector('.cell-attachment');
      if (item.attachment && item.attachment.token) {
        attachmentCell.appendChild(createAttachmentButton(item.attachment));
      } else {
        attachmentCell.textContent = 'Nessun file';
      }

      const actionsCell = row.querySelector('.cell-actions');
      const editLink = document.createElement('a');
      editLink.className = 'btn btn-secondary btn-small';
      editLink.href = `edit_item.html?id=${item.id}`;
      editLink.textContent = 'Modifica';

      const deleteButton = document.createElement('button');
      deleteButton.type = 'button';
      deleteButton.className = 'btn btn-danger btn-small';
      deleteButton.textContent = 'Elimina';
      deleteButton.addEventListener('click', () => deleteItem(item.id));

      actionsCell.appendChild(editLink);
      actionsCell.appendChild(deleteButton);

      inventoryBody.appendChild(row);
    });
  }

  async function deleteItem(itemId) {
    if (!confirm('Sei sicuro di voler eliminare questo articolo?')) {
      return;
    }
    let response;
    try {
      response = await fetch(`${API_BASE_URL}/inventory/${itemId}`, {
        method: 'DELETE',
        headers: { Authorization: 'Bearer ' + token }
      });
    } catch (error) {
      console.error(error);
      forceLogoutAndRedirect('Sessione scaduta o server non raggiungibile. Effettua di nuovo il login.');
      return;
    }
    const data = await safeJson(response);
    if (response.ok) {
      showPopup(data.message || 'Articolo eliminato', 'success');
      fetchInventory();
    } else {
      showPopup(data.message || "Impossibile eliminare l'articolo", 'error', false);
    }
  }

  const filterForm = document.getElementById('filter-form');
  if (filterForm) {
    filterForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const codice = document.getElementById('filter-codice').value.trim();
      const descrizione = document.getElementById('filter-descrizione').value.trim();
      const locazione = document.getElementById('filter-locazione').value.trim();
      const params = new URLSearchParams();
      if (codice) params.append('codice_articolo', codice);
      if (descrizione) params.append('descrizione', descrizione);
      if (locazione) params.append('locazione', locazione);
      const query = params.toString();
      fetchInventory(query ? `?${query}` : '');
    });

    // Prefill from URL and auto-apply if present
    const urlCodice = urlParams.get('codice_articolo');
    const urlDescrizione = urlParams.get('descrizione');
    const urlLocazione = urlParams.get('locazione');
    if (urlCodice) document.getElementById('filter-codice').value = urlCodice;
    if (urlDescrizione) document.getElementById('filter-descrizione').value = urlDescrizione;
    if (urlLocazione) document.getElementById('filter-locazione').value = urlLocazione;
    if (urlCodice || urlDescrizione || urlLocazione) {
      const params = new URLSearchParams();
      if (urlCodice) params.append('codice_articolo', urlCodice);
      if (urlDescrizione) params.append('descrizione', urlDescrizione);
      if (urlLocazione) params.append('locazione', urlLocazione);
      const query = params.toString();
      fetchInventory(`?${query}`);
    }
  }

  if (!urlParams.size) {
    fetchInventory();
  }
  document.getElementById('logout').addEventListener('click', function() {
    localStorage.removeItem('token');
    window.location.href = 'index.html';
  });
}

// --- Gestione della vista cartella (folder_view.html) ---
if (document.getElementById('tree-view-root')) {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = "index.html";
  }
  async function fetchInventoryForTree() {
    let response;
    try {
      response = await fetch(`${API_BASE_URL}/inventory`, {
        headers: { "Authorization": "Bearer " + token }
      });
    } catch (error) {
      console.error(error);
      forceLogoutAndRedirect('Sessione scaduta o server non raggiungibile. Effettua di nuovo il login.');
      return;
    }
    if (!response.ok) {
      if (response.status === 401) {
        showPopup('Sessione scaduta, effettua di nuovo il login.', 'error', false);
        localStorage.removeItem('token');
        window.location.href = "index.html";
        return;
      }
      const errorData = await safeJson(response);
      showPopup(errorData.message || 'Errore nel caricamento dell\'inventario', 'error', false);
      return;
    }
    const items = await safeJson(response);
    buildTreeView(items);
  }
  fetchInventoryForTree();
  document.getElementById('logout').addEventListener('click', function() {
    localStorage.removeItem('token');
    window.location.href = "index.html";
  });
}

// --- ESPORTA INVENTARIO ---
if (document.getElementById('export-btn')) {
  async function exportInventory() {
    const token = localStorage.getItem('token');
    let response;
    try {
      response = await fetch(`${API_BASE_URL}/inventory/export`, {
        headers: { "Authorization": "Bearer " + token }
      });
    } catch (error) {
      console.error(error);
      forceLogoutAndRedirect('Sessione scaduta o server non raggiungibile. Effettua di nuovo il login.');
      return;
    }
    if (!response.ok) {
      const errorText = await response.text();
      showPopup("Errore durante l'export: " + errorText, 'error', false);
      return;
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = "inventario.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
  }
  document.getElementById('export-btn').addEventListener('click', exportInventory);
}

// --- AGGIUNTA ARTICOLO (add_item.html) ---
if (document.getElementById('form-add-item')) {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = "index.html";
  }
  document.getElementById('form-add-item').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData();
    formData.append("codice_articolo", document.getElementById('codice_articolo').value);
    formData.append("descrizione", document.getElementById('descrizione').value);
    formData.append("unita_misura", document.getElementById('unita_misura').value);
    formData.append("locazione", document.getElementById('locazione').value);
    const fotoFile = document.getElementById('foto').files[0];
    if (fotoFile) {
      formData.append("foto", fotoFile);
    }
    const rawDate = document.getElementById('data_ingresso').value;
    const normalizedDate = toBackendDate(rawDate);
    if (!normalizedDate) {
      showPopup('Inserisci una data valida nel formato gg/mm/aaaa', 'error', false);
      return;
    }
    formData.append("data_ingresso", normalizedDate);
    formData.append("carico", document.getElementById('carico').value);
    formData.append("scarico", document.getElementById('scarico').value);
    
    let response;
    try {
      response = await fetch(`${API_BASE_URL}/inventory`, {
        method: "POST",
        headers: { "Authorization": "Bearer " + token },
        body: formData
      });
    } catch (error) {
      console.error(error);
      forceLogoutAndRedirect('Sessione scaduta o server non raggiungibile. Effettua di nuovo il login.');
      return;
    }
    const data = await safeJson(response);
    if (response.ok) {
      showPopup(data.message || 'Articolo aggiunto con successo', 'success');
      document.getElementById('form-add-item').reset();
    } else {
      showPopup(data.message || 'Errore durante l\'aggiunta dell\'articolo', 'error', false);
    }
  });
}

// --- MODIFICA ARTICOLO (edit_item.html) ---
if (document.getElementById('form-edit-item')) {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = "index.html";
  }
  const urlParams = new URLSearchParams(window.location.search);
  const itemId = urlParams.get('id');
  if (!itemId) {
    showPopup('ID articolo non specificato', 'error', false);
  } else {
    fetch(`${API_BASE_URL}/inventory/${itemId}`, {
      headers: { "Authorization": "Bearer " + token }
    })
    .then(response => response.json())
    .then(data => {
      if (data.message) {
        showPopup(data.message, 'error', false);
      } else {
        document.getElementById('codice_articolo').value = data.codice_articolo || "";
        document.getElementById('descrizione').value = data.descrizione || "";
        document.getElementById('unita_misura').value = data.unita_misura || "";
        document.getElementById('locazione').value = data.locazione || "";
        document.getElementById('data_ingresso').value = toInputDateValue(data.data_ingresso || "") || "";
      }
    })
    .catch(error => {
      console.error(error);
      forceLogoutAndRedirect('Sessione scaduta o server non raggiungibile. Effettua di nuovo il login.');
    });
  }
  document.getElementById('form-edit-item').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData();
    formData.append("codice_articolo", document.getElementById('codice_articolo').value);
    formData.append("descrizione", document.getElementById('descrizione').value);
    formData.append("unita_misura", document.getElementById('unita_misura').value);
    formData.append("locazione", document.getElementById('locazione').value);
    const fotoFile = document.getElementById('foto').files[0];
    if (fotoFile) {
      formData.append("foto", fotoFile);
    }
    const rawDate = document.getElementById('data_ingresso').value;
    const normalizedDate = toBackendDate(rawDate);
    if (!normalizedDate) {
      showPopup('Inserisci una data valida nel formato gg/mm/aaaa', 'error', false);
      return;
    }
    formData.append("data_ingresso", normalizedDate);
    formData.append("carico", document.getElementById('carico').value);
    formData.append("scarico", document.getElementById('scarico').value);
    
    let response;
    try {
      response = await fetch(`${API_BASE_URL}/inventory/${itemId}`, {
        method: "PUT",
        headers: { "Authorization": "Bearer " + token },
        body: formData
      });
    } catch (error) {
      console.error(error);
      forceLogoutAndRedirect('Sessione scaduta o server non raggiungibile. Effettua di nuovo il login.');
      return;
    }
    const data = await safeJson(response);
    if (response.ok) {
      showPopup(data.message || 'Articolo aggiornato con successo', 'success');
      setTimeout(() => {
        window.location.href = "inventory.html";
      }, 2200);
    } else {
      showPopup(data.message || 'Errore durante l\'aggiornamento dell\'articolo', 'error', false);
    }
  });
}
