from tests.conftest import login


def test_register_and_login(client):
    resp = client.post("/register", data={
        "username": "bob01", "password": "Passw0rd!", "confirm": "Passw0rd!",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert "로그인" in resp.get_data(as_text=True)

    resp = login(client, "bob01", "Passw0rd!")
    assert resp.status_code == 200
    assert "환영합니다" in resp.get_data(as_text=True) or "bob01" in resp.get_data(as_text=True)


def test_login_wrong_password_generic_error(client, make_user):
    make_user(username="carol", password="Passw0rd!")
    resp = login(client, "carol", "wrongpass")
    assert "아이디 또는 비밀번호가 올바르지 않습니다" in resp.get_data(as_text=True)


def test_login_unknown_user_same_generic_error(client):
    resp = login(client, "nosuchuser", "whatever")
    assert "아이디 또는 비밀번호가 올바르지 않습니다" in resp.get_data(as_text=True)


def test_weak_password_rejected(client):
    resp = client.post("/register", data={
        "username": "dave01", "password": "aaaaaaaa", "confirm": "aaaaaaaa",
    })
    # only lowercase letters -> fails the character-class-mix check
    assert b"\xec\xa1\xb0\xed\x95\xa9" in resp.data or resp.status_code == 200


def test_duplicate_username_rejected(client, make_user):
    make_user(username="erin")
    resp = client.post("/register", data={
        "username": "erin", "password": "Passw0rd!", "confirm": "Passw0rd!",
    }, follow_redirects=True)
    assert "이미 사용 중인 아이디" in resp.get_data(as_text=True)


def test_dormant_user_cannot_login(client, make_user, app):
    from app.extensions import db
    from app.models import User, UserStatus

    uid = make_user(username="frank", password="Passw0rd!")
    with app.app_context():
        u = db.session.get(User, uid)
        u.status = UserStatus.DORMANT
        db.session.commit()

    resp = login(client, "frank", "Passw0rd!")
    assert "휴면" in resp.get_data(as_text=True)
