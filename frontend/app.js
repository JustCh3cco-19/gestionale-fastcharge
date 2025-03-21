// URL base per le API del backend
const API_BASE_URL = "http://localhost:5000/api";

// --- LOGIN (index.html) ---
if (document.getElementById('form-login')) {
  document.getElementById('form-login').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    const messageDiv = document.getElementById('message');
    if (response.ok) {
      localStorage.setItem('token', data.token);
      window.location.href = "inventory.html";
    } else {
      messageDiv.textContent = data.message;
    }
  });
}

// --- REGISTRAZIONE (register.html) ---
if (document.getElementById('form-register')) {
  document.getElementById('form-register').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = data.message;
  });
}

// --- Toggle del filtro in inventory.html ---
if (document.getElementById('toggle-filter')) {
  document.getElementById('toggle-filter').addEventListener('click', function() {
    const filterContainer = document.getElementById('filter-container');
    if (filterContainer.style.display === "none") {
      filterContainer.style.display = "block";
      this.textContent = "Nascondi Filtri";
    } else {
      filterContainer.style.display = "none";
      this.textContent = "Mostra Filtri";
    }
  });
}

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
    locItem.textContent = locationName;

    const articleList = document.createElement("ul");
    groups[locationName].forEach(article => {
      const articleLi = document.createElement("li");
      articleLi.textContent = `${article.codice_articolo} - ${article.descrizione || ""}`;
      articleList.appendChild(articleLi);
    });

    locItem.appendChild(articleList);
    locItem.addEventListener("click", function(e) {
      e.stopPropagation();
      this.classList.toggle("expanded");
    });
    root.appendChild(locItem);
  }
}

// --- Gestione della vista tabellare (inventory.html) ---
if (document.getElementById('inventory-table')) {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = "index.html";
  }

  async function fetchInventory(queryParams = "") {
    const response = await fetch(`${API_BASE_URL}/inventory${queryParams}`, {
      headers: { "Authorization": "Bearer " + token }
    });
    const items = await response.json();
    const tbody = document.querySelector("#inventory-table tbody");
    tbody.innerHTML = "";

    items.forEach(item => {
      let fotoHTML = "Nessun file";
      if (item.foto) {
        if (item.foto.toLowerCase().endsWith('.pdf')) {
          fotoHTML = `<a class="btn" href="http://localhost:5000/uploads/${item.foto}" target="_blank">Visualizza PDF</a>`;
        } else {
          fotoHTML = `<a class="btn" href="http://localhost:5000/uploads/${item.foto}" target="_blank">Visualizza Immagine</a>`;
        }
      }

      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${item.codice_articolo}</td>
        <td>${item.descrizione || ""}</td>
        <td>${item.unita_misura || ""}</td>
        <td>${item.quantita}</td>
        <td>${item.locazione || ""}</td>
        <td>${fotoHTML}</td>
        <td>${item.data_ingresso || ""}</td>
        <td>${item.created_by || ""}</td>
        <td>${item.modified_by || ""}</td>
        <td>
          <a href="edit_item.html?id=${item.id}" class="btn">Modifica</a>
          <button class="btn btn-danger" onclick="deleteItem(${item.id})">Elimina</button>
        </td>
      `;
      tbody.appendChild(row);
    });
  }

  async function deleteItem(itemId) {
    if (confirm("Sei sicuro di voler eliminare questo articolo?")) {
      const response = await fetch(`${API_BASE_URL}/inventory/${itemId}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
      });
      const data = await response.json();
      alert(data.message);
      fetchInventory();
    }
  }
  window.deleteItem = deleteItem;

  if (document.getElementById('filter-form')) {
    document.getElementById('filter-form').addEventListener('submit', function(e) {
      e.preventDefault();
      const codice = document.getElementById('filter-codice').value;
      const descrizione = document.getElementById('filter-descrizione').value;
      const locazione = document.getElementById('filter-locazione').value;
      let queryParams = "?";
      if (codice) queryParams += "codice_articolo=" + encodeURIComponent(codice) + "&";
      if (descrizione) queryParams += "descrizione=" + encodeURIComponent(descrizione) + "&";
      if (locazione) queryParams += "locazione=" + encodeURIComponent(locazione);
      fetchInventory(queryParams);
    });
  }

  fetchInventory();
  document.getElementById('logout').addEventListener('click', function() {
    localStorage.removeItem('token');
    window.location.href = "index.html";
  });
}

// --- Gestione della vista cartella (folder_view.html) ---
if (document.getElementById('tree-view-root')) {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = "index.html";
  }
  async function fetchInventoryForTree() {
    const response = await fetch(`${API_BASE_URL}/inventory`, {
      headers: { "Authorization": "Bearer " + token }
    });
    const items = await response.json();
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
    const response = await fetch(`${API_BASE_URL}/inventory/export`, {
      headers: { "Authorization": "Bearer " + token }
    });
    if (!response.ok) {
      const errorText = await response.text();
      alert("Errore durante l'export: " + errorText);
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
    formData.append("data_ingresso", document.getElementById('data_ingresso').value);
    formData.append("carico", document.getElementById('carico').value);
    formData.append("scarico", document.getElementById('scarico').value);
    
    const response = await fetch(`${API_BASE_URL}/inventory`, {
      method: "POST",
      headers: { "Authorization": "Bearer " + token },
      body: formData
    });
    const data = await response.json();
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = data.message;
    if (response.ok) {
      document.getElementById('form-add-item').reset();
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
    document.getElementById('message').textContent = "ID articolo non specificato";
  } else {
    fetch(`${API_BASE_URL}/inventory/${itemId}`, {
      headers: { "Authorization": "Bearer " + token }
    })
    .then(response => response.json())
    .then(data => {
      if (data.message) {
        document.getElementById('message').textContent = data.message;
      } else {
        document.getElementById('codice_articolo').value = data.codice_articolo || "";
        document.getElementById('descrizione').value = data.descrizione || "";
        document.getElementById('unita_misura').value = data.unita_misura || "";
        document.getElementById('locazione').value = data.locazione || "";
        document.getElementById('data_ingresso').value = data.data_ingresso || "";
      }
    })
    .catch(error => {
      document.getElementById('message').textContent = "Errore nel recupero dei dati";
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
    formData.append("data_ingresso", document.getElementById('data_ingresso').value);
    formData.append("carico", document.getElementById('carico').value);
    formData.append("scarico", document.getElementById('scarico').value);
    
    const response = await fetch(`${API_BASE_URL}/inventory/${itemId}`, {
      method: "PUT",
      headers: { "Authorization": "Bearer " + token },
      body: formData
    });
    const data = await response.json();
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = data.message;
    if (response.ok) {
      setTimeout(() => {
        window.location.href = "inventory.html";
      }, 1500);
    }
  });
}
