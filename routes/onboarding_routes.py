import os
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

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

# ---------------------------
# Services
# ---------------------------
from services.otp_service import generate_otp, save_otp, verify_otp
from services.email_service import send_otp_email
from services.reward_service import award_reward
from services.referral_service import award_referral_bonus
from services.badge_service import assign_badge   # create if missing

# ---------------------------
# Blueprint
# ---------------------------
onboarding_bp = Blueprint("onboarding", __name__)

# =============================================================================
# Coach Onboarding
# =============================================================================
@onboarding_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding_unified():
    if current_user.role != "coach":
        return redirect(url_for("employer.dashboard"))

    profile = Profile.query.filter_by(user_id=current_user.id).first()
    current_step = current_user.onboarding_step or 1

    # ---------------------------
    # STEP 1 – OTP Verification
    # ---------------------------
    if current_step == 1 and request.method == "POST":

        if "send_phone_otp" in request.form:
            phone = request.form.get("phone", "").strip()
            if is_valid_indian_phone(phone):
                otp = generate_otp()
                save_otp(phone, otp)
                flash("📱 OTP sent to your phone!")
            else:
                flash("Invalid phone number")
            return redirect(url_for("onboarding.onboarding_unified"))

        if "send_email_otp" in request.form:
            otp = generate_otp()
            save_otp(current_user.email, otp)
            send_otp_email(current_user.email, otp)
            flash("📧 OTP sent to your email!")
            return redirect(url_for("onboarding.onboarding_unified"))

        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        phone = request.form.get("phone", "").strip()
        phone_otp = request.form.get("phone_otp", "").strip()
        email_otp = request.form.get("email_otp", "").strip()

        if not first_name or not last_name or not phone:
            flash("All fields required.")
            return redirect(url_for("onboarding.onboarding_unified"))

        if not verify_otp(phone, phone_otp):
            flash("Invalid phone OTP")
            return redirect(url_for("onboarding.onboarding_unified"))

        if not verify_otp(current_user.email, email_otp):
            flash("Invalid email OTP")
            return redirect(url_for("onboarding.onboarding_unified"))

        profile.full_name = f"{first_name} {last_name}"
        profile.phone = phone
        current_user.onboarding_step = 2

        award_reward(current_user, action="phone_verified", points=5)
        assign_badge(current_user.id, "phone_verified")

        db.session.commit()
        return redirect(url_for("onboarding.onboarding_unified"))

    # ---------------------------
    # STEP 2 – Location
    # ---------------------------
    elif current_step == 2 and request.method == "POST":
        state = request.form.get("state")
        city = request.form.get("city")
        travel_range = request.form.get("travel_range")

        if not state or not city or not travel_range:
            flash("Location fields required.")
            return redirect(url_for("onboarding.onboarding_unified"))

        profile.city = f"{city}, {state}"
        profile.travel_range = travel_range
        current_user.onboarding_step = 3

        award_reward(current_user, action="location_verified", points=20)
        assign_badge(current_user.id, "location_verified")

        db.session.commit()
        return redirect(url_for("onboarding.onboarding_unified"))

    # ---------------------------
    # STEP 3 – Education Upload
    # ---------------------------
    elif current_step == 3 and request.method == "POST":
        cert_file = request.files.get("certificate")

        if not cert_file or not is_allowed_file(cert_file.filename):
            flash("Valid certificate required.")
            return redirect(url_for("onboarding.onboarding_unified"))

        filename = secure_filename(f"edu_{current_user.id}_{cert_file.filename}")
        path = os.path.join(current_app.config["CERT_FOLDER"], filename)
        cert_file.save(path)

        profile.cert_proof_path = filename
        current_user.onboarding_step = 4

        db.session.commit()
        return redirect(url_for("onboarding.onboarding_unified"))

    # ---------------------------
    # STEP 4 – Optional Sports Cert
    # ---------------------------
    elif current_step == 4 and request.method == "POST":
        cert_file = request.files.get("certificate")

        if cert_file and is_allowed_file(cert_file.filename):
            filename = secure_filename(f"sport_{current_user.id}_{cert_file.filename}")
            path = os.path.join(current_app.config["EXP_PROOF_FOLDER"], filename)
            cert_file.save(path)
            profile.experience_proof_path = filename
            db.session.commit()

        current_user.onboarding_step = 5
        db.session.commit()
        return redirect(url_for("onboarding.onboarding_unified"))

    # ---------------------------
    # STEP 5 – Final Preferences
    # ---------------------------
    elif current_step == 5 and request.method == "POST":
        profile.sport_primary = request.form.get("sport")
        profile.working_type = request.form.get("working_type")
        profile.range_km = int(request.form.get("range_km") or 0)

        current_user.onboarding_completed = True
        award_referral_bonus(current_user.id)

        db.session.commit()
        flash("🎉 Onboarding completed!")
        return redirect(url_for("coach.dashboard"))

    return render_template(
        "onboarding_unified.html",
        profile=profile,
        current_step=current_step
    )


# =============================================================================
# Employer Onboarding
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

            # Debug: Print session data to see what's available
            print("DEBUG - Session data:", data)

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
