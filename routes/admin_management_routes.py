"""
Admin Management Routes
Handles Super Admin operations for managing regional admins
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime

from core.extensions import db
from models.user import User
from models.admin import Admin, AdminActivityLog
from core.access_guard import require_role

# Blueprint
admin_mgmt_bp = Blueprint("admin_mgmt", __name__, url_prefix="/admin-management")


# ============================================================================
# SUPER ADMIN DASHBOARD
# ============================================================================

@admin_mgmt_bp.route("/dashboard")
@login_required
def dashboard():
    """Admin dashboard - Super Admin or Regional Admin"""
    require_role("admin")
    
    # Get current admin
    admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not admin:
        flash("Admin profile not found", "error")
        return redirect(url_for("public.home"))
    
    if admin.role == "super_admin":
        # Super Admin Dashboard - All statistics
        total_admins = Admin.query.count()
        active_admins = Admin.query.filter_by(is_active=True).count()
        total_verifications = db.session.query(db.func.sum(Admin.total_verifications)).scalar() or 0
        total_approvals = db.session.query(db.func.sum(Admin.total_approvals)).scalar() or 0
        
        # Get recent activities
        recent_activities = AdminActivityLog.query.order_by(
            AdminActivityLog.created_at.desc()
        ).limit(10).all()
        
        # Get all admins
        admins = Admin.query.all()
        
        return render_template(
            "super_admin_dashboard.html",
            total_admins=total_admins,
            active_admins=active_admins,
            total_verifications=total_verifications,
            total_approvals=total_approvals,
            recent_activities=recent_activities,
            admins=admins
        )
    else:
        # Regional Admin Dashboard - Limited to their cities
        total_verifications = admin.total_verifications
        total_approvals = admin.total_approvals
        total_rejections = admin.total_rejections
        approval_rate = admin.get_approval_rate()
        
        # Get recent activities for this admin
        recent_activities = AdminActivityLog.query.filter_by(admin_id=admin.id).order_by(
            AdminActivityLog.created_at.desc()
        ).limit(10).all()
        
        return render_template(
            "admin_dashboard_regional.html",
            admin=admin,
            total_verifications=total_verifications,
            total_approvals=total_approvals,
            total_rejections=total_rejections,
            approval_rate=approval_rate,
            recent_activities=recent_activities,
            cities=admin.assigned_cities
        )


# ============================================================================
# ADMIN MANAGEMENT
# ============================================================================

@admin_mgmt_bp.route("/admins", methods=["GET"])
@login_required
def list_admins():
    """List all admins"""
    require_role("admin")
    
    admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not admin or admin.role != "super_admin":
        flash("Only Super Admin can access this page", "error")
        return redirect(url_for("public.home"))
    
    # Get filter parameters
    status_filter = request.args.get("status", "all")
    city_filter = request.args.get("city", "")
    
    # Build query
    query = Admin.query
    
    if status_filter == "active":
        query = query.filter_by(is_active=True)
    elif status_filter == "inactive":
        query = query.filter_by(is_active=False)
    
    admins = query.all()
    
    # Get unique cities
    cities = set()
    for admin in Admin.query.all():
        if admin.assigned_cities:
            cities.update(admin.assigned_cities)
    
    return render_template(
        "admin_list.html",
        admins=admins,
        cities=sorted(list(cities)),
        status_filter=status_filter,
        city_filter=city_filter
    )


@admin_mgmt_bp.route("/admin/create", methods=["GET", "POST"])
@login_required
def create_admin():
    """Create new admin"""
    require_role("admin")
    
    admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not admin or admin.role != "super_admin":
        flash("Only Super Admin can create admins", "error")
        return redirect(url_for("public.home"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        cities = request.form.getlist("cities")
        
        # Validation
        if not email or not name or not cities:
            flash("Email, name, and at least one city are required", "error")
            return redirect(url_for("admin_mgmt.create_admin"))
        
        # Check if email exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists", "error")
            return redirect(url_for("admin_mgmt.create_admin"))
        
        # Create user
        user = User(
            username=name.lower().replace(" ", "_"),
            email=email,
            password=generate_password_hash("temp_password_123"),  # Temporary password
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
        
        # Create admin profile
        new_admin = Admin(
            user_id=user.id,
            role="regional_admin",
            assigned_cities=cities
        )
        new_admin.generate_api_credentials()
        db.session.add(new_admin)
        db.session.commit()
        
        # Log activity
        admin.log_activity(
            action="create_admin",
            entity_type="admin",
            entity_id=new_admin.id,
            new_value={"email": email, "cities": cities}
        )
        
        flash(f"Admin created successfully! Email: {email}", "success")
        return redirect(url_for("admin_mgmt.list_admins"))
    
    return render_template("admin_create.html")


@admin_mgmt_bp.route("/admin/<int:admin_id>/edit", methods=["GET", "POST"])
@login_required
def edit_admin(admin_id):
    """Edit admin details and permissions"""
    require_role("admin")
    
    super_admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not super_admin or super_admin.role != "super_admin":
        flash("Only Super Admin can edit admins", "error")
        return redirect(url_for("public.home"))
    
    admin = Admin.query.get_or_404(admin_id)
    
    if request.method == "POST":
        # Update cities
        cities = request.form.getlist("cities")
        old_cities = admin.assigned_cities.copy() if admin.assigned_cities else []
        admin.assigned_cities = cities
        
        # Update permissions
        permissions = {
            'verify_coaches': request.form.get("verify_coaches") == "on",
            'approve_documents': request.form.get("approve_documents") == "on",
            'manage_admins': request.form.get("manage_admins") == "on",
            'view_analytics': request.form.get("view_analytics") == "on",
            'handle_appeals': request.form.get("handle_appeals") == "on",
            'send_notifications': request.form.get("send_notifications") == "on",
            'export_reports': request.form.get("export_reports") == "on"
        }
        admin.permissions = permissions
        
        db.session.commit()
        
        # Log activity
        super_admin.log_activity(
            action="edit_admin",
            entity_type="admin",
            entity_id=admin_id,
            old_value={"cities": old_cities},
            new_value={"cities": cities, "permissions": permissions}
        )
        
        flash("Admin updated successfully", "success")
        return redirect(url_for("admin_mgmt.list_admins"))
    
    return render_template("admin_edit.html", admin=admin)


@admin_mgmt_bp.route("/admin/<int:admin_id>/toggle", methods=["POST"])
@login_required
def toggle_admin_status(admin_id):
    """Toggle admin active/inactive status"""
    require_role("admin")
    
    super_admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not super_admin or super_admin.role != "super_admin":
        return jsonify({"error": "Unauthorized"}), 403
    
    admin = Admin.query.get_or_404(admin_id)
    old_status = admin.is_active
    admin.is_active = not admin.is_active
    db.session.commit()
    
    # Log activity
    super_admin.log_activity(
        action="toggle_admin_status",
        entity_type="admin",
        entity_id=admin_id,
        old_value={"is_active": old_status},
        new_value={"is_active": admin.is_active}
    )
    
    status = "activated" if admin.is_active else "deactivated"
    return jsonify({"success": True, "message": f"Admin {status}"}), 200


@admin_mgmt_bp.route("/admin/<int:admin_id>/delete", methods=["POST"])
@login_required
def delete_admin(admin_id):
    """Delete admin"""
    require_role("admin")
    
    super_admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not super_admin or super_admin.role != "super_admin":
        flash("Only Super Admin can delete admins", "error")
        return redirect(url_for("public.home"))
    
    admin = Admin.query.get_or_404(admin_id)
    
    # Log activity before deletion
    super_admin.log_activity(
        action="delete_admin",
        entity_type="admin",
        entity_id=admin_id,
        old_value={"email": admin.user.email, "cities": admin.assigned_cities}
    )
    
    # Delete admin profile
    db.session.delete(admin)
    
    # Delete user
    user = User.query.get(admin.user_id)
    if user:
        db.session.delete(user)
    
    db.session.commit()
    
    flash("Admin deleted successfully", "success")
    return redirect(url_for("admin_mgmt.list_admins"))


# ============================================================================
# ADMIN CREDENTIALS
# ============================================================================

@admin_mgmt_bp.route("/admin/<int:admin_id>/credentials", methods=["GET"])
@login_required
def view_credentials(admin_id):
    """View admin API credentials"""
    require_role("admin")
    
    super_admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not super_admin or super_admin.role != "super_admin":
        flash("Only Super Admin can view credentials", "error")
        return redirect(url_for("public.home"))
    
    admin = Admin.query.get_or_404(admin_id)
    
    return render_template("admin_credentials.html", admin=admin)


@admin_mgmt_bp.route("/admin/<int:admin_id>/credentials/regenerate", methods=["POST"])
@login_required
def regenerate_credentials(admin_id):
    """Regenerate API credentials"""
    require_role("admin")
    
    super_admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not super_admin or super_admin.role != "super_admin":
        return jsonify({"error": "Unauthorized"}), 403
    
    admin = Admin.query.get_or_404(admin_id)
    
    old_key = admin.api_key
    admin.generate_api_credentials()
    db.session.commit()
    
    # Log activity
    super_admin.log_activity(
        action="regenerate_credentials",
        entity_type="admin",
        entity_id=admin_id,
        old_value={"api_key": old_key},
        new_value={"api_key": admin.api_key}
    )
    
    return jsonify({
        "success": True,
        "api_key": admin.api_key,
        "api_secret": admin.api_secret
    }), 200


# ============================================================================
# ADMIN ACTIVITY
# ============================================================================

@admin_mgmt_bp.route("/admin/<int:admin_id>/activity", methods=["GET"])
@login_required
def admin_activity(admin_id):
    """View admin activity log"""
    require_role("admin")
    
    super_admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not super_admin or super_admin.role != "super_admin":
        flash("Only Super Admin can view activity", "error")
        return redirect(url_for("public.home"))
    
    admin = Admin.query.get_or_404(admin_id)
    
    # Get pagination
    page = request.args.get("page", 1, type=int)
    per_page = 20
    
    # Get activity logs
    activities = AdminActivityLog.query.filter_by(admin_id=admin_id).order_by(
        AdminActivityLog.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return render_template(
        "admin_activity.html",
        admin=admin,
        activities=activities
    )


# ============================================================================
# ADMIN PERFORMANCE
# ============================================================================

@admin_mgmt_bp.route("/admin/<int:admin_id>/performance", methods=["GET"])
@login_required
def admin_performance(admin_id):
    """View admin performance metrics"""
    require_role("admin")
    
    super_admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not super_admin or super_admin.role != "super_admin":
        flash("Only Super Admin can view performance", "error")
        return redirect(url_for("public.home"))
    
    admin = Admin.query.get_or_404(admin_id)
    
    # Calculate metrics
    approval_rate = admin.get_approval_rate()
    
    # Get recent activities
    recent_activities = AdminActivityLog.query.filter_by(admin_id=admin_id).order_by(
        AdminActivityLog.created_at.desc()
    ).limit(20).all()
    
    return render_template(
        "admin_performance.html",
        admin=admin,
        approval_rate=approval_rate,
        recent_activities=recent_activities
    )


# ============================================================================
# ADMIN REPORTS
# ============================================================================

@admin_mgmt_bp.route("/reports/admins", methods=["GET"])
@login_required
def admin_reports():
    """View admin reports and statistics"""
    require_role("admin")
    
    super_admin = Admin.query.filter_by(user_id=current_user.id).first()
    if not super_admin or super_admin.role != "super_admin":
        flash("Only Super Admin can view reports", "error")
        return redirect(url_for("public.home"))
    
    # Get all admins
    admins = Admin.query.all()
    
    # Calculate statistics
    total_admins = len(admins)
    active_admins = sum(1 for a in admins if a.is_active)
    total_verifications = sum(a.total_verifications for a in admins)
    total_approvals = sum(a.total_approvals for a in admins)
    total_rejections = sum(a.total_rejections for a in admins)
    
    # Calculate average approval rate
    total_decisions = total_approvals + total_rejections
    avg_approval_rate = (total_approvals / total_decisions * 100) if total_decisions > 0 else 0
    
    return render_template(
        "admin_reports.html",
        admins=admins,
        total_admins=total_admins,
        active_admins=active_admins,
        total_verifications=total_verifications,
        total_approvals=total_approvals,
        total_rejections=total_rejections,
        avg_approval_rate=avg_approval_rate
    )
