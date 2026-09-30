from flask import Blueprint, render_template, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Report, TargetType, User, Product, UserStatus, ProductStatus
from app.reports.forms import ReportForm
from app.utils import clean_text

reports_bp = Blueprint("reports", __name__, url_prefix="/report")


@reports_bp.route("/user/<int:user_id>", methods=["GET", "POST"])
@login_required
def report_user(user_id):
    target = User.query.get_or_404(user_id)
    if target.id == current_user.id:
        abort(400)  # can't report yourself

    form = ReportForm()
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            target_type=TargetType.USER,
            target_id=target.id,
            reason=clean_text(form.reason.data),
        )
        db.session.add(report)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("이미 이 사용자를 신고하셨습니다.", "warning")
            return redirect(url_for("auth.public_profile", user_id=target.id))

        _apply_threshold_if_needed(TargetType.USER, target.id)
        flash("신고가 접수되었습니다.", "success")
        return redirect(url_for("auth.public_profile", user_id=target.id))

    return render_template("reports/report_form.html", form=form, target_label=f"사용자 '{target.username}'")


@reports_bp.route("/product/<int:product_id>", methods=["GET", "POST"])
@login_required
def report_product(product_id):
    target = Product.query.get_or_404(product_id)
    if target.seller_id == current_user.id:
        abort(400)

    form = ReportForm()
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            target_type=TargetType.PRODUCT,
            target_id=target.id,
            reason=clean_text(form.reason.data),
        )
        db.session.add(report)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("이미 이 상품을 신고하셨습니다.", "warning")
            return redirect(url_for("products.detail", product_id=target.id))

        _apply_threshold_if_needed(TargetType.PRODUCT, target.id)
        flash("신고가 접수되었습니다.", "success")
        return redirect(url_for("products.detail", product_id=target.id))

    return render_template("reports/report_form.html", form=form, target_label=f"상품 '{target.title}'")


def _apply_threshold_if_needed(target_type: TargetType, target_id: int):
    threshold = current_app.config["REPORT_THRESHOLD"]
    count = Report.query.filter_by(target_type=target_type, target_id=target_id).count()

    if target_type == TargetType.USER:
        user = db.session.get(User, target_id)
        user.report_count = count
        if count >= threshold and user.status == UserStatus.ACTIVE:
            user.status = UserStatus.DORMANT
            current_app.logger.info("user id=%s auto-suspended after %s reports", target_id, count)
    else:
        product = db.session.get(Product, target_id)
        product.report_count = count
        if count >= threshold and product.status == ProductStatus.ACTIVE:
            product.status = ProductStatus.BLOCKED
            current_app.logger.info("product id=%s auto-blocked after %s reports", target_id, count)

    db.session.commit()
