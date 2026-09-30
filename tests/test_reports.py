from tests.conftest import login


def test_product_auto_blocked_after_threshold(client, app):
    from app.extensions import db
    from app.models import User, Product, ProductStatus

    with app.app_context():
        seller = User(username="seller_x", balance=0)
        seller.set_password("Passw0rd!")
        db.session.add(seller)
        db.session.commit()
        product = Product(title="의심상품", description="d", price=1000, seller_id=seller.id)
        db.session.add(product)
        db.session.commit()
        product_id = product.id

        reporters = []
        for i in range(app.config["REPORT_THRESHOLD"]):
            u = User(username=f"reporter{i}", balance=0)
            u.set_password("Passw0rd!")
            db.session.add(u)
            db.session.commit()
            reporters.append(u.username)

    for name in reporters:
        login(client, name, "Passw0rd!")
        client.post(f"/report/product/{product_id}", data={"reason": "가짜 상품인 것 같습니다"})
        client.get("/logout")

    with app.app_context():
        p = db.session.get(Product, product_id)
        assert p.status == ProductStatus.BLOCKED


def test_cannot_report_same_target_twice(client, make_user):
    seller_id = make_user(username="seller_y", balance=0)
    make_user(username="reporter_dup")

    login(client, "reporter_dup", "Passw0rd!")
    resp1 = client.post(f"/report/user/{seller_id}", data={"reason": "abc12345"}, follow_redirects=True)
    resp2 = client.post(f"/report/user/{seller_id}", data={"reason": "abc12345"}, follow_redirects=True)
    assert "이미 이 사용자를 신고" in resp2.get_data(as_text=True)
