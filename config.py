import os
import secrets
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY MUST come from the environment in real deployments.
    # We only fall back to a random throwaway key so `flask run` doesn't
    # crash on a fresh checkout; every restart would invalidate sessions,
    # which is a deliberate nudge to set a real SECRET_KEY in .env.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "instance", "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Session / cookie hardening ---
    SESSION_COOKIE_HTTPONLY = True          # JS (and thus XSS) cannot read the cookie
    SESSION_COOKIE_SAMESITE = "Lax"         # mitigates CSRF via cross-site navigation
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 2  # 2 hours idle logout
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # --- File upload hardening ---
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024    # 4 MB hard cap on any request body
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # --- App-specific business rules ---
    REPORT_THRESHOLD = int(os.environ.get("REPORT_THRESHOLD", 5))
    SIGNUP_BONUS_BALANCE = int(os.environ.get("SIGNUP_BONUS_BALANCE", 100000))

    WTF_CSRF_TIME_LIMIT = None  # tokens tied to session lifetime instead of a fixed timeout


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # allow plain HTTP on localhost


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True   # cookie only sent over HTTPS
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SESSION_COOKIE_SECURE = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
