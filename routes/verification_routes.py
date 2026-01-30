import os
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, current_app, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from core.extensions import db
from core.onboarding_guard import require_onboarding_completion
from models.verification import VerificationStage, VerificationDocument, CoachSlugPage
from models.user import User
from models.profile import Profile
from services.verification_service import VerificationService
from services.otp_service import generate_otp, save_otp, verify_otp
from services.email_service import send_otp_email
from validators.phone_validator import is_valid_phone
from validators.common_validator import validate_email

# ---------------------------
# Blueprint
# ---------------------------
verification_bp = Blueprint("verification", __name__)

# ---------------------------
# Multi-Stage Verification Dashboard
# ---------------------------
@verification_bp.route("/verification/dashboard")
@login_required
@require_onboarding_completion
def verification_dashboard():
    """Main verification dashboard showing all stages - requires onboarding completion"""
    if current_user.role != "coach":
        flash("Only coaches can access verification system")
        return redirect(url_for("public.home"))
    
    progress = VerificationService.get_verification_progress(current_user.id)
    stage = VerificationService.get_or_create_verification_stage(current_user.id)
    
    return render_template(
        "verification/dashboard.html",
        progress=progress,
        stage=stage,
        current_stage=stage.get_current_stage()
    )

# ---------------------------
# Stage 1: Basic Verification (Orange Badge)
# ---------------------------
@verification_bp.route("/verification/stage1")
@login_required
@require_onboarding_completion
def stage1():
    """Stage 1 verification - requires onboarding completion"""
    """Stage 1: Basic personal verification"""
    if current_user.role != "coach":
        return redirect(url_for("public.home"))
    
    stage = VerificationService.get_or_create_verification_stage(current_user.id)
    return render_template("verification/stage1.html", stage=stage)

@verification_bp.route("/verification/stage1/phone", methods=["POST"])
@login_required
def verify_phone():
    """Verify phone number with OTP"""
    phone = request.form.get("phone")
    
    if not is_valid_phone(phone):
        flash("Invalid phone number format", "error")
        return redirect(url_for("verification.stage1"))
    
    # Generate and send OTP
    otp = generate_otp()
    save_otp(current_user.id, phone, otp, "phone")
    
    # In production, send SMS OTP
    # For now, just show in flash message
    flash(f"OTP sent to {phone}: {otp}", "info")
    
    session['verification_phone'] = phone
    return render_template("verification/verify_otp.html", 
                         phone=phone, verification_type="phone")

@verification_bp.route("/verification/stage1/phone/confirm", methods=["POST"])
@login_required
def confirm_phone():
    """Confirm phone OTP"""
    otp = request.form.get("otp")
    phone = session.get('verification_phone')
    
    if verify_otp(current_user.id, otp, "phone"):
        VerificationService.verify_phone(current_user.id, phone)
        
        # Update user phone
        current_user.profile.phone = phone
        db.session.commit()
        
        flash("Phone verified successfully! +50 coins earned", "success")
        session.pop('verification_phone', None)
        
        # Check if stage 1 is complete
        VerificationService.complete_stage_1(current_user.id)
        
        return redirect(url_for("verification.stage1"))
    else:
        flash("Invalid OTP. Please try again.", "error")
        return redirect(url_for("verification.stage1"))

@verification_bp.route("/verification/stage1/email", methods=["POST"])
@login_required
def verify_email():
    """Send email verification"""
    if not validate_email(current_user.email):
        flash("Invalid email address", "error")
        return redirect(url_for("verification.stage1"))
    
    # Generate verification token
    otp = generate_otp()
    save_otp(current_user.id, current_user.email, otp, "email")
    
    # Send verification email
    try:
        send_otp_email(current_user.email, otp)
        flash("Verification email sent! Check your inbox.", "info")
    except Exception as e:
        flash("Failed to send verification email. Please try again.", "error")
    
    return redirect(url_for("verification.stage1"))

@verification_bp.route("/verification/stage1/email/confirm/<token>")
def confirm_email(token):
    """Confirm email verification"""
    if verify_otp(current_user.id, token, "email"):
        VerificationService.verify_email(current_user.id)
        flash("Email verified successfully! +50 coins earned", "success")
        
        # Check if stage 1 is complete
        VerificationService.complete_stage_1(current_user.id)
        
        return redirect(url_for("verification.stage1"))
    else:
        flash("Invalid or expired verification link.", "error")
        return redirect(url_for("verification.stage1"))

@verification_bp.route("/verification/stage1/aadhar", methods=["POST"])
@login_required
def verify_aadhar():
    """Verify Aadhar number"""
    aadhar = request.form.get("aadhar")
    
    # Basic Aadhar validation (12 digits)
    if not aadhar or len(aadhar) != 12 or not aadhar.isdigit():
        flash("Invalid Aadhar number. Must be 12 digits.", "error")
        return redirect(url_for("verification.stage1"))
    
    # In production, integrate with Aadhar verification API
    # For now, just mark as verified
    VerificationService.verify_aadhar(current_user.id, aadhar)
    flash("Aadhar verified successfully! +50 coins earned", "success")
    
    # Check if stage 1 is complete
    VerificationService.complete_stage_1(current_user.id)
    
    return redirect(url_for("verification.stage1"))

@verification_bp.route("/verification/stage1/username", methods=["POST"])
@login_required
def create_username():
    """Create username and digital ID"""
    username = request.form.get("username")
    
    if not username or len(username) < 3:
        flash("Username must be at least 3 characters long", "error")
        return redirect(url_for("verification.stage1"))
    
    # Check if username is available
    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != current_user.id:
        flash("Username already taken. Please choose another.", "error")
        return redirect(url_for("verification.stage1"))
    
    # Update username
    current_user.username = username
    
    # Create slug and digital ID
    slug = VerificationService.create_username_and_digital_id(current_user.id, username)
    
    db.session.commit()
    
    flash(f"Username created! Your coach page: koachsmart.com/coach/{slug}", "success")
    
    # Check if stage 1 is complete
    VerificationService.complete_stage_1(current_user.id)
    
    return redirect(url_for("verification.stage1"))

# ---------------------------
# Stage 2: Location & Availability (Purple Badge)
# ---------------------------
@verification_bp.route("/verification/stage2")
@login_required
def stage2():
    """Stage 2: Location and availability setup"""
    if current_user.role != "coach":
        return redirect(url_for("public.home"))
    
    stage = VerificationService.get_or_create_verification_stage(current_user.id)
    
    # Check if stage 1 is completed
    if not stage.stage_1_completed:
        flash("Please complete Stage 1 first", "warning")
        return redirect(url_for("verification.stage1"))
    
    return render_template("verification/stage2.html", stage=stage)

@verification_bp.route("/verification/stage2/location", methods=["POST"])
@login_required
def set_location():
    """Set coach location and preferences"""
    stage = VerificationService.get_or_create_verification_stage(current_user.id)
    
    # Get form data
    language = request.form.get("language")
    state = request.form.get("state")
    city = request.form.get("city")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    job_type = request.form.get("job_type")
    range_km = request.form.get("range_km")
    
    # Update verification stage
    if language:
        stage.language_selected = True
        stage.preferred_language = language
    
    if state:
        stage.state_selected = True
        current_user.profile.state = state
    
    if city:
        stage.city_selected = True
        current_user.profile.city = city
    
    if latitude and longitude:
        stage.location_mapped = True
        current_user.profile.latitude = float(latitude)
        current_user.profile.longitude = float(longitude)
    
    if job_type:
        stage.job_type_selected = True
        current_user.profile.working_type = job_type
    
    if range_km:
        stage.range_set = True
        current_user.profile.range_km = int(range_km)
    
    stage.serviceable_area_set = True
    stage.specific_location_set = True
    
    db.session.commit()
    
    # Check if stage 2 is complete
    if VerificationService.complete_stage_2(current_user.id):
        flash("Stage 2 completed! Purple Badge earned! +500 coins", "success")
    else:
        flash("Location preferences updated", "success")
    
    return redirect(url_for("verification.stage2"))

# ---------------------------
# Stage 3: Education & Experience (Blue Badge)
# ---------------------------
@verification_bp.route("/verification/stage3")
@login_required
def stage3():
    """Stage 3: Education and experience verification"""
    if current_user.role != "coach":
        return redirect(url_for("public.home"))
    
    stage = VerificationService.get_or_create_verification_stage(current_user.id)
    
    # Check if stage 2 is completed
    if not stage.stage_2_completed:
        flash("Please complete Stage 2 first", "warning")
        return redirect(url_for("verification.stage2"))
    
    documents = VerificationDocument.query.filter_by(user_id=current_user.id).all()
    
    return render_template("verification/stage3.html", stage=stage, documents=documents)

@verification_bp.route("/verification/stage3/education", methods=["POST"])
@login_required
def add_education():
    """Add education qualification"""
    stage = VerificationService.get_or_create_verification_stage(current_user.id)
    
    qualification = request.form.get("qualification")
    specialization = request.form.get("specialization")
    
    if qualification:
        stage.education_qualification_added = True
        # Store in profile or separate education table
        current_user.profile.certifications = qualification
    
    if specialization:
        stage.specialization_added = True
    
    db.session.commit()
    flash("Education details added", "success")
    
    return redirect(url_for("verification.stage3"))

@verification_bp.route("/verification/stage3/experience", methods=["POST"])
@login_required
def add_experience():
    """Add coaching experience"""
    stage = VerificationService.get_or_create_verification_stage(current_user.id)
    
    experience_years = request.form.get("experience_years")
    experience_details = request.form.get("experience_details")
    
    if experience_years:
        stage.experience_added = True
        current_user.profile.experience_years = int(experience_years)
        current_user.profile.bio = experience_details
    
    db.session.commit()
    flash("Experience details added", "success")
    
    # Check if stage 3 is complete
    if VerificationService.complete_stage_3(current_user.id):
        flash("Stage 3 completed! Blue Badge earned! +1000 coins", "success")
    
    return redirect(url_for("verification.stage3"))

# ---------------------------
# Stage 4: Certified Coach (Green Badge)
# ---------------------------
@verification_bp.route("/verification/stage4")
@login_required
def stage4():
    """Stage 4: Advanced certifications"""
    if current_user.role != "coach":
        return redirect(url_for("public.home"))
    
    stage = VerificationService.get_or_create_verification_stage(current_user.id)
    
    # Check if stage 3 is completed
    if not stage.stage_3_completed:
        flash("Please complete Stage 3 first", "warning")
        return redirect(url_for("verification.stage3"))
    
    return render_template("verification/stage4.html", stage=stage)

@verification_bp.route("/verification/stage4/certifications", methods=["POST"])
@login_required
def add_certifications():
    """Add advanced certifications"""
    stage = VerificationService.get_or_create_verification_stage(current_user.id)
    
    first_aid = request.form.get("first_aid")
    coaching_principles = request.form.get("coaching_principles")
    soft_skills = request.form.get("soft_skills")
    
    if first_aid:
        stage.first_aid_certified = True
        current_user.coins += VerificationService.ACTION_REWARDS['first_aid_certified']
    
    if coaching_principles:
        stage.coaching_principles_certified = True
        current_user.coins += VerificationService.ACTION_REWARDS['coaching_principles_certified']
    
    if soft_skills:
        stage.soft_skills_certified = True
        current_user.coins += VerificationService.ACTION_REWARDS['soft_skills_certified']
    
    db.session.commit()
    
    # Check if stage 4 is complete
    if VerificationService.complete_stage_4(current_user.id):
        flash("Stage 4 completed! Green Badge earned! +2000 coins", "success")
        flash("Congratulations! You are now a Certified Coach!", "success")
    else:
        flash("Certifications updated", "success")
    
    return redirect(url_for("verification.stage4"))

# ---------------------------
# Document Upload
# ---------------------------
@verification_bp.route("/verification/upload", methods=["POST"])
@login_required
def upload_document():
    """Upload verification document"""
    if 'document' not in request.files:
        flash("No file selected", "error")
        return redirect(request.referrer)
    
    file = request.files['document']
    document_type = request.form.get('document_type')
    
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(request.referrer)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Create upload directory
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'verification', str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Store in database
        doc = VerificationService.upload_verification_document(
            current_user.id,
            document_type,
            file_path,
            filename,
            os.path.getsize(file_path)
        )
        
        flash(f"{document_type.title()} document uploaded successfully", "success")
        
        return redirect(request.referrer)
    else:
        flash("Invalid file type. Please upload PDF, DOC, or image files.", "error")
        return redirect(request.referrer)

def allowed_file(filename):
    """Check if file type is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------
# Public Coach Profile (Slug Page)
# ---------------------------
@verification_bp.route("/coach/<slug>")
def public_coach_profile(slug):
    """Public coach profile page"""
    slug_page = CoachSlugPage.query.filter_by(slug=slug, is_active=True).first_or_404()
    user = User.query.get_or_404(slug_page.user_id)
    profile = user.profile
    stage = VerificationStage.query.filter_by(user_id=user.id).first()
    
    # Increment page views
    slug_page.page_views += 1
    if profile:
        profile.views += 1
    db.session.commit()
    
    return render_template(
        "verification/public_profile.html",
        user=user,
        profile=profile,
        stage=stage,
        slug_page=slug_page
    )

# ---------------------------
# API Endpoints
# ---------------------------
@verification_bp.route("/api/verification/progress")
@login_required
def api_verification_progress():
    """API endpoint for verification progress"""
    progress = VerificationService.get_verification_progress(current_user.id)
    return jsonify(progress)

@verification_bp.route("/api/verification/documents")
@login_required
def api_verification_documents():
    """API endpoint for user's verification documents"""
    documents = VerificationDocument.query.filter_by(user_id=current_user.id).all()
    
    docs_data = []
    for doc in documents:
        docs_data.append({
            'id': doc.id,
            'document_type': doc.document_type,
            'original_filename': doc.original_filename,
            'verification_status': doc.verification_status,
            'uploaded_at': doc.uploaded_at.isoformat(),
            'verified_at': doc.verified_at.isoformat() if doc.verified_at else None
        })
    
    return jsonify(docs_data)