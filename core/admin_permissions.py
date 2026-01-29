"""
Admin Permission Middleware
Handles permission checking for admin operations
"""

from functools import wraps
from flask import redirect, url_for, flash, current_app
from flask_login import current_user
from models.admin import Admin


def require_admin_permission(permission):
    """
    Decorator to check if admin has specific permission
    
    Usage:
        @require_admin_permission('verify_coaches')
        def verify_coach():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in first", "error")
                return redirect(url_for("auth.login"))
            
            admin = Admin.query.filter_by(user_id=current_user.id).first()
            
            if not admin:
                flash("You don't have admin access", "error")
                return redirect(url_for("public.home"))
            
            if not admin.is_active:
                flash("Your admin account is inactive", "error")
                return redirect(url_for("public.home"))
            
            if not admin.has_permission(permission):
                flash(f"You don't have permission to {permission.replace('_', ' ')}", "error")
                return redirect(url_for("public.home"))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_super_admin(f):
    """
    Decorator to check if user is super admin
    
    Usage:
        @require_super_admin
        def manage_admins():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first", "error")
            return redirect(url_for("auth.login"))
        
        admin = Admin.query.filter_by(user_id=current_user.id).first()
        
        if not admin or admin.role != "super_admin":
            flash("Only Super Admin can access this page", "error")
            return redirect(url_for("public.home"))
        
        if not admin.is_active:
            flash("Your admin account is inactive", "error")
            return redirect(url_for("public.home"))
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_regional_admin(f):
    """
    Decorator to check if user is regional admin or super admin
    
    Usage:
        @require_regional_admin
        def verify_coaches():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first", "error")
            return redirect(url_for("auth.login"))
        
        admin = Admin.query.filter_by(user_id=current_user.id).first()
        
        if not admin or admin.role not in ["super_admin", "regional_admin"]:
            flash("You don't have admin access", "error")
            return redirect(url_for("public.home"))
        
        if not admin.is_active:
            flash("Your admin account is inactive", "error")
            return redirect(url_for("public.home"))
        
        return f(*args, **kwargs)
    
    return decorated_function


def check_city_access(city):
    """
    Check if current admin can access specific city
    
    Usage:
        if not check_city_access('Mumbai'):
            flash("You don't have access to this city", "error")
            return redirect(url_for("public.home"))
    """
    if not current_user.is_authenticated:
        return False
    
    admin = Admin.query.filter_by(user_id=current_user.id).first()
    
    if not admin or not admin.is_active:
        return False
    
    return admin.can_access_city(city)


def get_admin_cities():
    """
    Get list of cities current admin can access
    
    Usage:
        cities = get_admin_cities()
    """
    if not current_user.is_authenticated:
        return []
    
    admin = Admin.query.filter_by(user_id=current_user.id).first()
    
    if not admin:
        return []
    
    if admin.role == "super_admin":
        # Super admin can access all cities
        return ['Mumbai', 'Pune', 'Nagpur', 'Aurangabad', 'Nashik', 'Kolhapur', 'Solapur', 'Amravati']
    
    return admin.assigned_cities or []


def log_admin_action(action, entity_type, entity_id, old_value=None, new_value=None, ip_address=None):
    """
    Log admin action for audit trail
    
    Usage:
        log_admin_action(
            action='verify_document',
            entity_type='coach',
            entity_id=123,
            old_value={'status': 'pending'},
            new_value={'status': 'verified'}
        )
    """
    if not current_user.is_authenticated:
        return False
    
    admin = Admin.query.filter_by(user_id=current_user.id).first()
    
    if not admin:
        return False
    
    try:
        admin.log_activity(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
        return True
    except Exception as e:
        current_app.logger.error(f"Error logging admin action: {str(e)}")
        return False
