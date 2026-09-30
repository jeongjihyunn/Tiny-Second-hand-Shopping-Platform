from urllib.parse import urlparse

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, limiter
from app.models import User, UserStatus
from app.auth.forms import RegisterForm, LoginForm, ProfileForm, ChangePasswordForm
from app.utils import clean_text

auth_bp = Blueprint("auth", __name__)


def _safe_redirect_target(target):
    """Only allow redirecting to a relative, same-site path.

    Blindly trusting `next=` lets an attacker craft a login link that sends
    the user to `evil.com` right after they authenticate (open redirect,
    often chained with phishing). We only accept paths with no netloc/scheme.
    """
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.netloc or parsed.scheme:
        return None
    return target


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing:
            flash("이미 사용 중인 아이디입니다.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(username=form.username.data, balance=current_app.config["SIGNUP_BONUS_BALANCE"])
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("회원가입이 완료되었습니다. 로그인해주세요.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # slow down brute-force / credential-stuffing attempts
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        # Deliberately identical error message + timing-insensitive check
        # regardless of whether the username exists, to avoid leaking which
        # usernames are registered (user enumeration).
        if user is None or not user.check_password(form.password.data):
            current_app.logger.info("failed login attempt for username=%r", form.username.data)
            flash("아이디 또는 비밀번호가 올바르지 않습니다.", "danger")
            return render_template("auth/login.html", form=form)

        if user.status == UserStatus.DORMANT:
            flash("신고 누적으로 휴면 처리된 계정입니다. 관리자에게 문의하세요.", "danger")
            return render_template("auth/login.html", form=form)
        if user.status == UserStatus.BANNED:
            flash("이용이 정지된 계정입니다.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user)
        flash(f"{user.username}님, 환영합니다!", "success")
        target = _safe_redirect_target(request.args.get("next"))
        return redirect(target or url_for("products.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃 되었습니다.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/mypage", methods=["GET", "POST"])
@login_required
def mypage():
    profile_form = ProfileForm(bio=current_user.bio)
    password_form = ChangePasswordForm()

    if profile_form.submit_profile.data and profile_form.validate_on_submit():
        current_user.bio = clean_text(profile_form.bio.data)
        db.session.commit()
        flash("소개글이 저장되었습니다.", "success")
        return redirect(url_for("auth.mypage"))

    if password_form.submit_password.data and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash("현재 비밀번호가 올바르지 않습니다.", "danger")
        else:
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash("비밀번호가 변경되었습니다.", "success")
        return redirect(url_for("auth.mypage"))

    return render_template("auth/mypage.html", profile_form=profile_form, password_form=password_form)


@auth_bp.route("/users/<int:user_id>")
@login_required
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("auth/public_profile.html", profile_user=user)
