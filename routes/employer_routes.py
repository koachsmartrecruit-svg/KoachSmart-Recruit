from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash

from core.extensions import db
from models.job import Job
from models.user import User
from models.application import Application # Added import

# ---------------------------
# Blueprint
# ---------------------------
employer_bp = Blueprint("employer", __name__)

# ---------------------------
# Routes
# ---------------------------
@employer_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and current_user.role == "employer":
        return redirect(url_for("employer.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        
        if user and user.role == "employer" and user.password and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful")
            return redirect(url_for("employer.dashboard"))
        else:
            flash("Invalid email or password")
            return redirect(url_for("employer.login"))

    return render_template("employer_login.html")

@employer_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated and current_user.role == "employer":
        return redirect(url_for("employer.dashboard"))

    if request.method == "POST":
        company_name = request.form.get("company_name")
        email = request.form.get("email")
        password = request.form.get("password")

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email already registered")
            return redirect(url_for("employer.register"))

        user = User(
            username=company_name,
            email=email,
            password=generate_password_hash(password),
            role="employer"
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created successfully")
        return redirect(url_for("employer.dashboard"))

    return render_template("employer_register.html")

@employer_bp.route("/job/new", methods=["GET", "POST"])
@login_required
def new_job():
    if current_user.role != "employer":
        return redirect(url_for("employer.dashboard"))

    if request.method == "POST":
        job = Job(
            employer_id=current_user.id,
            title=request.form.get("title"),
            sport=request.form.get("sport"),
            description=request.form.get("description"),
            city=request.form.get("city"),
            is_active=True
        )

        db.session.add(job)
        db.session.commit()
        flash("Job posted successfully")

        return redirect(url_for("employer.dashboard"))

    return render_template("job_new.html")

@employer_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "employer":
        return redirect(url_for("employer.dashboard"))
    
    # Render the employer dashboard template
    return render_template("employer_dashboard.html")


@employer_bp.route("/explore")
@login_required
def explore_coaches():
    # Mock data for template rendering
    class Pagination:
        page = 1
        pages = 1
        has_prev = False
        has_next = False
        prev_num = None
        next_num = None

    return render_template(
        "coach_explore.html",
        coaches=[],
        sports=[],
        filters={},
        pagination=Pagination()
    )
