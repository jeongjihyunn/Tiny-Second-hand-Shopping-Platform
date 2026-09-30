import os
from app import create_app
from app.extensions import socketio

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    # Dev server (threading mode unless eventlet/gevent is installed).
    # Use a real WSGI/ASGI deployment (gunicorn + eventlet worker, etc.) for production.
    socketio.run(app, host="127.0.0.1", port=5000, debug=app.config.get("DEBUG", False))
