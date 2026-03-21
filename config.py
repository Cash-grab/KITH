import os
from pathlib import Path

from dotenv import load_dotenv

# load .env in repo root by default (or override with environment variables)
base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / '.env')


class Config:
    # use env values when available (for Docker and production)
    SECRET_KEY = os.getenv('SECRET_KEY') or 'hard-to-guess-string'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True

    DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
    if DATABASE_URL:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(DATABASE_URL)
        if parsed.scheme in ('postgresql', 'postgres') and (parsed.path == '' or parsed.path == '/'):
            parsed = parsed._replace(path='/kith_db')
            DATABASE_URL = urlunparse(parsed)

    # runtime database path for sqlite (or override with DATABASE_URL)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or f"sqlite:///{base_dir / 'data.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATABASE_PATH = os.getenv('DATABASE_PATH', str(base_dir / 'data.db'))

