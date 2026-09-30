from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Product, ProductStatus
from app.products.forms import ProductForm, SearchForm
from app.utils import save_product_image, clean_text

products_bp = Blueprint("products", __name__)


def _escape_like(value: str) -> str:
    # Escape SQL LIKE wildcard characters so a search for "50%" or "a_b"
    # can't be abused to widen the match beyond the literal text typed.
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@products_bp.route("/")
def index():
    search_form = SearchForm(request.args, meta={"csrf": False})
    query = Product.query.filter_by(status=ProductStatus.ACTIVE)

    q = request.args.get("q", "").strip()
    if q:
        # Parameterized query via SQLAlchemy ORM -> no raw string
        # concatenation, so this is not vulnerable to SQL injection.
        query = query.filter(Product.title.ilike(f"%{_escape_like(q)}%", escape="\\"))

    products = query.order_by(Product.created_at.desc()).all()
    return render_template("products/index.html", products=products, search_form=search_form, q=q)


@products_bp.route("/products/new", methods=["GET", "POST"])
@login_required
def new():
    form = ProductForm()
    if form.validate_on_submit():
        try:
            image_name = save_product_image(form.image.data)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("products/new.html", form=form)

        product = Product(
            title=clean_text(form.title.data),
            description=clean_text(form.description.data),
            price=form.price.data,
            image_filename=image_name,
            seller_id=current_user.id,
        )
        db.session.add(product)
        db.session.commit()
        flash("상품이 등록되었습니다.", "success")
        return redirect(url_for("products.detail", product_id=product.id))

    return render_template("products/new.html", form=form)


@products_bp.route("/products/<int:product_id>")
def detail(product_id):
    product = Product.query.get_or_404(product_id)

    is_owner = current_user.is_authenticated and current_user.id == product.seller_id
    is_admin = current_user.is_authenticated and current_user.is_admin

    # Blocked/sold products are hidden from everyone except the seller and admins,
    # so a malicious actor can't just guess sequential IDs to view content that
    # was hidden because it was reported (broken access control / IDOR check).
    if product.status == ProductStatus.BLOCKED and not (is_owner or is_admin):
        abort(404)

    return render_template("products/detail.html", product=product, is_owner=is_owner)


@products_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin:
        abort(403)  # authorization check prevents IDOR (editing someone else's listing)

    form = ProductForm(obj=product)
    if form.validate_on_submit():
        try:
            image_name = save_product_image(form.image.data)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("products/edit.html", form=form, product=product)

        product.title = clean_text(form.title.data)
        product.description = clean_text(form.description.data)
        product.price = form.price.data
        if image_name:
            product.image_filename = image_name
        db.session.commit()
        flash("상품 정보가 수정되었습니다.", "success")
        return redirect(url_for("products.detail", product_id=product.id))

    return render_template("products/edit.html", form=form, product=product)


@products_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash("상품이 삭제되었습니다.", "info")
    return redirect(url_for("products.my_products"))


@products_bp.route("/products/<int:product_id>/sold", methods=["POST"])
@login_required
def mark_sold(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin:
        abort(403)
    product.status = ProductStatus.SOLD
    db.session.commit()
    flash("판매완료로 표시했습니다.", "success")
    return redirect(url_for("products.detail", product_id=product.id))


@products_bp.route("/my-products")
@login_required
def my_products():
    products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template("products/my_products.html", products=products)
