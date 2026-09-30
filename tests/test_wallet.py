from tests.conftest import login


def test_transfer_success(client, make_user, app):
    from app.extensions import db
    from app.models import User

    sender_id = make_user(username="payer", balance=1000)
    make_user(username="payee", balance=0)

    login(client, "payer", "Passw0rd!")
    resp = client.post("/wallet/transfer", data={
        "to_username": "payee", "amount": "400", "memo": "test",
    }, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        payer = User.query.filter_by(username="payer").first()
        payee = User.query.filter_by(username="payee").first()
        assert payer.balance == 600
        assert payee.balance == 400


def test_transfer_insufficient_balance_rejected(client, make_user):
    make_user(username="poor", balance=10)
    make_user(username="rich_target", balance=0)

    login(client, "poor", "Passw0rd!")
    resp = client.post("/wallet/transfer", data={
        "to_username": "rich_target", "amount": "9999", "memo": "",
    }, follow_redirects=True)
    assert "잔액이 부족" in resp.get_data(as_text=True)


def test_cannot_transfer_negative_amount(client, make_user):
    make_user(username="tricky", balance=1000)
    make_user(username="victim", balance=0)
    login(client, "tricky", "Passw0rd!")
    resp = client.post("/wallet/transfer", data={
        "to_username": "victim", "amount": "-500", "memo": "",
    })
    # WTForms NumberRange(min=1) rejects this before it ever touches balances
    assert resp.status_code == 200
