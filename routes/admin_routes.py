from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, abort
)
from flask_login import login_required, current_user
from datetime import datetime

from core.extensions import db
from models.user import User
from models.profile import Profile
from models.job import Job
from models.application import Application
from models.hirer import Hirer, HirerReview
from services.reward_service import award_reward
from services.badge_service import assign_badge   # if you moved badge logic
from services.sheets_service import append_row
from core.access_guard import require_role

# ---------------------------
# Blueprint
# ---------------------------
admin_bp = Blueprint("admin", __name__)

# ---------------------------
# Admin Dashboard
# ---------------------------
@admin_bp.route("/super-admin")
@login_required
def super_admin():
    if current_user.role != "admin":
        flash("Unauthorized")
        return redirect(url_for("coach.dashboard"))

    pending_coaches = Profile.query.filter(
        Profile.cert_proof_path != None,
        Profile.is_verified == False
    ).all()

    return render_template(
        "super_admin.html",
        pending_coaches=pending_coaches,
        total_users=User.query.count(),
        total_coaches=User.query.filter_by(role="coach").count(),
        total_employers=User.query.filter_by(role="employer").count(),
        total_admins=User.query.filter_by(role="admin").count(),
        total_jobs=Job.query.count(),
        active_jobs=Job.query.filter_by(is_active=True).count(),
        total_applications=Application.query.count(),
        paying_users=User.query.filter(User.subscription_status != "free").count(),
    )


# ---------------------------
# Users
# ---------------------------
@admin_bp.route("/admin/users")
@login_required
def admin_users():
    require_role("admin")
    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/admin/user/<int:user_id>/role", methods=["POST"])
@login_required
def admin_change_role(user_id):
    require_role("admin")

    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")

    if new_role in ["coach", "employer", "admin"]:
        user.role = new_role
        db.session.commit()
        flash("Role updated")

    return redirect(url_for("admin.admin_users"))


# ---------------------------
# Jobs
# ---------------------------
@admin_bp.route("/admin/jobs")
@login_required
def admin_jobs():
    require_role("admin")
    jobs = Job.query.order_by(Job.posted_date.desc()).all()
    return render_template("admin_jobs.html", jobs=jobs)


# ---------------------------
# Hirer Review
# ---------------------------
@admin_bp.route("/admin/hirers")
@login_required
def admin_hirers():
    require_role("admin", "reviewer_l1", "reviewer_l2", "compliance")

    hirers = Hirer.query.order_by(Hirer.created_at.desc()).all()
    reviews = {r.hirer_id: r for r in HirerReview.query.all()}

    return render_template(
        "admin_hirer_review.html",
        hirers=hirers,
        reviews=reviews
    )


@admin_bp.route("/admin/hirer/<int:hirer_id>/review", methods=["POST"])
@login_required
def update_hirer_review(hirer_id):
    h = Hirer.query.get_or_404(hirer_id)
    hr = HirerReview.query.filter_by(hirer_id=hirer_id).first()

    if not hr:
        hr = HirerReview(hirer_id=hirer_id)
        db.session.add(hr)
        db.session.commit()

    action = request.form.get("action")
    status = request.form.get("status")
    note = request.form.get("note", "").strip()

    if action == "l1":
        require_role("admin", "reviewer_l1")
        hr.l1_status = status
        hr.l1_reviewer_id = current_user.id
        hr.l1_note = note
        hr.l1_at = datetime.utcnow()

    elif action == "l2":
        require_role("admin", "reviewer_l2")
        hr.l2_status = status
        hr.l2_reviewer_id = current_user.id
        hr.l2_note = note
        hr.l2_at = datetime.utcnow()

    elif action == "compliance":
        require_role("admin", "compliance")
        hr.compliance_status = status
        hr.compliance_reviewer_id = current_user.id
        hr.compliance_note = note
        hr.compliance_at = datetime.utcnow()

    elif action == "docs":
        require_role("admin", "reviewer_l1", "reviewer_l2", "compliance")
        hr.docs_address_proof = bool(request.form.get("docs_address_proof"))
        hr.docs_registration = bool(request.form.get("docs_registration"))
        hr.docs_website = bool(request.form.get("docs_website"))
        hr.docs_maps_link = bool(request.form.get("docs_maps_link"))

    else:
        abort(400)

    compute_final_status(hr, h)
    db.session.commit()

    try:
        append_row(
            spreadsheet_id=None,   # put your sheet id if needed
            sheet_name="Hirer_Review_Log!A2",
            values=[
                hr.hirer_id,
                h.institute_name,
                hr.l1_status,
                hr.l1_reviewer_id or "",
                hr.l1_at.isoformat() if hr.l1_at else "",
                hr.l2_status,
                hr.l2_reviewer_id or "",
                hr.l2_at.isoformat() if hr.l2_at else "",
                hr.compliance_status,
                hr.final_status,
                "Yes" if hr.ready_to_post else "No",
            ]
        )
    except Exception as e:
        print(f"[Sheets] Failed to append review log: {e}")

    flash("✅ Review updated.")
    return redirect(url_for("admin.admin_hirers"))


def compute_final_status(hr, h):
    """Compute final status based on all review levels"""
    # Check if all required reviews are completed
    l1_approved = hr.l1_status == "approved"
    l2_approved = hr.l2_status == "approved" 
    compliance_ok = hr.compliance_status in ["approved", "not_required"]
    
    # Check if all required documents are verified
    docs_complete = (hr.docs_address_proof and hr.docs_registration and 
                    hr.docs_website and hr.docs_maps_link)
    
    if l1_approved and l2_approved and compliance_ok and docs_complete:
        hr.final_status = "approved"
        hr.ready_to_post = True
    elif hr.l1_status == "rejected" or hr.l2_status == "rejected" or hr.compliance_status == "rejected":
        hr.final_status = "rejected"
        hr.ready_to_post = False
    else:
        hr.final_status = "pending"
        hr.ready_to_post = False


# ---------------------------
# Advanced Coach Verification System
# ---------------------------
@admin_bp.route("/admin/coach-verification")
@login_required
def admin_coach_verification():
    """Advanced multi-stage coach verification dashboard"""
    require_role("admin")
    
    from models.verification import VerificationStage, VerificationDocument
    
    # Get all coaches with verification stages
    coaches = db.session.query(User, VerificationStage, Profile).join(
        VerificationStage, User.id == VerificationStage.user_id, isouter=True
    ).join(
        Profile, User.id == Profile.user_id, isouter=True
    ).filter(User.role == "coach").all()
    
    # Get pending document verifications
    pending_docs = VerificationDocument.query.filter_by(verification_status="pending").all()
    
    return render_template(
        "admin_coach_verification.html",
        coaches=coaches,
        pending_docs=pending_docs
    )

@admin_bp.route("/admin/coach/<int:user_id>/verification", methods=["GET", "POST"])
@login_required
def admin_coach_verification_detail(user_id):
    """Detailed coach verification management"""
    require_role("admin")
    
    from models.verification import VerificationStage, VerificationDocument
    from services.verification_service import VerificationService
    
    user = User.query.get_or_404(user_id)
    stage = VerificationStage.query.filter_by(user_id=user_id).first()
    documents = VerificationDocument.query.filter_by(user_id=user_id).order_by(VerificationDocument.uploaded_at.desc()).all()
    progress = VerificationService.get_verification_progress(user_id)
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "approve_stage":
            stage_num = int(request.form.get("stage"))
            admin_notes = request.form.get("admin_notes", "")
            
            # Create or get verification stage
            if not stage:
                stage = VerificationService.get_or_create_verification_stage(user_id)
            
            # Approve the specific stage
            success = False
            if stage_num == 1:
                # Mark all Stage 1 requirements as completed
                stage.name_verified = True
                stage.phone_verified = True
                stage.email_verified = True
                stage.aadhar_verified = True
                stage.username_created = True
                stage.password_set = True
                stage.digital_id_created = True
                success = VerificationService.complete_stage_1(user_id)
            elif stage_num == 2:
                # Mark all Stage 2 requirements as completed
                stage.language_selected = True
                stage.state_selected = True
                stage.city_selected = True
                stage.location_mapped = True
                stage.serviceable_area_set = True
                stage.job_type_selected = True
                stage.specific_location_set = True
                stage.range_set = True
                success = VerificationService.complete_stage_2(user_id)
            elif stage_num == 3:
                # Mark all Stage 3 requirements as completed
                stage.education_qualification_added = True
                stage.specialization_added = True
                stage.education_document_uploaded = True
                stage.professional_certification_added = True
                stage.certification_document_uploaded = True
                stage.playing_level_added = True
                stage.playing_document_uploaded = True
                stage.experience_added = True
                success = VerificationService.complete_stage_3(user_id)
            elif stage_num == 4:
                # Mark all Stage 4 requirements as completed
                stage.first_aid_certified = True
                stage.coaching_principles_certified = True
                stage.soft_skills_certified = True
                stage.cv_uploaded = True
                stage.social_media_content_uploaded = True
                stage.aadhar_verification_complete = True
                stage.pcc_verified = True
                stage.noc_certified = True
                success = VerificationService.complete_stage_4(user_id)
            
            if success:
                db.session.commit()
                flash(f"Stage {stage_num} approved for {user.username}! Badge awarded and coins credited.", "success")
            else:
                flash(f"Error approving Stage {stage_num}. Please check requirements.", "error")
        
        elif action == "verify_document":
            doc_id = int(request.form.get("document_id"))
            status = request.form.get("status")
            notes = request.form.get("notes", "")
            
            doc = VerificationDocument.query.get(doc_id)
            if doc:
                doc.verification_status = status
                doc.verified_by = current_user.id
                doc.verification_notes = notes
                doc.verified_at = datetime.utcnow()
                db.session.commit()
                
                flash(f"Document {doc.document_type} {status}", "success")
        
        elif action == "reset_verification":
            # Reset all verification progress
            if stage:
                # Reset all stage completions and badges
                stage.stage_1_completed = False
                stage.stage_2_completed = False
                stage.stage_3_completed = False
                stage.stage_4_completed = False
                stage.orange_badge = False
                stage.purple_badge = False
                stage.blue_badge = False
                stage.green_badge = False
                
                # Reset all individual fields
                for field in ['name_verified', 'phone_verified', 'email_verified', 'aadhar_verified',
                             'username_created', 'password_set', 'digital_id_created',
                             'language_selected', 'state_selected', 'city_selected', 'location_mapped',
                             'serviceable_area_set', 'job_type_selected', 'specific_location_set', 'range_set',
                             'education_qualification_added', 'specialization_added', 'education_document_uploaded',
                             'professional_certification_added', 'certification_document_uploaded',
                             'playing_level_added', 'playing_document_uploaded', 'experience_added',
                             'first_aid_certified', 'coaching_principles_certified', 'soft_skills_certified',
                             'cv_uploaded', 'social_media_content_uploaded', 'aadhar_verification_complete',
                             'pcc_verified', 'noc_certified']:
                    setattr(stage, field, False)
                
                # Reset scores and coins
                stage.stage_1_score = 0
                stage.stage_2_score = 0
                stage.stage_3_score = 0
                stage.stage_4_score = 0
                stage.stage_1_coins = 0
                stage.stage_2_coins = 0
                stage.stage_3_coins = 0
                stage.stage_4_coins = 0
                
                db.session.commit()
                flash("Verification progress has been reset", "warning")
        
        return redirect(url_for("admin.admin_coach_verification_detail", user_id=user_id))
    
    return render_template(
        "admin_coach_verification_detail.html",
        user=user,
        stage=stage,
        documents=documents,
        progress=progress
    )

@admin_bp.route("/admin/document/<int:doc_id>/verify", methods=["POST"])
@login_required
def verify_document(doc_id):
    """Verify a specific document"""
    require_role("admin")
    
    from models.verification import VerificationDocument
    
    doc = VerificationDocument.query.get_or_404(doc_id)
    status = request.form.get("status")  # verified, rejected, pending
    notes = request.form.get("notes", "")
    
    # Update document status
    doc.verification_status = status
    doc.verified_by = current_user.id
    doc.verification_notes = notes
    doc.verified_at = datetime.utcnow()
    
    db.session.commit()
    
    # Return JSON response for AJAX calls
    if request.headers.get('Content-Type') == 'application/json' or request.is_json:
        return {
            'success': True,
            'message': f'Document {doc.document_type} {status}',
            'document_id': doc_id,
            'status': status
        }
    
    flash(f"Document {doc.document_type} {status}", "success")
    return redirect(request.referrer or url_for("admin.admin_coach_verification"))


# ---------------------------
# Coach Verification (Legacy)
# ---------------------------
@admin_bp.route("/verify-coach/<int:profile_id>")
@login_required
def verify_coach(profile_id):
    require_role("admin")

    profile = Profile.query.get_or_404(profile_id)
    user = User.query.get(profile.user_id)

    profile.is_verified = True
    user.education_verified = True
    db.session.commit()

    award_reward(user, action="education_verified", points=10)
    assign_badge(user.id, badge_field="education_verified")

    if user.onboarding_step == 3:
        user.onboarding_step = 4
        db.session.commit()

    flash("Coach education verified successfully.")
    return redirect(url_for("admin.super_admin"))


@admin_bp.route("/reject-coach/<int:profile_id>")
@login_required
def reject_coach(profile_id):
    require_role("admin")

    profile = Profile.query.get_or_404(profile_id)
    profile.cert_proof_path = None
    db.session.commit()

    return redirect(url_for("admin.super_admin"))