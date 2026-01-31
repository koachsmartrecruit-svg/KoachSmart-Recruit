from flask import (
    Blueprint, render_template,
    request, redirect, url_for, flash, jsonify
)
from flask_login import login_required, current_user

from core.extensions import db
from core.onboarding_guard import require_onboarding_completion
from core.membership_guard import require_coach_membership, check_usage_limits
from models.job import Job
from models.application import Application
from models.profile import Profile
from models.user import User
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
@require_onboarding_completion
@require_coach_membership
def coach_jobs():
    """Coach jobs listing - requires onboarding completion and active membership"""
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
    """Coach dashboard - shows onboarding progress if not completed"""
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))
    
    # Check onboarding completion
    if not current_user.onboarding_completed:
        from core.onboarding_guard import get_onboarding_progress, get_onboarding_rewards
        progress = get_onboarding_progress()
        rewards = get_onboarding_rewards()
        
        return render_template(
            "coach_onboarding_prompt.html",
            progress=progress,
            rewards=rewards,
            user=current_user
        )
        
    profile = current_user.profile
    jobs = Job.query.filter_by(is_active=True).limit(5).all()  # Show recent jobs
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
# My Profile - User Journey Dashboard
# ---------------------------
@coach_bp.route("/profile")
@login_required
def my_profile():
    """My Profile - Shows complete user journey, documents, badges, coins"""
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))
    
    from models.verification import VerificationStage, VerificationDocument, CoachSlugPage
    
    profile = current_user.profile
    
    # Get or create verification stage
    verification = VerificationStage.query.filter_by(user_id=current_user.id).first()
    if not verification:
        verification = VerificationStage(user_id=current_user.id)
        db.session.add(verification)
        db.session.commit()
    
    # Get uploaded documents with verification status
    documents = VerificationDocument.query.filter_by(user_id=current_user.id).all()
    
    # Get public slug page
    slug_page = CoachSlugPage.query.filter_by(user_id=current_user.id).first()
    
    # Calculate journey progress
    journey_data = {
        'stage_1': {
            'completed': current_user.onboarding_completed or verification.stage_1_completed,
            'score': verification.calculate_stage_1_score(),
            'max_score': 7,
            'coins': verification.stage_1_coins or 150,
            'badge': 'Orange Badge' if verification.orange_badge else None,
            'checklist': [
                {'name': 'Name Verified', 'status': verification.name_verified or bool(profile and profile.full_name)},
                {'name': 'Phone Verified', 'status': current_user.phone_verified},
                {'name': 'Email Verified', 'status': current_user.email_verified},
                {'name': 'Aadhar Verified', 'status': current_user.aadhar_verified},
                {'name': 'Username Created', 'status': bool(current_user.username)},
                {'name': 'Password Set', 'status': bool(current_user.password)},
                {'name': 'Digital ID Created', 'status': bool(current_user.digital_id)}
            ]
        },
        'stage_2': {
            'completed': verification.stage_2_completed,
            'score': verification.calculate_stage_2_score(),
            'max_score': 8,
            'coins': verification.stage_2_coins or 200,
            'badge': 'Purple Badge' if verification.purple_badge else None,
            'checklist': [
                {'name': 'Language Selected', 'status': bool(current_user.preferred_language)},
                {'name': 'State Selected', 'status': bool(profile and profile.state)},
                {'name': 'City Selected', 'status': bool(profile and profile.city)},
                {'name': 'Location Mapped', 'status': bool(profile and profile.location)},
                {'name': 'Service Area Set', 'status': bool(profile and profile.serviceable_area)},
                {'name': 'Job Type Selected', 'status': bool(profile and profile.job_types)},
                {'name': 'Specific Location Set', 'status': bool(profile and profile.specific_locations)},
                {'name': 'Range Set', 'status': bool(profile and profile.range_km)}
            ]
        },
        'stage_3': {
            'completed': verification.stage_3_completed,
            'score': verification.calculate_stage_3_score(),
            'max_score': 8,
            'coins': verification.stage_3_coins or 500,
            'badge': 'Blue Verified Badge' if verification.blue_badge else None,
            'checklist': [
                {'name': 'Education Added', 'status': bool(profile and profile.education)},
                {'name': 'Specialization Added', 'status': bool(profile and profile.specialization)},
                {'name': 'Education Document', 'status': bool(profile and profile.education_doc_path)},
                {'name': 'Professional Cert', 'status': bool(profile and profile.has_professional_cert)},
                {'name': 'Cert Document', 'status': bool(profile and profile.cert_doc_path)},
                {'name': 'Playing Level', 'status': bool(profile and profile.playing_level)},
                {'name': 'Playing Document', 'status': bool(profile and profile.playing_doc_path)},
                {'name': 'Experience Added', 'status': bool(profile and profile.experience_years)}
            ]
        }
    }
    
    # Get badges from user
    user_badges = current_user.badges.split(',') if current_user.badges else []
    
    # Document status summary
    doc_summary = {
        'total': len(documents),
        'pending': len([d for d in documents if d.verification_status == 'pending']),
        'verified': len([d for d in documents if d.verification_status == 'verified']),
        'rejected': len([d for d in documents if d.verification_status == 'rejected'])
    }
    
    return render_template(
        "coach_profile.html",
        profile=profile,
        verification=verification,
        documents=documents,
        slug_page=slug_page,
        journey_data=journey_data,
        user_badges=user_badges,
        doc_summary=doc_summary,
        current_stage=verification.get_current_stage(),
        badge_level=verification.get_badge_level()
    )

# ---------------------------
# Edit Profile
# ---------------------------
@coach_bp.route("/profile/edit")
@login_required
@require_onboarding_completion
def edit_profile():
    """Edit profile - requires onboarding completion"""
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))
    
    # For now, redirect to onboarding - you may want to create a separate edit template
    return redirect(url_for("onboarding.onboarding_unified"))


# ---------------------------
# Apply Job
# ---------------------------
@coach_bp.route("/job/apply/<int:job_id>", methods=["POST"])
@login_required
@require_onboarding_completion
@require_coach_membership
def apply_job(job_id):
    # 🔐 Onboarding check
    if not current_user.onboarding_completed:
        flash("Complete onboarding to apply for jobs.", "error")
        return redirect(url_for("onboarding.onboarding_unified"))

    """Apply for job - requires onboarding completion and active membership"""
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))

    # Check usage limits before allowing application
    if not check_usage_limits(current_user, 'job_applications'):
        flash('You have reached your monthly application limit. Please upgrade your membership to apply for more jobs.', 'warning')
        return redirect(url_for('membership.plans'))

    job = Job.query.get_or_404(job_id)
    
    # Check if already applied
    existing_application = Application.query.filter_by(
        job_id=job_id,
        user_id=current_user.id
    ).first()
    
    if existing_application:
        flash('You have already applied for this job.', 'info')
        return redirect(url_for("coach.coach_jobs"))

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

    flash(f"Applied successfully! Match: {score}%", 'success')
    return redirect(url_for("coach.coach_jobs"))


@coach_bp.route("/resume/<int:user_id>")
@login_required
@require_onboarding_completion
def view_resume(user_id):
    """View resume - requires onboarding completion"""
    return "Resume View Not Implemented", 501


@coach_bp.route("/applications")
@login_required
@require_onboarding_completion
def view_applications():
    """View job applications - requires onboarding completion"""
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))
    
    applications = Application.query.filter_by(user_id=current_user.id).all()
    return render_template("coach_applications.html", applications=applications)


@coach_bp.route("/profile/update", methods=["POST"])
@login_required
@require_onboarding_completion
def update_profile():
    """Update profile - requires onboarding completion"""
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))
    
    # Profile update logic here
    flash("Profile updated successfully!")
    return redirect(url_for("coach.dashboard"))


@coach_bp.route("/profile/delete", methods=["POST"])
@login_required
def delete_profile():
    # In a real app, you would delete related data (profile, applications, etc.)
    # For now, just a placeholder or basic delete
    db.session.delete(current_user)
    db.session.commit()
    flash("Account deleted.")
    return redirect(url_for("public.home"))

# ---------------------------
# Referral Dashboard
# ---------------------------
@coach_bp.route("/referrals")
@login_required
@require_onboarding_completion
def referral_dashboard():
    """Referral dashboard - shows referral stats and code"""
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))
    
    # Ensure user has a referral code
    if not current_user.referral_code:
        import secrets
        current_user.referral_code = secrets.token_hex(4).upper()
        db.session.commit()
    
    # Get basic referral statistics
    from models.language import ReferralSystem
    total_referrals = User.query.filter_by(referred_by=current_user.referral_code).count()
    
    # Calculate total rewards (1000 coins per successful referral)
    successful_referrals = User.query.filter(
        User.referred_by == current_user.referral_code,
        User.onboarding_completed == True
    ).count()
    
    total_rewards = successful_referrals * 1000
    
    # Get recent referrals
    recent_referrals = User.query.filter_by(referred_by=current_user.referral_code).limit(5).all()
    recent_list = []
    for user in recent_referrals:
        recent_list.append({
            'username': user.username,
            'date': user.onboarding_completed_at,  # Keep as datetime object or None
            'milestone': 'orange_completion' if user.onboarding_completed else None,
            'reward_awarded': user.onboarding_completed
        })
    
    referral_stats = {
        'referral_code': current_user.referral_code,
        'total_referrals': total_referrals,
        'successful_referrals': successful_referrals,
        'total_rewards_earned': total_rewards,
        'recent_referrals': recent_list
    }
    
    # Simple leaderboard
    leaderboard = []
    
    return render_template(
        "referral_dashboard.html",
        referral_stats=referral_stats,
        leaderboard=leaderboard,
        user=current_user
    )