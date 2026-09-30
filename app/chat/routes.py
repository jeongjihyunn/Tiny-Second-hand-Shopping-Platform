from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.models import User, Message

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

HISTORY_LIMIT = 100


@chat_bp.route("/")
@login_required
def global_chat():
    history = (Message.query.filter_by(room="global")
               .order_by(Message.created_at.desc()).limit(HISTORY_LIMIT).all())
    history.reverse()
    return render_template("chat/global.html", room="global", history=history)


@chat_bp.route("/inbox")
@login_required
def inbox():
    # A user only ever knows about a DM room's existence by being one of the
    # two IDs baked into its name ("dm:<lo>:<hi>"), so this is a safe filter:
    # it can't surface a conversation the current user isn't part of.
    my_rooms = (Message.query
                .filter(or_(Message.room.like(f"dm:{current_user.id}:%"),
                            Message.room.like(f"dm:%:{current_user.id}")))
                .order_by(Message.created_at.desc())
                .all())

    conversations = []
    seen_rooms = set()
    for m in my_rooms:
        if m.room in seen_rooms:
            continue
        seen_rooms.add(m.room)
        _, lo, hi = m.room.split(":")
        other_id = int(hi) if int(lo) == current_user.id else int(lo)
        other = User.query.get(other_id)
        if other:
            conversations.append({"other": other, "last_message": m})

    return render_template("chat/inbox.html", conversations=conversations)


@chat_bp.route("/dm/<int:user_id>")
@login_required
def direct_message(user_id):
    if user_id == current_user.id:
        abort(400)
    other = User.query.get_or_404(user_id)
    room = Message.dm_room(current_user.id, other.id)

    # Authorization: only the two participants can ever view/join this room.
    # Server derives the room name itself from the two IDs rather than
    # trusting a room name supplied by the client, so a user can't guess or
    # forge another pair's room string to eavesdrop (IDOR on chat rooms).
    history = (Message.query.filter_by(room=room)
               .order_by(Message.created_at.desc()).limit(HISTORY_LIMIT).all())
    history.reverse()
    return render_template("chat/dm.html", room=room, history=history, other=other)
