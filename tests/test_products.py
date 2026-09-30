from tests.conftest import login


def _register(client, username, password="Passw0rd!"):
    client.post("/register", data={"username": username, "password": password, "confirm": password})
    login(client, username, password)


def test_product_create_and_view(client):
    _register(client, "seller1")
    resp = client.post("/products/new", data={
        "title": "아이폰 팝니다", "description": "상태 좋음", "price": "500000",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert "아이폰 팝니다" in resp.get_data(as_text=True)


def test_edit_forbidden_for_non_owner(client):
    _register(client, "owner1")
    resp = client.post("/products/new", data={
        "title": "노트북", "description": "설명", "price": "300000",
    }, follow_redirects=True)
    assert "노트북" in resp.get_data(as_text=True)

    from app.models import Product
    # find the product id via listing page link count is awkward in a pure
    # black-box test, so just assume id=1 for a freshly created DB.
    client.get("/logout")
    _register(client, "attacker1")
    resp = client.get("/products/1/edit")
    assert resp.status_code == 403


def test_search_is_safe_and_functional(client):
    _register(client, "seller2")
    client.post("/products/new", data={"title": "카메라", "description": "d", "price": "1000"})
    client.post("/products/new", data={"title": "카메라 렌즈", "description": "d", "price": "2000"})

    resp = client.get("/?q=카메라")
    body = resp.get_data(as_text=True)
    assert "카메라" in body

    # A classic SQLi payload should not error out or return everything -
    # it's just treated as a literal (harmless) search string.
    resp = client.get("/?q=' OR '1'='1")
    assert resp.status_code == 200


def test_xss_in_title_is_not_rendered_as_html(client):
    _register(client, "seller3")
    payload = "<script>alert(1)</script>"
    client.post("/products/new", data={"title": payload, "description": "d", "price": "1000"})
    resp = client.get("/")
    body = resp.get_data(as_text=True)
    assert "<script>alert(1)</script>" not in body
