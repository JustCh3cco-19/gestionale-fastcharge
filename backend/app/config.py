import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_URI = 'postgresql+psycopg2://fastcharge:fastcharge@db:5432/fastcharge'


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chiave_segreta')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', DEFAULT_DB_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}
    TOKEN_TTL_SECONDS = int(os.getenv('TOKEN_TTL_SECONDS', 60 * 60 * 24))
    DB_INIT_MAX_RETRIES = int(os.getenv('DB_INIT_MAX_RETRIES', 10))
    DB_INIT_RETRY_DELAY = float(os.getenv('DB_INIT_RETRY_DELAY', 2))
    FILE_TOKEN_TTL_SECONDS = int(os.getenv('FILE_TOKEN_TTL_SECONDS', 60 * 60))
