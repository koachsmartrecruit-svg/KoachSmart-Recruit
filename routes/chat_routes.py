from flask import (
    Blueprint, render_template,
    request, redirect, url_for, flash
)
from flask_login import login_required, current_user

from core.extensions import socketio, db
from models.user import User
from models.message import Message

# ---------------------------
# Blueprint
# ---------------------------
chat_bp = Blueprint("chat", __name__)

# ---------------------------
# Chat Page
# ---------------------------
@chat_bp.route("/chat")
@login_required
def chat_home():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template("chat.html", users=users)


@chat_bp.route("/chat/<int:user_id>")
@login_required
def chat_with_user(user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()

    return render_template(
        "chat_window.html",
        messages=messages,
        receiver_id=user_id
    )


# ---------------------------
# Socket Events
# ---------------------------
@socketio.on("send_message")
def handle_message(data):
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    content = data.get("content")

    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )

    db.session.add(message)
    db.session.commit()

    socketio.emit("receive_message", {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": content
    })
