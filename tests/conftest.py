import pytest

from app import create_app
from app.extensions import db as _db
from app.models import User


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    def _make(username="alice", password="Passw0rd!", admin=False, balance=1000):
        with app.app_context():
            u = User(username=username, is_admin=admin, balance=balance)
            u.set_password(password)
            _db.session.add(u)
            _db.session.commit()
            return u.id
    return _make


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
