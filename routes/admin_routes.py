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


# ---------------------------
# Coach Verification
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