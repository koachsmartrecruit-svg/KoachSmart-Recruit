from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash

from core.extensions import db
from core.membership_guard import require_employer_membership, check_usage_limits
from models.job import Job
from models.user import User
from models.application import Application # Added import
from services.ai_service import predict_salary
from services.stats_service import get_employer_stats

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

    # Get real-time stats for the login page
    stats = get_employer_stats()
    return render_template("employer_login.html", stats=stats)

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

    # Get real-time stats for the register page
    stats = get_employer_stats()
    return render_template("employer_register.html", stats=stats)

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

    predicted_salary = None
    ai_reason = None
    form_data = {}

    if request.method == "POST":
        # Get form data
        title = request.form.get("title", "").strip()
        sport = request.form.get("sport", "").strip()
        description = request.form.get("description", "").strip()
        venue = request.form.get("venue", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        country = request.form.get("country", "").strip()
        requirements = request.form.get("requirements", "").strip()
        screening_questions = request.form.get("screening_questions", "").strip()
        job_type = request.form.get("job_type", "Full Time").strip()
        working_hours = request.form.get("working_hours", "").strip()
        salary = request.form.get("salary", "").strip()
        
        # Store form data for re-rendering
        form_data = {
            'title': title,
            'sport': sport,
            'description': description,
            'venue': venue,
            'city': city,
            'state': state,
            'country': country,
            'requirements': requirements,
            'screening_questions': screening_questions,
            'job_type': job_type,
            'working_hours': working_hours,
            'salary': salary
        }
        
        # Handle AI salary prediction
        if 'predict' in request.form:
            if title and sport and city:
                try:
                    predicted_salary, ai_reason = predict_salary(
                        title=title,
                        sport=sport,
                        city=city,
                        state=state,
                        country=country,
                        job_type=job_type,
                        requirements=requirements
                    )
                    if predicted_salary:
                        flash(f"💡 AI suggested salary: ₹{predicted_salary}/month", "success")
                    else:
                        flash("Unable to generate salary prediction. Please try again.", "warning")
                except Exception as e:
                    flash("Salary prediction service temporarily unavailable.", "warning")
                    predicted_salary, ai_reason = None, None
            else:
                flash("Please fill in job title, sport, and city to get salary prediction.", "warning")
            
            return render_template("job_new.html", 
                                 form_data=form_data, 
                                 predicted_salary=predicted_salary, 
                                 ai_reason=ai_reason)
        
        # Handle job creation
        if not title or not sport or not description:
            flash("Title, sport, and description are required.", "error")
            return render_template("job_new.html", 
                                 form_data=form_data, 
                                 predicted_salary=predicted_salary, 
                                 ai_reason=ai_reason)
        
        # Build location string from available components
        location_parts = []
        if venue:
            location_parts.append(venue)
        if city:
            location_parts.append(city)
        if state:
            location_parts.append(state)
        if country:
            location_parts.append(country)
        
        location = ", ".join(location_parts) if location_parts else "Location not specified"
        
        job = Job(
            employer_id=current_user.id,
            title=title,
            sport=sport,
            description=description,
            location=location,
            venue=venue,
            city=city,
            state=state,
            country=country,
            requirements=requirements or None,
            screening_questions=screening_questions or None,
            job_type=job_type,
            working_hours=working_hours or None,
            salary_range=salary or None,
            is_active=True
        )

        db.session.add(job)
        db.session.commit()
        flash("Job posted successfully", "success")

        return redirect(url_for("employer.dashboard"))

    return render_template("job_new.html", 
                         form_data=form_data, 
                         predicted_salary=predicted_salary, 
                         ai_reason=ai_reason)

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
    
    # Get employer's jobs for dashboard stats
    jobs = Job.query.filter_by(employer_id=current_user.id).all()
    active_jobs = [job for job in jobs if job.is_active]
    
    # Get applications for employer's jobs
    applications = Application.query.join(Job).filter(Job.employer_id == current_user.id).all()
    
    # Calculate stats
    stats = {
        'active_jobs': len(active_jobs),
        'total_jobs': len(jobs),
        'total_applications': len(applications),
        'pending_applications': len([app for app in applications if app.status == 'Applied']),
        'interviews_scheduled': len([app for app in applications if app.status == 'Interview']),
        'hired_count': len([app for app in applications if app.status == 'Hired'])
    }
    
    # Recent jobs (last 5)
    recent_jobs = Job.query.filter_by(employer_id=current_user.id).order_by(Job.created_at.desc()).limit(5).all()
    
    return render_template("employer_dashboard.html", stats=stats, recent_jobs=recent_jobs)

@employer_bp.route("/jobs")
@login_required
def jobs():
    """View all jobs posted by the employer"""
    if current_user.role != "employer":
        return redirect(url_for("employer.dashboard"))
    
    # Get all jobs for this employer
    jobs = Job.query.filter_by(employer_id=current_user.id).order_by(Job.created_at.desc()).all()
    
    # Get application counts for each job
    job_stats = {}
    for job in jobs:
        applications = Application.query.filter_by(job_id=job.id).all()
        job_stats[job.id] = {
            'total_applications': len(applications),
            'pending': len([app for app in applications if app.status == 'Applied']),
            'interviews': len([app for app in applications if app.status == 'Interview']),
            'hired': len([app for app in applications if app.status == 'Hired'])
        }
    
    return render_template("employer_jobs.html", jobs=jobs, job_stats=job_stats)


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
