from __future__ import annotations

import os
import secrets
import sys
import threading
import time
import webbrowser
from pathlib import Path

from waitress import serve

from app import create_app

DEFAULT_PORT = 5000


def _resource_path(*parts: str) -> Path:
    """Restituisce un percorso valido sia in sviluppo che con PyInstaller."""
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    candidate = base.joinpath(*parts)
    if candidate.exists():
        return candidate
    # In sviluppo i file frontend vivono una directory sopra `backend/`.
    return base.parent.joinpath(*parts)


def _runtime_dir() -> Path:
    """Directory persistente usata per DB SQLite e upload."""
    if getattr(sys, 'frozen', False):
        base_dir = Path(os.environ.get('APPDATA', Path.home()))
        target = base_dir / 'GestionaleFastCharge'
    else:
        target = Path(__file__).resolve().parent / '.runtime'
    target.mkdir(parents=True, exist_ok=True)
    (target / 'uploads').mkdir(parents=True, exist_ok=True)
    return target


def _ensure_env(data_dir: Path) -> None:
    db_path = data_dir / 'fastcharge.db'
    uploads_dir = data_dir / 'uploads'

    os.environ.setdefault('DATABASE_URL', f"sqlite:///{db_path.as_posix()}")
    os.environ.setdefault('UPLOAD_FOLDER', str(uploads_dir))
    os.environ.setdefault('SECRET_KEY', secrets.token_hex(32))
    os.environ.setdefault('TOKEN_TTL_SECONDS', '86400')
    os.environ.setdefault('FILE_TOKEN_TTL_SECONDS', '3600')


def _auto_open_browser(port: int) -> None:
    time.sleep(2)
    try:
        webbrowser.open_new(f'http://127.0.0.1:{port}')
    except Exception:
        pass


def main() -> None:
    data_dir = _runtime_dir()
    _ensure_env(data_dir)

    frontend_root = _resource_path('frontend')
    app = create_app(frontend_root=frontend_root)

    port = int(os.environ.get('PORT', DEFAULT_PORT))
    threading.Thread(target=_auto_open_browser, args=(port,), daemon=True).start()

    serve(app, host='127.0.0.1', port=port)


if __name__ == '__main__':
    main()
