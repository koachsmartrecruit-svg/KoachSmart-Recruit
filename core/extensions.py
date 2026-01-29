from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO

# -----------------------------
# Database
# -----------------------------
db = SQLAlchemy()

# -----------------------------
# Authentication
# -----------------------------
login_manager = LoginManager()
login_manager.login_view = "auth.login"

# -----------------------------
# Mail
# -----------------------------
mail = Mail()

# -----------------------------
# Realtime / SocketIO
# -----------------------------
socketio = SocketIO(cors_allowed_origins="*")


@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))
