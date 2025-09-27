import time
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from sqlalchemy.exc import OperationalError

from .config import Config
from .extensions import db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    with app.app_context():
        from . import models  # noqa: F401

        _initialise_database(app)

    from .auth.routes import bp as auth_bp
    from .inventory.routes import bp as inventory_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(inventory_bp, url_prefix='/api')

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename: str):
        from flask import send_from_directory

        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app


def _initialise_database(app: Flask) -> None:
    max_attempts = app.config.get('DB_INIT_MAX_RETRIES', 1)
    delay_seconds = app.config.get('DB_INIT_RETRY_DELAY', 1)

    uploads_path = Path(app.config['UPLOAD_FOLDER'])

    for attempt in range(1, max_attempts + 1):
        try:
            db.create_all()
            uploads_path.mkdir(parents=True, exist_ok=True)
            return
        except OperationalError as exc:
            app.logger.warning(
                "Database connection failed (attempt %s/%s): %s",
                attempt,
                max_attempts,
                exc,
            )
            if attempt == max_attempts:
                raise
            time.sleep(delay_seconds)
