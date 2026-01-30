from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash

from core.extensions import db
from core.membership_guard import require_employer_membership, check_usage_limits
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
@require_employer_membership
def new_job():
    """Create new job posting - requires active membership"""
    if current_user.role != "employer":
        return redirect(url_for("employer.dashboard"))

    # Check usage limits before allowing job posting
    if not check_usage_limits(current_user, 'job_posting'):
        flash('You have reached your monthly job posting limit. Please upgrade your membership to post more jobs.', 'warning')
        return redirect(url_for('membership.plans'))

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
        flash("Job posted successfully", "success")

        return redirect(url_for("employer.dashboard"))

    return render_template("job_new.html")

@employer_bp.route("/job/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
@require_employer_membership
def edit_job(job_id):
    """Edit job posting - requires active membership"""
    if current_user.role != "employer":
        return redirect(url_for("employer.dashboard"))
    
    job = Job.query.get_or_404(job_id)
    
    # Ensure only job owner can edit
    if job.employer_id != current_user.id:
        flash("You can only edit your own jobs", "error")
        return redirect(url_for("employer.dashboard"))
    
    if request.method == "POST":
        job.title = request.form.get("title")
        job.sport = request.form.get("sport")
        job.description = request.form.get("description")
        job.city = request.form.get("city")
        
        db.session.commit()
        flash("Job updated successfully", "success")
        return redirect(url_for("employer.dashboard"))
    
    return render_template("job_edit.html", job=job)

@employer_bp.route("/job/<int:job_id>/toggle", methods=["POST"])
@login_required
def toggle_job_status(job_id):
    """Toggle job active/inactive status"""
    if current_user.role != "employer":
        return redirect(url_for("employer.dashboard"))
    
    job = Job.query.get_or_404(job_id)
    
    # Ensure only job owner can toggle
    if job.employer_id != current_user.id:
        flash("You can only manage your own jobs", "error")
        return redirect(url_for("employer.dashboard"))
    
    job.is_active = not job.is_active
    db.session.commit()
    
    status = "activated" if job.is_active else "deactivated"
    flash(f"Job {status} successfully", "success")
    return redirect(url_for("employer.dashboard"))

@employer_bp.route("/application/<int:app_id>/status/<new_status>", methods=["GET", "POST"])
@login_required
def update_status(app_id, new_status):
    """Update application status"""
    if current_user.role != "employer":
        return redirect(url_for("employer.dashboard"))
    
    app = Application.query.get_or_404(app_id)
    
    # Ensure only job owner can update status
    if app.job.employer_id != current_user.id:
        flash("You can only manage applications for your jobs", "error")
        return redirect(url_for("employer.dashboard"))
    
    app.status = new_status
    
    # Handle interview scheduling
    if new_status == "Interview" and request.method == "POST":
        meeting_link = request.form.get("meeting_link")
        if meeting_link:
            # You could store this in a separate table or add a field to Application
            flash(f"Interview scheduled. Meeting link: {meeting_link}", "success")
    
    db.session.commit()
    flash(f"Application status updated to {new_status}", "success")
    return redirect(url_for("employer.dashboard"))

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
