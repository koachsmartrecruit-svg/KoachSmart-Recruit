import os
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, current_app, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import random
import string

from core.extensions import db

# ---------------------------
# Validators
# ---------------------------
from validators.phone_validator import is_valid_indian_phone
from validators.address_validator import is_valid_pincode
from validators.document_validator import is_allowed_file

# ---------------------------
# Models
# ---------------------------
from models.profile import Profile
from models.hirer import Hirer, HirerReview
from models.user import User

# ---------------------------
# Services
# ---------------------------
from services.otp_service import send_mobile_otp, send_email_otp_service, verify_otp
from services.email_service import send_welcome_email
from services.reward_service import award_reward
from services.referral_service import award_referral_bonus

# ---------------------------
# Blueprint
# ---------------------------
onboarding_bp = Blueprint("onboarding", __name__)

# Language options
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'हिंदी (Hindi)',
    'mr': 'मराठी (Marathi)',
    'ta': 'தமிழ் (Tamil)',
    'te': 'తెలుగు (Telugu)',
    'gu': 'ગુજરાતી (Gujarati)',
    'kn': 'ಕನ್ನಡ (Kannada)',
    'bn': 'বাংলা (Bengali)',
    'ml': 'മലയാളം (Malayalam)',
    'pa': 'ਪੰਜਾਬੀ (Punjabi)'
}

# Sports options
SPORTS_OPTIONS = [
    'Cricket', 'Football', 'Basketball', 'Badminton', 'Tennis', 
    'Swimming', 'Athletics', 'Volleyball', 'Hockey', 'Table Tennis',
    'Boxing', 'Wrestling', 'Kabaddi', 'Kho Kho', 'Chess'
]

# Education levels with scoring
EDUCATION_LEVELS = {
    'below_10': {'name': 'Below 10th', 'score': 1},
    '10th': {'name': '10th Pass', 'score': 1},
    '12th': {'name': '12th Pass', 'score': 2},
    'diploma': {'name': 'Diploma', 'score': 3},
    'graduate': {'name': 'Graduate', 'score': 3},
    'postgraduate': {'name': 'Post Graduate', 'score': 4},
    'masters': {'name': 'Masters', 'score': 4},
    'phd': {'name': 'PhD', 'score': 5}
}

# Experience levels
EXPERIENCE_LEVELS = [
    'fresher', '0-1 years', '1-3 years', '3-5 years', '5+ years'
]

def generate_username(full_name):
    """Generate a unique username from full name"""
    if not full_name:
        return None
    
    # Create base username from name
    base = full_name.lower().replace(' ', '-')
    base = ''.join(c for c in base if c.isalnum() or c == '-')
    
    # Check if unique
    if not User.query.filter_by(username=base).first():
        return base
    
    # Add random suffix if not unique
    for i in range(1, 100):
        username = f"{base}-{i}"
        if not User.query.filter_by(username=username).first():
            return username
    
    # Fallback with random string
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"{base}-{random_suffix}"

def award_coins(user, amount, reason):
    """Award coins to user"""
    if not hasattr(user, 'coins') or user.coins is None:
        user.coins = 0
    user.coins += amount
    db.session.commit()
    flash(f"🪙 You earned {amount} coins! {reason}", "success")

def assign_badge(user, badge_name):
    """Assign badge to user"""
    if not hasattr(user, 'badges') or user.badges is None:
        user.badges = ""
    
    if badge_name not in user.badges:
        user.badges = f"{user.badges},{badge_name}" if user.badges else badge_name
        db.session.commit()
        flash(f"🏆 You earned the {badge_name} badge!", "success")

# =============================================================================
# Coach Onboarding - Comprehensive Multi-Stage Verification System
# =============================================================================

@onboarding_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding_unified():
    """Comprehensive Coach Onboarding with Language Support and Badge System"""
    
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))

    # Initialize profile if not exists
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    # Get current step from user or default to 1
    current_step = getattr(current_user, 'onboarding_step', 1) or 1
    
    # If already completed, redirect to dashboard
    if getattr(current_user, 'onboarding_completed', False):
        flash("You have already completed onboarding!", "info")
        return redirect(url_for("coach.dashboard"))

    # Handle language selection first
    if request.method == "POST" and 'language' in request.form:
        selected_language = request.form.get('language')
        if selected_language in SUPPORTED_LANGUAGES:
            session['user_language'] = selected_language
            flash(f"Language set to {SUPPORTED_LANGUAGES[selected_language]}", "success")
        return redirect(url_for("onboarding.onboarding_unified"))

    # Get user's selected language
    user_language = session.get('user_language', 'en')

    if request.method == "POST":
        # Handle different form submissions based on current step
        if current_step == 1:
            return handle_stage1_submission(profile)
        elif current_step == 2:
            return handle_stage2_submission(profile)
        elif current_step == 3:
            return handle_stage3_submission(profile)

    # Calculate progress and badges
    progress = calculate_onboarding_progress(current_user, profile)
    
    return render_template(
        "onboarding_comprehensive.html",
        current_step=current_step,
        profile=profile,
        progress=progress,
        languages=SUPPORTED_LANGUAGES,
        user_language=user_language,
        sports_options=SPORTS_OPTIONS,
        education_levels=EDUCATION_LEVELS,
        experience_levels=EXPERIENCE_LEVELS
    )

def handle_stage1_submission(profile):
    """Handle Stage 1: Basic Information & Verification"""
    
    # Basic Information
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    phone = request.form.get("phone", "").strip()
    aadhar = request.form.get("aadhar", "").strip()
    sport1 = request.form.get("sport1", "").strip()
    sport2 = request.form.get("sport2", "").strip()
    languages = request.form.getlist("languages")
    
    # Validation
    if not first_name or not last_name or not phone:
        flash("Name and phone number are required.", "error")
        return redirect(url_for("onboarding.onboarding_unified"))
    
    if not is_valid_indian_phone(phone):
        flash("Invalid phone number format", "error")
        return redirect(url_for("onboarding.onboarding_unified"))
    
    # Handle OTP verification
    if 'verify_phone' in request.form:
        result = send_mobile_otp(phone)
        if result['success']:
            flash("📱 Demo OTP sent! Use 123456 for verification.", "success")
        else:
            flash(f"❌ {result['message']}", "error")
        return redirect(url_for("onboarding.onboarding_unified"))
    
    if 'verify_email' in request.form:
        result = send_email_otp_service(current_user.email)
        if result['success']:
            flash("📧 OTP sent to your email!", "success")
        else:
            flash(f"❌ {result['message']}", "error")
        return redirect(url_for("onboarding.onboarding_unified"))
    
    # Process main form submission
    phone_otp = request.form.get("phone_otp", "").strip()
    email_otp = request.form.get("email_otp", "").strip()
    
    # Verify OTPs (both phone and email use 123456 for demo)
    phone_verified = False
    email_verified = False
    
    if phone_otp:
        if phone_otp == "123456" or verify_otp(phone, phone_otp):
            phone_verified = True
        else:
            flash("❌ Invalid phone OTP. Use 123456 for demo.", "error")
            return redirect(url_for("onboarding.onboarding_unified"))
    
    if email_otp:
        if email_otp == "123456" or verify_otp(current_user.email, email_otp):
            email_verified = True
        else:
            flash("❌ Invalid email OTP. Use 123456 for demo.", "error")
            return redirect(url_for("onboarding.onboarding_unified"))
    
    # Language proficiency levels
    language_proficiency = request.form.getlist("language_proficiency")
    
    # Update profile
    full_name = f"{first_name} {last_name}"
    profile.full_name = full_name
    profile.phone = phone
    profile.aadhar_number = aadhar
    profile.sport = sport1
    profile.sport2 = sport2
    
    # Store languages with proficiency levels
    if languages and language_proficiency:
        language_data = []
        for i, lang in enumerate(languages):
            proficiency = language_proficiency[i] if i < len(language_proficiency) else 'basic'
            language_data.append(f"{lang}:{proficiency}")
        profile.languages = ",".join(language_data)
    else:
        profile.languages = ",".join(languages) if languages else ""
    
    # Generate username
    username = generate_username(full_name)
    if username:
        current_user.username = username
    
    # Mark verifications
    if phone_verified:
        current_user.phone_verified = True
        award_coins(current_user, 50, "Phone verification completed!")
    
    if email_verified:
        current_user.email_verified = True
        award_coins(current_user, 50, "Email verification completed!")
    
    if aadhar:
        current_user.aadhar_verified = True
        award_coins(current_user, 50, "Aadhar verification completed!")
    
    # Award Orange Badge if basic info is complete
    if phone_verified and full_name and sport1:
        assign_badge(current_user, "Orange Badge")
        award_coins(current_user, 100, "Orange Badge earned!")
        
        # Create slug-based public page
        slug = username or full_name.lower().replace(' ', '-')
        profile.public_slug = slug
        
        flash("🎉 Congratulations! You earned the Orange Badge and 100 coins!", "success")
        flash("📄 Your public profile is now available!", "info")
    
    # Move to next step
    current_user.onboarding_step = 2
    db.session.commit()
    
    return redirect(url_for("onboarding.onboarding_unified"))

def handle_stage2_submission(profile):
    """Handle Stage 2: Location & Service Details"""
    
    state = request.form.get("state", "").strip()
    city = request.form.get("city", "").strip()
    location = request.form.get("location", "").strip()
    job_type = request.form.getlist("job_type")
    specific_locations = request.form.getlist("specific_locations")
    range_km = request.form.get("range_km", "").strip()
    
    # Only store range for part-time and full-time jobs
    store_range = any(jt in ['part_time', 'full_time'] for jt in job_type)
    
    if not state or not city:
        flash("State and city are required.", "error")
        return redirect(url_for("onboarding.onboarding_unified"))
    
    # Update profile
    profile.state = state
    profile.city = city
    profile.location = location
    profile.job_types = ",".join(job_type) if job_type else ""
    profile.specific_locations = ",".join(specific_locations) if specific_locations else ""
    
    # Only set range for part-time and full-time
    if store_range and range_km.isdigit():
        profile.range_km = int(range_km)
    elif not store_range:
        profile.range_km = None  # Clear range for session-based jobs
    
    # Award Purple Badge
    assign_badge(current_user, "Purple Badge")
    award_coins(current_user, 200, "Purple Badge earned for location setup!")
    
    # Move to next step
    current_user.onboarding_step = 3
    db.session.commit()
    
    flash("🟣 Purple Badge earned! You're getting closer to verification!", "success")
    return redirect(url_for("onboarding.onboarding_unified"))

def handle_stage3_submission(profile):
    """Handle Stage 3: Education & Professional Verification"""
    
    education = request.form.get("education", "").strip()
    specialization = request.form.get("specialization", "").strip()
    has_professional_cert = request.form.get("has_professional_cert") == "yes"
    cert_name = request.form.get("cert_name", "").strip()
    playing_level = request.form.get("playing_level", "").strip()
    experience = request.form.get("experience", "").strip()
    
    # Handle file uploads
    education_doc = request.files.get("education_doc")
    cert_doc = request.files.get("cert_doc")
    playing_doc = request.files.get("playing_doc")
    
    if not education:
        flash("Education qualification is required.", "error")
        return redirect(url_for("onboarding.onboarding_unified"))
    
    # Update profile
    profile.education = education
    profile.specialization = specialization
    profile.has_professional_cert = has_professional_cert
    profile.cert_name = cert_name
    profile.playing_level = playing_level
    profile.experience_years = experience
    
    # Handle document uploads
    if education_doc and is_allowed_file(education_doc.filename):
        filename = secure_filename(f"edu_{current_user.id}_{education_doc.filename}")
        education_doc.save(os.path.join(current_app.config["CERT_FOLDER"], filename))
        profile.education_doc_path = filename
    
    if cert_doc and is_allowed_file(cert_doc.filename):
        filename = secure_filename(f"cert_{current_user.id}_{cert_doc.filename}")
        cert_doc.save(os.path.join(current_app.config["CERT_FOLDER"], filename))
        profile.cert_doc_path = filename
    
    if playing_doc and is_allowed_file(playing_doc.filename):
        filename = secure_filename(f"play_{current_user.id}_{playing_doc.filename}")
        playing_doc.save(os.path.join(current_app.config["CERT_FOLDER"], filename))
        profile.playing_doc_path = filename
    
    # Calculate education score and award coins
    if education in EDUCATION_LEVELS:
        score = EDUCATION_LEVELS[education]['score']
        coins = score * 50
        award_coins(current_user, coins, f"Education verification: {EDUCATION_LEVELS[education]['name']}")
    
    # Award Blue Verified Badge
    assign_badge(current_user, "Blue Verified Badge")
    award_coins(current_user, 500, "Blue Verified Badge earned!")
    
    # Complete onboarding
    current_user.onboarding_completed = True
    current_user.onboarding_completed_at = datetime.utcnow()
    
    # Award referral bonus if user was referred
    if hasattr(current_user, 'referred_by') and current_user.referred_by:
        try:
            award_referral_bonus(current_user.referred_by, 'orange_completion')
        except Exception as e:
            current_app.logger.error(f"Error awarding referral bonus: {str(e)}")
    
    db.session.commit()
    
    flash("🔵 Congratulations! You earned the Blue Verified Badge!", "success")
    flash("🎉 Onboarding completed! Parents can now discover you!", "success")
    flash("💼 You now have access to premium features!", "info")
    
    return redirect(url_for("coach.dashboard"))

def calculate_onboarding_progress(user, profile):
    """Calculate onboarding progress and badges"""
    progress = {
        'current_step': getattr(user, 'onboarding_step', 1) or 1,
        'total_steps': 3,
        'coins': getattr(user, 'coins', 0) or 0,
        'badges': getattr(user, 'badges', '').split(',') if getattr(user, 'badges', '') else [],
        'phone_verified': getattr(user, 'phone_verified', False),
        'email_verified': getattr(user, 'email_verified', False),
        'aadhar_verified': getattr(user, 'aadhar_verified', False),
        'username': getattr(user, 'username', ''),
        'public_slug': getattr(profile, 'public_slug', '') if profile else ''
    }
    
    # Calculate percentage
    step = progress['current_step']
    progress['percentage'] = min(((step - 1) / 3) * 100, 100)
    
    return progress

# AJAX endpoints for OTP (kept for compatibility)
@onboarding_bp.route("/send-phone-otp", methods=["POST"])
@login_required
def send_phone_otp_ajax():
    """AJAX endpoint for sending phone OTP"""
    try:
        phone = request.form.get("phone", "").strip()
        
        if not is_valid_indian_phone(phone):
            return jsonify({
                'success': False,
                'message': 'Invalid phone number format'
            })
        
        result = send_mobile_otp(phone)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error in send_phone_otp_ajax: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to send phone OTP. Please try again.'
        })

@onboarding_bp.route("/send-email-otp", methods=["POST"])
@login_required
def send_email_otp_ajax():
    """AJAX endpoint for sending email OTP"""
    try:
        result = send_email_otp_service(current_user.email)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error in send_email_otp_ajax: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to send email OTP. Please try again.'
        })

# =============================================================================
# Public Coach Profile (Slug-based)
# =============================================================================
@onboarding_bp.route("/coach/<slug>")
def public_coach_profile(slug):
    """Public coach profile page accessible via slug"""
    profile = Profile.query.filter_by(public_slug=slug).first()
    if not profile:
        flash("Coach profile not found.", "error")
        return redirect(url_for("public.home"))
    
    user = User.query.get(profile.user_id)
    if not user or not user.onboarding_completed:
        flash("Coach profile not available.", "error")
        return redirect(url_for("public.home"))
    
    return render_template(
        "verification/public_profile.html",
        user=user,
        profile=profile
    )

# =============================================================================
# Employer Onboarding (kept as is)
# =============================================================================
@onboarding_bp.route("/hirer/onboarding", methods=["GET", "POST"])
@login_required
def hirer_onboarding():

    if current_user.role != "employer":
        flash("Unauthorized")
        return redirect(url_for("coach.dashboard"))

    if not current_user.employer_onboarding_step:
        current_user.employer_onboarding_step = 1
        db.session.commit()

    current_step = current_user.employer_onboarding_step
    session.setdefault("hirer_onboarding", {})
    data = session["hirer_onboarding"]

    if request.method == "POST":

        # STEP 1 – Basic Details
        if current_step == 1:
            institute = request.form.get("institute_name", "").strip()
            contact_person = request.form.get("contact_person_name", "").strip()
            phone = request.form.get("contact_number", "").strip()
            alternate_number = request.form.get("alternate_number", "").strip()

            if not institute or not contact_person or not is_valid_indian_phone(phone):
                flash("Institute name, contact person name, and valid phone number are required.")
                return redirect(url_for("onboarding.hirer_onboarding"))

            data.update({
                "institute_name": institute,
                "contact_person_name": contact_person,
                "contact_number": phone,
                "alternate_number": alternate_number
            })

            session["hirer_onboarding"] = data
            current_user.employer_onboarding_step = 2
            db.session.commit()

        # STEP 2 – Business Details
        elif current_step == 2:
            business_type = request.form.get("business_type", "").strip()
            gst_number = request.form.get("gst_number", "").strip()
            years_active = request.form.get("years_active", "").strip()
            
            # Handle file uploads
            gst_doc = request.files.get("gst_doc")
            reg_doc = request.files.get("registration_doc")
            owner_id_doc = request.files.get("owner_id_doc")

            if not business_type:
                flash("Business type is required.")
                return redirect(url_for("onboarding.hirer_onboarding"))

            data.update({
                "business_type": business_type,
                "gst_number": gst_number,
                "years_active": int(years_active) if years_active else None
            })

            # Handle file uploads
            if gst_doc and is_allowed_file(gst_doc.filename):
                filename = secure_filename(f"gst_{current_user.id}_{gst_doc.filename}")
                gst_doc.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                data["gst_doc_path"] = filename

            if reg_doc and is_allowed_file(reg_doc.filename):
                filename = secure_filename(f"reg_{current_user.id}_{reg_doc.filename}")
                reg_doc.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                data["registration_doc_path"] = filename

            if owner_id_doc and is_allowed_file(owner_id_doc.filename):
                filename = secure_filename(f"id_{current_user.id}_{owner_id_doc.filename}")
                owner_id_doc.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                data["owner_id_doc_path"] = filename

            session["hirer_onboarding"] = data
            current_user.employer_onboarding_step = 3
            db.session.commit()

        # STEP 3 – Location
        elif current_step == 3:
            address_full = request.form.get("address_full", "").strip()
            city = request.form.get("city", "").strip()
            state = request.form.get("state", "").strip()
            country = request.form.get("country", "").strip()
            pincode = request.form.get("pincode", "").strip()
            latitude = request.form.get("latitude", "").strip()
            longitude = request.form.get("longitude", "").strip()

            if not address_full or not city or not state or not is_valid_pincode(pincode):
                flash("Address, city, state, and valid pincode are required.")
                return redirect(url_for("onboarding.hirer_onboarding"))

            data.update({
                "address_full": address_full,
                "city": city,
                "state": state,
                "country": country or "India",
                "pincode": pincode,
                "latitude": float(latitude) if latitude else None,
                "longitude": float(longitude) if longitude else None
            })

            session["hirer_onboarding"] = data
            current_user.employer_onboarding_step = 4
            db.session.commit()

        # STEP 4 – Final Save
        elif current_step == 4:
            hiring_mode = request.form.get("hiring_mode", "").strip()
            hiring_count = request.form.get("hiring_count", "").strip()
            google_maps_link = request.form.get("google_maps_link", "").strip()
            notes = request.form.get("notes", "").strip()

            if not hiring_mode:
                flash("Hiring mode is required.")
                return redirect(url_for("onboarding.hirer_onboarding"))

            # Update data with final step info
            data.update({
                "hiring_mode": hiring_mode,
                "hiring_count": int(hiring_count) if hiring_count else None,
                "google_maps_link": google_maps_link,
                "notes": notes
            })

            hirer = Hirer(
                institute_name=data.get("institute_name") or "Unknown Institute",
                contact_person_name=data.get("contact_person_name") or "Unknown Contact",
                contact_number=data.get("contact_number") or "0000000000",
                alternate_number=data.get("alternate_number"),
                email=current_user.email,
                business_type=data.get("business_type") or "Academy",
                gst_number=data.get("gst_number"),
                years_active=data.get("years_active"),
                address_full=data.get("address_full") or "Address not provided",
                city=data.get("city") or "Unknown City",
                state=data.get("state") or "Unknown State",
                country=data.get("country", "India"),
                pincode=data.get("pincode") or "000000",
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                hiring_mode=data.get("hiring_mode"),
                hiring_count=data.get("hiring_count"),
                google_maps_link=data.get("google_maps_link"),
                notes=data.get("notes"),
                gst_doc_path=data.get("gst_doc_path"),
                registration_doc_path=data.get("registration_doc_path"),
                owner_id_doc_path=data.get("owner_id_doc_path"),
                phone_otp_status="Verified",
                email_otp_status="Verified",
            )

            db.session.add(hirer)
            db.session.commit()

            db.session.add(HirerReview(hirer_id=hirer.id))
            db.session.commit()

            current_user.employer_onboarding_completed = True
            session.pop("hirer_onboarding", None)
            db.session.commit()

            flash("🎉 Employer onboarding completed!")
            return redirect(url_for("employer.dashboard"))

        return redirect(url_for("onboarding.hirer_onboarding"))

    return render_template(
        "hirer_onboarding.html",
        current_step=current_step,
        data=data
    )