"""
Tests for Admin Management System
Tests admin creation, editing, permissions, and activity logging
"""

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash
from models.user import User
from models.admin import Admin, AdminActivityLog
from core.extensions import db


class TestAdminManagement:
    """Test admin management functionality"""
    
    def test_create_super_admin(self, app, client):
        """Test creating a super admin user"""
        with app.app_context():
            # Create super admin user
            user = User(
                username="super_admin",
                email="super@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            # Create admin profile
            admin = Admin(
                user_id=user.id,
                role="super_admin"
            )
            admin.generate_api_credentials()
            db.session.add(admin)
            db.session.commit()
            
            # Verify
            assert admin.role == "super_admin"
            assert admin.api_key is not None
            assert admin.api_secret is not None
            assert admin.is_active is True
    
    def test_create_regional_admin(self, app, client):
        """Test creating a regional admin"""
        with app.app_context():
            # Create regional admin user
            user = User(
                username="regional_admin",
                email="regional@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            # Create admin profile
            admin = Admin(
                user_id=user.id,
                role="regional_admin",
                assigned_cities=["Mumbai", "Pune"]
            )
            admin.generate_api_credentials()
            db.session.add(admin)
            db.session.commit()
            
            # Verify
            assert admin.role == "regional_admin"
            assert "Mumbai" in admin.assigned_cities
            assert "Pune" in admin.assigned_cities
    
    def test_admin_permissions(self, app, client):
        """Test admin permission checking"""
        with app.app_context():
            # Create admin
            user = User(
                username="test_admin",
                email="test@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            admin = Admin(
                user_id=user.id,
                role="regional_admin",
                permissions={
                    'verify_coaches': True,
                    'approve_documents': True,
                    'manage_admins': False,
                    'view_analytics': True,
                    'handle_appeals': True,
                    'send_notifications': True,
                    'export_reports': True
                }
            )
            db.session.add(admin)
            db.session.commit()
            
            # Test permissions
            assert admin.has_permission('verify_coaches') is True
            assert admin.has_permission('manage_admins') is False
            assert admin.has_permission('view_analytics') is True
    
    def test_super_admin_all_permissions(self, app, client):
        """Test that super admin has all permissions"""
        with app.app_context():
            # Create super admin
            user = User(
                username="super",
                email="super@test.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            admin = Admin(
                user_id=user.id,
                role="super_admin"
            )
            db.session.add(admin)
            db.session.commit()
            
            # Super admin should have all permissions
            assert admin.has_permission('verify_coaches') is True
            assert admin.has_permission('manage_admins') is True
            assert admin.has_permission('view_analytics') is True
    
    def test_city_access_control(self, app, client):
        """Test city access control for regional admins"""
        with app.app_context():
            # Create regional admin
            user = User(
                username="city_admin",
                email="city@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            admin = Admin(
                user_id=user.id,
                role="regional_admin",
                assigned_cities=["Mumbai", "Pune"]
            )
            db.session.add(admin)
            db.session.commit()
            
            # Test city access
            assert admin.can_access_city("Mumbai") is True
            assert admin.can_access_city("Pune") is True
            assert admin.can_access_city("Nagpur") is False
    
    def test_super_admin_city_access(self, app, client):
        """Test that super admin can access all cities"""
        with app.app_context():
            # Create super admin
            user = User(
                username="super_city",
                email="super_city@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            admin = Admin(
                user_id=user.id,
                role="super_admin"
            )
            db.session.add(admin)
            db.session.commit()
            
            # Super admin can access all cities
            assert admin.can_access_city("Mumbai") is True
            assert admin.can_access_city("Nagpur") is True
            assert admin.can_access_city("AnyCity") is True
    
    def test_add_remove_city(self, app, client):
        """Test adding and removing cities from admin"""
        with app.app_context():
            # Create admin
            user = User(
                username="city_mgmt",
                email="city_mgmt@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            admin = Admin(
                user_id=user.id,
                role="regional_admin",
                assigned_cities=["Mumbai"]
            )
            db.session.add(admin)
            db.session.commit()
            
            # Add city
            admin.add_city("Pune")
            db.session.commit()
            assert "Pune" in admin.assigned_cities
            
            # Remove city
            admin.remove_city("Mumbai")
            db.session.commit()
            assert "Mumbai" not in admin.assigned_cities
            assert "Pune" in admin.assigned_cities
    
    def test_approval_rate_calculation(self, app, client):
        """Test approval rate calculation"""
        with app.app_context():
            # Create admin
            user = User(
                username="approval_test",
                email="approval@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            admin = Admin(
                user_id=user.id,
                role="regional_admin",
                total_approvals=80,
                total_rejections=20
            )
            db.session.add(admin)
            db.session.commit()
            
            # Calculate approval rate
            rate = admin.get_approval_rate()
            assert rate == 80.0
    
    def test_activity_logging(self, app, client):
        """Test admin activity logging"""
        with app.app_context():
            # Create admin
            user = User(
                username="log_test",
                email="log@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            admin = Admin(
                user_id=user.id,
                role="regional_admin"
            )
            db.session.add(admin)
            db.session.commit()
            
            # Log activity
            admin.log_activity(
                action="verify_document",
                entity_type="coach",
                entity_id=123,
                old_value={"status": "pending"},
                new_value={"status": "verified"}
            )
            
            # Verify log
            log = AdminActivityLog.query.filter_by(admin_id=admin.id).first()
            assert log is not None
            assert log.action == "verify_document"
            assert log.entity_type == "coach"
            assert log.entity_id == 123
    
    def test_api_credentials_generation(self, app, client):
        """Test API credentials generation"""
        with app.app_context():
            # Create admin
            user = User(
                username="api_test",
                email="api@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            admin = Admin(
                user_id=user.id,
                role="regional_admin"
            )
            
            # Generate credentials
            api_key, api_secret = admin.generate_api_credentials()
            
            assert api_key.startswith("admin_")
            assert len(api_secret) > 0
            assert admin.api_key == api_key
            assert admin.api_secret == api_secret
    
    def test_admin_status_toggle(self, app, client):
        """Test toggling admin active/inactive status"""
        with app.app_context():
            # Create admin
            user = User(
                username="status_test",
                email="status@admin.com",
                password=generate_password_hash("password123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            admin = Admin(
                user_id=user.id,
                role="regional_admin",
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            
            # Toggle status
            assert admin.is_active is True
            admin.is_active = False
            db.session.commit()
            assert admin.is_active is False


class TestAdminRoutes:
    """Test admin management routes"""
    
    def test_dashboard_requires_super_admin(self, app, client):
        """Test that dashboard requires super admin"""
        response = client.get(url_for("admin_mgmt.dashboard"))
        # Should redirect to login
        assert response.status_code in [302, 401]
    
    def test_list_admins_requires_super_admin(self, app, client):
        """Test that list admins requires super admin"""
        response = client.get(url_for("admin_mgmt.list_admins"))
        # Should redirect to login
        assert response.status_code in [302, 401]
    
    def test_create_admin_requires_super_admin(self, app, client):
        """Test that create admin requires super admin"""
        response = client.get(url_for("admin_mgmt.create_admin"))
        # Should redirect to login
        assert response.status_code in [302, 401]
