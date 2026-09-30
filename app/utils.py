import os
import uuid
from functools import wraps

import bleach
from flask import current_app, abort
from flask_login import current_user
from werkzeug.utils import secure_filename


def allowed_image(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_product_image(file_storage):
    """Persist an uploaded image safely.

    Security notes:
    - Extension is checked against an allow-list (not a deny-list).
    - The stored filename is a fresh random UUID, never the client-supplied
      name, so path traversal (`../../etc/passwd`) and overwrite attacks are
      impossible regardless of what the browser sends.
    - `secure_filename` is also applied defensively before we even look at
      the extension.
    - Files are written under app/static/uploads, a directory the app never
      executes code from (no .php/.py interpreters there).
    """
    if not file_storage or file_storage.filename == "":
        return None

    filename = secure_filename(file_storage.filename)
    if not allowed_image(filename):
        raise ValueError("허용되지 않는 파일 형식입니다. (png, jpg, jpeg, gif, webp만 가능)")

    ext = filename.rsplit(".", 1)[1].lower()
    new_name = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(current_app.config["UPLOAD_FOLDER"], new_name)
    file_storage.save(dest)
    return new_name


def clean_text(text: str) -> str:
    """Strip any HTML/JS from user-supplied free text before it is stored.

    Jinja2 autoescaping (default in Flask) already neutralizes XSS on output,
    but sanitizing on input too is defense-in-depth: it keeps stored data
    clean for any future consumer (API, export, admin tool) that might not
    autoescape.
    """
    if text is None:
        return ""
    return bleach.clean(text, tags=[], attributes={}, strip=True).strip()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped
