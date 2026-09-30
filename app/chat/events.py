from flask_login import current_user
from flask_socketio import join_room, emit, disconnect

from app.extensions import db, socketio
from app.models import Message
from app.utils import clean_text

MAX_MESSAGE_LEN = 1000


def _room_is_authorized(room: str) -> bool:
    """Re-derive/verify membership server-side; never trust the client's
    claim about which room it belongs in.
    """
    if room == "global":
        return True
    if room.startswith("dm:"):
        try:
            _, lo, hi = room.split(":")
            lo, hi = int(lo), int(hi)
        except ValueError:
            return False
        return current_user.id in (lo, hi)
    return False


@socketio.on("connect")
def handle_connect():
    if not current_user.is_authenticated:
        # Reject unauthenticated socket connections outright.
        disconnect()
        return False


@socketio.on("join")
def handle_join(data):
    if not current_user.is_authenticated:
        disconnect()
        return
    room = (data or {}).get("room", "")
    if not _room_is_authorized(room):
        emit("error", {"message": "채팅방에 접근할 권한이 없습니다."})
        disconnect()
        return
    join_room(room)


@socketio.on("send_message")
def handle_send_message(data):
    if not current_user.is_authenticated:
        disconnect()
        return

    room = (data or {}).get("room", "")
    body = (data or {}).get("body", "")

    if not _room_is_authorized(room):
        emit("error", {"message": "채팅방에 접근할 권한이 없습니다."})
        return

    body = clean_text(body)[:MAX_MESSAGE_LEN]
    if not body:
        return

    message = Message(room=room, sender_id=current_user.id, body=body)
    db.session.add(message)
    db.session.commit()

    # Broadcast the *sanitized, server-persisted* copy back out, not the raw
    # client payload, so every recipient (including the sender's other tabs)
    # sees the same trusted content. Jinja/JS-side rendering still escapes
    # this on display as a second layer of XSS protection.
    emit("new_message", {
        "room": room,
        "sender_id": current_user.id,
        "sender_username": current_user.username,
        "body": message.body,
        "created_at": message.created_at.isoformat(),
    }, room=room)
