import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask

from core.extensions import db, login_manager, mail, socketio
from core.access_guard import unified_access_guard


# ------------------------------------------------------
# Project Base Directory
# ------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------
# Application Factory
# ------------------------------------------------------
def create_app():
    load_dotenv()

    # ✅ Explicit template + static folders
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    # -----------------------------
    # Core Config
    # -----------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # -----------------------------
    # Upload Folders
    # -----------------------------
    app.config["UPLOAD_FOLDER"] = str(BASE_DIR / "static/uploads")
    app.config["CERT_FOLDER"] = str(BASE_DIR / "static/certs")
    app.config["RESUME_FOLDER"] = str(BASE_DIR / "static/resumes")
    app.config["PROFILE_PIC_FOLDER"] = str(BASE_DIR / "static/profile_pics")
    app.config["EXP_PROOF_FOLDER"] = str(BASE_DIR / "static/experience_proofs")
    app.config["ID_PROOF_FOLDER"] = str(BASE_DIR / "static/id_proofs")
    app.config["TEMP_FOLDER"] = str(BASE_DIR / "static/temp_docs")
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

    for folder in [
        app.config["UPLOAD_FOLDER"],
        app.config["CERT_FOLDER"],
        app.config["RESUME_FOLDER"],
        app.config["PROFILE_PIC_FOLDER"],
        app.config["EXP_PROOF_FOLDER"],
        app.config["ID_PROOF_FOLDER"],
        app.config["TEMP_FOLDER"],
    ]:
        os.makedirs(folder, exist_ok=True)

    # -----------------------------
    # Mail Config
    # -----------------------------
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

    # -----------------------------
    # Stripe Config
    # -----------------------------
    app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY")
    app.config["STRIPE_PUBLISHABLE_KEY"] = os.getenv("STRIPE_PUBLISHABLE_KEY")
    app.config["STRIPE_PRICE_BASIC"] = os.getenv("STRIPE_PRICE_BASIC")
    app.config["STRIPE_PRICE_PRO"] = os.getenv("STRIPE_PRICE_PRO")
    app.config["STRIPE_WEBHOOK_SECRET"] = os.getenv("STRIPE_WEBHOOK_SECRET")

    # -----------------------------
    # Initialize Extensions
    # -----------------------------
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)

    # -----------------------------
    # Register Guards
    # -----------------------------
    app.before_request(unified_access_guard)

    # -----------------------------
    # Register Models (important)
    # -----------------------------
    import models  # noqa

    # -----------------------------
    # Register Blueprints
    # -----------------------------
    from routes.public_routes import public_bp
    from routes.auth_routes import auth_bp
    from routes.coach_routes import coach_bp
    from routes.employer_routes import employer_bp
    from routes.onboarding_routes import onboarding_bp
    from routes.admin_routes import admin_bp
    from routes.payment_routes import payment_bp
    from routes.chat_routes import chat_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(employer_bp, url_prefix='/employer')
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(chat_bp)

    return app
