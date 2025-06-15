# Gestionale FastCharge

> **Inventory management system with full Docker support – Flask backend and JS/HTML frontend in separate containers.**

Gestionale FastCharge is a full-stack inventory management platform for tracking items, managing stock levels, uploading files, and exporting data. It supports user login/registration, authorization via token, and separate frontend/backend services using Docker and `docker-compose`.

---

## 🧱 Architecture

- 🖥️ **Frontend** (HTML, CSS, JS) served as a static web interface
- 🔙 **Backend** (Flask + SQLite) with REST API for inventory and auth
- 🐳 Dockerized frontend and backend, orchestrated via `docker-compose`

---

## 📁 Project Structure

```
├── backend/
│   ├── app.py              # Flask application
│   └── build_image.sh      # Docker image builder
├── frontend/
│   ├── index.html, *.html  # UI pages
│   ├── app.js              # JS logic
│   └── build_image.sh      # Docker image builder
├── docker-compose.yml      # Multi-container orchestration
├── build-docker-images.sh  # Script to build all Docker images
├── launch_system.sh        # Unified launcher script
└── uploads/                # Uploaded files (images, PDFs)
```

---

## 🚀 Quick Start

> 🐧 For Linux: requires `sudo`  
> 🍎 For macOS: `sudo` is **not** required

1. Clone the repository:
```bash
git clone https://github.com/JustCh3cco-19/gestionale-fastcharge.git
cd gestionale-fastcharge
```

2. Launch the entire system:
```bash
bash launch_system.sh
```

This script will:
- Build both frontend and backend images using `build-docker-images.sh`
- Start all containers via `docker-compose up`

3. Access the application:
- Frontend: [http://localhost:8080](http://localhost:8080)
- Backend API: [http://localhost:5000/api](http://localhost:5000/api)

---

## 🧪 Core Features

- Token-based authentication (login + register)
- Create, view, update, delete inventory entries
- Upload/view images or PDFs for each item
- CSV export of inventory
- Tree-view grouping by location

---

## 🛠️ Requirements

- Docker
- Docker Compose
- Bash

---

## 📌 Notes

- On Linux, container shutdown is handled via systemd (post-launch)
- Inventory quantity is calculated as `carico - scarico`
- Uploads are stored in `/uploads/` and accessible via API

---

## 📦 Example API endpoints

- `POST /api/login` – login and receive token
- `GET /api/inventory` – fetch all items (with filter support)
- `POST /api/inventory` – add new item (form-data)
- `PUT /api/inventory/<id>` – update item
- `DELETE /api/inventory/<id>` – delete item
