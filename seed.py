"""Optional convenience script: creates an initial admin account for local
testing/demo. Run with `python seed.py` after `flask db` tables exist
(they are auto-created by create_app() on first run).

SECURITY NOTE: this is a *development* convenience only. The password below
is intentionally simple and printed to stdout - never use this script, or
this password, against a real deployment.
"""
from app import create_app
from app.extensions import db
from app.models import User, UserStatus

app = create_app("development")

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", is_admin=True, balance=1_000_000, status=UserStatus.ACTIVE)
        admin.set_password("ChangeMe123!")
        db.session.add(admin)
        db.session.commit()
        print("Created admin / ChangeMe123!  (change this password immediately)")
    else:
        print("admin user already exists")
