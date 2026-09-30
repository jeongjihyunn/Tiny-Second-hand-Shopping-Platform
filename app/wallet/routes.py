from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Transaction
from app.wallet.forms import TransferForm
from app.utils import clean_text

wallet_bp = Blueprint("wallet", __name__, url_prefix="/wallet")


@wallet_bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    form = TransferForm()
    if form.validate_on_submit():
        amount = form.amount.data
        to_username = form.to_username.data.strip()

        if to_username == current_user.username:
            flash("자기 자신에게는 송금할 수 없습니다.", "danger")
            return render_template("wallet/transfer.html", form=form)

        # Everything below runs inside one DB transaction. On the SQLite
        # backend used for local/dev runs, SQLAlchemy's `with_for_update()`
        # is a no-op, but SQLite already serializes writers at the
        # connection level, so two concurrent transfers from the same
        # sender cannot both read a stale balance and overdraw the account.
        # On a real deployment (Postgres/MySQL) `with_for_update()` takes a
        # genuine row lock, closing the same TOCTOU race there too.
        sender = User.query.filter_by(id=current_user.id).with_for_update().first()
        receiver = User.query.filter_by(username=to_username).with_for_update().first()

        if receiver is None:
            db.session.rollback()
            flash("받는 사람을 찾을 수 없습니다.", "danger")
            return render_template("wallet/transfer.html", form=form)

        if sender.balance < amount:
            db.session.rollback()
            flash("잔액이 부족합니다.", "danger")
            return render_template("wallet/transfer.html", form=form)

        sender.balance -= amount
        receiver.balance += amount
        tx = Transaction(
            sender_id=sender.id, receiver_id=receiver.id,
            amount=amount, memo=clean_text(form.memo.data),
        )
        db.session.add(tx)
        db.session.commit()

        flash(f"{receiver.username}님에게 {amount:,}원을 송금했습니다.", "success")
        return redirect(url_for("wallet.history"))

    return render_template("wallet/transfer.html", form=form)


@wallet_bp.route("/history")
@login_required
def history():
    sent = Transaction.query.filter_by(sender_id=current_user.id)
    received = Transaction.query.filter_by(receiver_id=current_user.id)
    txs = sent.union(received).order_by(Transaction.created_at.desc()).all()
    return render_template("wallet/history.html", txs=txs)
