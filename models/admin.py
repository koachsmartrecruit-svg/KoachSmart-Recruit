"""
Admin Management Models
Handles Super Admin and Regional Admin roles with activity tracking
"""

from core.extensions import db
from datetime import datetime
import secrets
import string


class Admin(db.Model):
    """Admin user with role hierarchy and city assignment"""
    __tablename__ = "admin"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    
    # Role: 'super_admin' or 'regional_admin'
    role = db.Column(db.String(50), nullable=False, default="regional_admin")
    
    # City Assignment (JSON array for regional admins)
    assigned_cities = db.Column(db.JSON, default=[])  # ['Mumbai', 'Pune', 'Nagpur']
    
    # Permissions (JSON object)
    permissions = db.Column(db.JSON, default={
        'verify_coaches': True,
        'approve_documents': True,
        'manage_admins': False,
        'view_analytics': True,
        'handle_appeals': True,
        'send_notifications': True,
        'export_reports': True
    })
    
    # API Credentials
    api_key = db.Column(db.String(255), unique=True, nullable=True)
    api_secret = db.Column(db.String(255), nullable=True)
    
    # Activity Tracking
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    total_verifications = db.Column(db.Integer, default=0)
    total_approvals = db.Column(db.Integer, default=0)
    total_rejections = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="admin_profile")
    activity_logs = db.relationship("AdminActivityLog", backref="admin", cascade="all, delete-orphan")
    
    def generate_api_credentials(self):
        """Generate API key and secret for admin"""
        self.api_key = f"admin_{secrets.token_urlsafe(32)}"
        self.api_secret = secrets.token_urlsafe(64)
        return self.api_key, self.api_secret
    
    def has_permission(self, permission):
        """Check if admin has specific permission"""
        if self.role == "super_admin":
            return True  # Super admin has all permissions
        return self.permissions.get(permission, False)
    
    def can_access_city(self, city):
        """Check if admin can access specific city"""
        if self.role == "super_admin":
            return True
        return city in self.assigned_cities
    
    def add_city(self, city):
        """Add city to admin's assigned cities"""
        if not self.assigned_cities:
            self.assigned_cities = []
        if city not in self.assigned_cities:
            self.assigned_cities.append(city)
            # Mark as modified for SQLAlchemy
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(self, "assigned_cities")
    
    def remove_city(self, city):
        """Remove city from admin's assigned cities"""
        if self.assigned_cities and city in self.assigned_cities:
            self.assigned_cities.remove(city)
            # Mark as modified for SQLAlchemy
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(self, "assigned_cities")
    
    def get_approval_rate(self):
        """Calculate approval rate"""
        total = self.total_approvals + self.total_rejections
        if total == 0:
            return 0
        return (self.total_approvals / total) * 100
    
    def log_activity(self, action, entity_type, entity_id, old_value=None, new_value=None, ip_address=None):
        """Log admin activity"""
        log = AdminActivityLog(
            admin_id=self.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        return log


class AdminActivityLog(db.Model):
    """Tracks all admin activities for audit trail"""
    __tablename__ = "admin_activity_log"
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=False)
    
    # Action Details
    action = db.Column(db.String(100), nullable=False)  # 'verify_document', 'approve_coach', etc.
    entity_type = db.Column(db.String(50), nullable=False)  # 'coach', 'document', 'application'
    entity_id = db.Column(db.Integer, nullable=False)
    
    # Changes
    old_value = db.Column(db.JSON, nullable=True)
    new_value = db.Column(db.JSON, nullable=True)
    
    # Metadata
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AdminActivityLog {self.action} by Admin {self.admin_id}>"


class AdminPermission(db.Model):
    """Predefined permissions for admin roles"""
    __tablename__ = "admin_permission"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(50))  # 'verification', 'management', 'reporting'
    
    # Predefined permissions
    PERMISSIONS = {
        'verify_coaches': 'Verify coach documents and profiles',
        'approve_documents': 'Approve or reject coach documents',
        'manage_admins': 'Create and manage other admins',
        'view_analytics': 'View platform analytics and reports',
        'handle_appeals': 'Handle coach appeals and disputes',
        'send_notifications': 'Send notifications to coaches',
        'export_reports': 'Export verification reports',
        'manage_subscriptions': 'Manage user subscriptions',
        'view_payments': 'View payment information',
        'manage_plans': 'Manage membership plans'
    }


class AdminRole(db.Model):
    """Predefined admin roles with default permissions"""
    __tablename__ = "admin_role"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.JSON)
    
    # Predefined roles
    ROLES = {
        'super_admin': {
            'description': 'Platform owner with full access',
            'permissions': {
                'verify_coaches': True,
                'approve_documents': True,
                'manage_admins': True,
                'view_analytics': True,
                'handle_appeals': True,
                'send_notifications': True,
                'export_reports': True,
                'manage_subscriptions': True,
                'view_payments': True,
                'manage_plans': True
            }
        },
        'regional_admin': {
            'description': 'City-level admin for verification',
            'permissions': {
                'verify_coaches': True,
                'approve_documents': True,
                'manage_admins': False,
                'view_analytics': True,
                'handle_appeals': True,
                'send_notifications': True,
                'export_reports': True,
                'manage_subscriptions': False,
                'view_payments': False,
                'manage_plans': False
            }
        },
        'verification_officer': {
            'description': 'Document verification only',
            'permissions': {
                'verify_coaches': True,
                'approve_documents': True,
                'manage_admins': False,
                'view_analytics': False,
                'handle_appeals': False,
                'send_notifications': False,
                'export_reports': False,
                'manage_subscriptions': False,
                'view_payments': False,
                'manage_plans': False
            }
        }
    }
