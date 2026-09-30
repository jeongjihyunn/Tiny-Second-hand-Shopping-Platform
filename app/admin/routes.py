from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Product, Report, UserStatus, ProductStatus, TargetType
from app.utils import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
@admin_required
def _guard():
    """Every route in this blueprint requires an authenticated admin.
    Using before_request means we can't forget the decorator on a future
    route added to this file (fail-safe by construction)."""
    pass


@admin_bp.route("/")
def dashboard():
    stats = {
        "users": User.query.count(),
        "products": Product.query.count(),
        "open_reports": Report.query.filter_by(resolved=False).count(),
        "dormant_users": User.query.filter_by(status=UserStatus.DORMANT).count(),
        "blocked_products": Product.query.filter_by(status=ProductStatus.BLOCKED).count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/users")
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/status/<string:new_status>", methods=["POST"])
def set_user_status(user_id, new_status):
    if new_status not in UserStatus.__members__.values() and new_status not in [s.value for s in UserStatus]:
        abort(400)
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("자기 자신의 상태는 변경할 수 없습니다.", "warning")
        return redirect(url_for("admin.users"))
    user.status = UserStatus(new_status)
    db.session.commit()
    flash(f"{user.username}의 상태를 {new_status}(으)로 변경했습니다.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/products")
def products():
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=all_products)


@admin_bp.route("/products/<int:product_id>/status/<string:new_status>", methods=["POST"])
def set_product_status(product_id, new_status):
    if new_status not in [s.value for s in ProductStatus]:
        abort(400)
    product = Product.query.get_or_404(product_id)
    product.status = ProductStatus(new_status)
    db.session.commit()
    flash("상품 상태가 변경되었습니다.", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/reports")
def reports():
    open_reports = Report.query.filter_by(resolved=False).order_by(Report.created_at.desc()).all()
    return render_template("admin/reports.html", reports=open_reports, User=User, Product=Product,
                            TargetType=TargetType)


@admin_bp.route("/reports/<int:report_id>/resolve", methods=["POST"])
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.resolved = True
    db.session.commit()
    flash("신고를 처리 완료로 표시했습니다.", "success")
    return redirect(url_for("admin.reports"))
