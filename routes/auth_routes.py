from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from core.extensions import db
from models.user import User
from models.profile import Profile

from services.referral_service import generate_referral_code, apply_referral_bonus

# ---------------------------
# Blueprint
# ---------------------------
auth_bp = Blueprint("auth", __name__)

# ---------------------------
# Register
# ---------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing = User.query.filter_by(
            email=request.form.get("email")
        ).first()

        if existing:
            flash("Email already exists")
            return redirect(url_for("auth.register"))

        user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            role="coach",
            password=generate_password_hash(
                request.form.get("password")
            ),
            referral_code=generate_referral_code()
        )

        db.session.add(user)
        db.session.commit()

        profile = Profile(
            user_id=user.id,
            full_name=user.username
        )
        db.session.add(profile)
        db.session.commit()

        apply_referral_bonus(user)
        login_user(user)

        return redirect(url_for("payment.show_plans"))

    return render_template("register.html")


# ---------------------------
# Login
# ---------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            email=request.form.get("email")
        ).first()

        if user and user.password and check_password_hash(
            user.password,
            request.form.get("password")
        ):
            login_user(user)
            return redirect(url_for("coach.dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")


# ---------------------------
# Logout
# ---------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("public.home"))


# ---------------------------
# Google Auth (Placeholder)
# ---------------------------
@auth_bp.route("/login/google")
def login_google():
    return "Google Login Not Implemented", 501

@auth_bp.route("/authorize/google")
def authorize_google():
    return "Google Authorization Not Implemented", 501


# ---------------------------
# Password Reset
# ---------------------------
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("Password reset link sent (mock)")
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html")

@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password_mock():
    return render_template("reset_password.html")


# ---------------------------
# Role Selection
# ---------------------------
@auth_bp.route("/select-role", methods=["GET", "POST"])
@login_required
def select_role():
    if request.method == "POST":
        role = request.form.get("role")
        current_user.role = role
        db.session.commit()
        return redirect(url_for("coach.dashboard"))
    return render_template("select_role.html")
