# Gestionale FastCharge

> **Inventory management system with a Flask + PostgreSQL backend and a static HTML/CSS/JS frontend.**

## 📚 Quick Index
- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Preparing the `.env` Files](#preparing-the-env-files)
- [Running with Docker](#running-with-docker)
- [Installing Without Docker](#installing-without-docker)
- [Key Features](#key-features)
- [Database & Persistence](#database--persistence)
- [Operational Notes](#operational-notes)
- [Reference API](#reference-api)

---

## Overview

Gestionale FastCharge is a full-stack inventory platform that lets you track items, handle stock movements, attach files, export data, and audit user changes. The project ships with both containerised and bare-metal deployment options.

---

## Architecture

- 🖥️ **Frontend** – Static interface (HTML, CSS, vanilla JS) served by Nginx or any static web server.
- 🔙 **Backend** – Flask REST API with token authentication, SQLAlchemy, and PostgreSQL storage.
- 🐳 **Containerisation** – `docker-compose.yml` orchestrates frontend, backend, and database services.

---

## Project Structure

```
├── backend/
│   ├── app/                # Flask application package
│   │   ├── __init__.py     # Application factory & wiring
│   │   ├── auth/           # Login, logout, token management
│   │   └── inventory/      # Inventory routes & logic
│   ├── wsgi.py             # Entry point (used inside containers)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── uploads/            # User-uploaded files
├── frontend/
│   ├── src/                # Static pages, JS, CSS
│   │   ├── *.html
│   │   ├── app.js
│   │   └── style.css
│   ├── Dockerfile
│   └── build_image.sh      # Optional Docker builder helper
├── docker-compose.yml      # Multi-container orchestration
├── .env.example            # Shared environment variable template
├── build-docker-images.sh  # Build all project images
└── launch_system.sh        # One-shot startup script
```

---

## Preparing the `.env` Files

Keep secrets and credentials out of source control:

1. Copy the provided template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with secure values:
   - `BACKEND_SECRET_KEY` – long random string (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).
   - `POSTGRES_PASSWORD` – strong password for the database user.
   - Optional: adjust port mappings or the database connection string.
3. Never commit `.env`. The root `.gitignore` already keeps it private.

Docker Compose automatically loads the `.env` file and injects values into the containers.

---

## Running with Docker

> Requirements: Docker, Docker Compose, Bash

1. **Clone the repository**
   ```bash
   git clone https://github.com/JustCh3cco-19/gestionale-fastcharge.git
   cd gestionale-fastcharge
   ```
2. **Prepare the `.env` files** as described above.
3. **Build & start**
   ```bash
   docker-compose build
   docker-compose up
   ```
   The backend retries automatically until PostgreSQL is ready.
4. **Access the app**
   - Frontend: [http://localhost:${FRONTEND_PORT}](http://localhost:8080)
   - Backend API: [http://localhost:${BACKEND_PORT}/api](http://localhost:5000/api)
5. **Shutdown**
   ```bash
   docker-compose down
   ```
   Append `-v` to remove the `postgres-data` volume (this erases the database).

### Rebuilding Images

Use the helper script when you need a clean rebuild:
```bash
./build-docker-images.sh
docker-compose up --build
```

---

## Installing Without Docker

This mode is useful for environments where Docker is unavailable or for lightweight development.

### 1. Prerequisites

- Python 3.9+
- PostgreSQL 13+ (local or remote)
- Node/NPM **not required** (frontend is static)

### 2. Database Setup

```bash
psql -U postgres
CREATE DATABASE fastcharge;
CREATE USER fastcharge WITH PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE fastcharge TO fastcharge;
\q
```

### 3. Flask Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cat <<'EOF' > .env
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=postgresql+psycopg2://fastcharge:strong-password@localhost:5432/fastcharge
TOKEN_TTL_SECONDS=86400
DB_INIT_MAX_RETRIES=5
DB_INIT_RETRY_DELAY=1
EOF

export $(grep -v '^#' .env | xargs)  # or load variables with your preferred method
python -m app.wsgi  # starts the server on 0.0.0.0:5000
```

> Tip: if you prefer the Flask CLI, set `FLASK_APP=wsgi.py` and run `flask run --host=0.0.0.0 --port=5000`.

### 4. Static Frontend

You can open `frontend/src/index.html` directly or serve it through a tiny static server:

```bash
cd frontend/src
python3 -m http.server 8080
# or: npx serve
```

Ensure the backend API is reachable at `http://localhost:5000`. Update `API_BASE_URL` in `app.js` if you expose the backend elsewhere.

---

## Key Features

- Token-based authentication (register/login/logout) with strong password policy.
- Full inventory CRUD with integer-only stock movements and author/modifier tracking.
- Image/PDF uploads exposed through a dedicated download endpoint.
- Filtering by code, description, location, plus a tree-view grouped by location.
- Inventory CSV export.
- Responsive pop-up feedback for every significant frontend action.

---

## Database & Persistence

- PostgreSQL 14 managed by the `db` service (or manually when running bare metal).
- Connection string configurable through `DATABASE_URL`.
- Tables are created automatically at application startup.
- Persistent storage:
  - `postgres-data` Docker volume for the database.
  - `backend/uploads` bind mount for uploaded files.

---

## Operational Notes

- On Linux you may need `sudo` to run Docker commands.
- Item quantities are calculated as `carico - scarico` and only accept integers ≥ 0 to avoid rounding issues.
- Uploaded files are served from `http://localhost:${BACKEND_PORT}/uploads/<filename>`.
- Login tokens expire after 24 hours (configurable) and are stored in PostgreSQL.
- To completely reset the Docker environment: `docker-compose down -v && rm -rf backend/uploads/*` (beware: this wipes data).

---

## Reference API

- `POST /api/register` – register a new user (strong password + confirmation required)
- `POST /api/login` – obtain an auth token
- `POST /api/logout` – revoke the current token
- `GET /api/inventory` – list items; supports query-string filters
- `POST /api/inventory` – create a new item (multipart/form-data)
- `GET /api/inventory/<id>` – retrieve a single item
- `PUT /api/inventory/<id>` – update an item (JSON or multipart/form-data)
- `DELETE /api/inventory/<id>` – delete an item
- `GET /api/inventory/export` – download the inventory as CSV

Document any extensions by adding new sections to this wiki and linking them in the index above.
