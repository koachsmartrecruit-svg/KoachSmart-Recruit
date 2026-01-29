from flask import (
    Blueprint, render_template,
    request, redirect, url_for, flash, jsonify
)
from flask_login import login_required, current_user

from core.extensions import db
from models.job import Job
from models.application import Application
from models.profile import Profile
from services.ai_service import calculate_match_score

# ---------------------------
# Blueprint
# ---------------------------
coach_bp = Blueprint("coach", __name__)

# ---------------------------
# Coach Jobs Listing
# ---------------------------
@coach_bp.route("/jobs")
@login_required
def coach_jobs():
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))
    
    # Get filter parameters
    sport_filter = request.args.get('sport', 'All')
    city_filter = request.args.get('city', '')
    job_type_filter = request.args.get('job_type', 'All')
    min_salary_filter = request.args.get('min_salary', '')
    
    # Build query
    query = Job.query.filter_by(is_active=True)
    
    if sport_filter != 'All':
        query = query.filter(Job.sport == sport_filter)
    
    if city_filter:
        query = query.filter(Job.location.ilike(f'%{city_filter}%'))
    
    if job_type_filter != 'All':
        query = query.filter(Job.job_type == job_type_filter)
    
    jobs = query.all()
    
    # Get unique values for filters
    sports = db.session.query(Job.sport).distinct().all()
    sports = [s[0] for s in sports if s[0]]
    
    job_types = db.session.query(Job.job_type).distinct().all()
    job_types = [jt[0] for jt in job_types if jt[0]]
    
    filters = {
        'sport': sport_filter,
        'city': city_filter,
        'job_type': job_type_filter,
        'min_salary': min_salary_filter
    }
    
    # Mock pagination object
    class MockPagination:
        def __init__(self, items):
            self.items = items
            self.pages = 1
            self.page = 1
            self.has_prev = False
            self.has_next = False
            self.prev_num = None
            self.next_num = None
    
    pagination = MockPagination(jobs)
    
    return render_template(
        "coach_jobs.html",
        jobs=jobs,
        sports=sports,
        job_types=job_types,
        filters=filters,
        pagination=pagination
    )


# ---------------------------
# Dashboard
# ---------------------------
@coach_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))
        
    profile = current_user.profile
    jobs = Job.query.filter_by(is_active=True).all()
    my_apps = Application.query.filter_by(user_id=current_user.id).all()

    # Calculate profile completion percentage
    profile_completion = 0
    if profile:
        total_fields = 10  # Adjust based on required fields
        completed_fields = 0
        
        if profile.full_name: completed_fields += 1
        if profile.phone: completed_fields += 1
        if profile.bio: completed_fields += 1
        if profile.sport: completed_fields += 1
        if profile.experience_years: completed_fields += 1
        if profile.city: completed_fields += 1
        if profile.resume_path: completed_fields += 1
        if profile.certifications: completed_fields += 1
        if profile.working_type: completed_fields += 1
        if profile.is_verified: completed_fields += 1
        
        profile_completion = int((completed_fields / total_fields) * 100)
    
    # Get profile views (default to 0 if no profile)
    views = profile.views if profile else 0
    
    # Calculate average rating (placeholder - you may want to implement a rating system)
    avg_rating = 4.5  # Default rating
    
    return render_template(
        "coach_listing.html",
        jobs=jobs,
        my_apps=my_apps,
        profile=profile,
        profile_completion=profile_completion,
        views=views,
        avg_rating=avg_rating
    )


# ---------------------------
# Resume Builder
# ---------------------------
@coach_bp.route("/resume-builder")
@login_required
def resume_builder():
    return render_template("resume_builder.html")


@coach_bp.route("/text-to-resume", methods=["POST"])
@login_required
def text_to_resume():
    """API endpoint for AI resume generation"""
    data = request.get_json()
    text = data.get('text', '')
    
    # Simple text parsing - you can enhance this with AI service
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Basic parsing logic
    resume_data = {
        "full_name": "Professional Coach",
        "headline": "Sports Coach",
        "summary": "Experienced sports coach with passion for developing athletes.",
        "skills": ["Coaching", "Team Management", "Player Development", "Fitness Training"],
        "experience": [
            {
                "role": "Sports Coach",
                "description": "Coaching experience with focus on player development and team building."
            }
        ],
        "certifications": [],
        "achievements": []
    }
    
    # Extract name if mentioned
    for line in lines:
        if any(word in line.lower() for word in ['नाम', 'name', 'मैं']):
            # Simple name extraction
            words = line.split()
            if len(words) > 2:
                resume_data["full_name"] = " ".join(words[-2:])
    
    # Extract experience years
    for line in lines:
        if any(word in line for word in ['साल', 'year', 'experience']):
            resume_data["experience"][0]["description"] = line
    
    # Extract certifications
    for line in lines:
        if any(word in line.lower() for word in ['certified', 'certification', 'level']):
            resume_data["certifications"].append(line)
    
    return resume_data


# ---------------------------
# Edit Profile
# ---------------------------
@coach_bp.route("/profile/edit")
@login_required
def edit_profile():
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))
    
    # For now, redirect to onboarding - you may want to create a separate edit template
    return redirect(url_for("onboarding.onboarding_unified"))


# ---------------------------
# Apply Job
# ---------------------------
@coach_bp.route("/job/apply/<int:job_id>", methods=["POST"])
@login_required
def apply_job(job_id):
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))

    job = Job.query.get_or_404(job_id)
    profile = Profile.query.filter_by(
        user_id=current_user.id
    ).first()

    score, reason = calculate_match_score(profile, job)

    application = Application(
        job_id=job.id,
        user_id=current_user.id,
        match_score=score,
        match_reasons=reason
    )

    db.session.add(application)
    db.session.commit()

    flash(f"Applied successfully! Match: {score}%")
    return redirect(url_for("coach.dashboard"))


@coach_bp.route("/resume/<int:user_id>")
@login_required
def view_resume(user_id):
    return "Resume View Not Implemented", 501


@coach_bp.route("/profile/delete", methods=["POST"])
@login_required
def delete_profile():
    # In a real app, you would delete related data (profile, applications, etc.)
    # For now, just a placeholder or basic delete
    db.session.delete(current_user)
    db.session.commit()
    flash("Account deleted.")
    return redirect(url_for("public.home"))
