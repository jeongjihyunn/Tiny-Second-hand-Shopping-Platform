import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template

from config import config_by_name
from app.extensions import db, login_manager, csrf, socketio, limiter


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    # Pinned to Werkzeug's built-in "threading" mode so `pip install -r
    # requirements.txt` stays portable (no eventlet/gevent <-> system
    # OpenSSL version conflicts). Fine for this project's scale; swap to
    # async_mode="eventlet" (pip install eventlet) for production-grade
    # websocket concurrency.
    socketio.init_app(app, async_mode="threading", cors_allowed_origins="*")

    _register_security_headers(app)
    _register_error_handlers(app)
    _register_logging(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.auth.routes import auth_bp
    from app.products.routes import products_bp
    from app.chat.routes import chat_bp
    from app.reports.routes import reports_bp
    from app.wallet.routes import wallet_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(admin_bp)

    # SocketIO event handlers register themselves on import.
    from app.chat import events  # noqa: F401

    with app.app_context():
        db.create_all()

    return app


def _register_security_headers(app):
    @app.after_request
    def set_secure_headers(response):
        # Defense-in-depth HTTP headers (belt-and-braces alongside
        # Flask-WTF's CSRF protection and Jinja2 autoescaping).
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"          # clickjacking
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # Fairly strict CSP: only same-origin scripts/styles, no inline JS.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "script-src 'self' https://cdn.socket.io; "
            "style-src 'self' 'unsafe-inline'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        )
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


def _register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(e):
        # Never leak stack traces / internals to the client.
        app.logger.exception("Unhandled server error")
        return render_template("errors/500.html"), 500


def _register_logging(app):
    if app.debug:
        return
    os.makedirs(os.path.join(app.instance_path, "logs"), exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(app.instance_path, "logs", "app.log"), maxBytes=1_000_000, backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(remote_addr)s] %(message)s"
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
