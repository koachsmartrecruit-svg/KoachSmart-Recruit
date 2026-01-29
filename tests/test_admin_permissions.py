"""
Comprehensive Admin Permission Testing
Tests all admin permission functionality including role-based access control,
city access restrictions, and permission validation.
"""

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash

from core.extensions import db
from models.user import User
from models.admin import Admin
from core.admin_permissions import (
    require_admin_permission, require_super_admin, require_regional_admin,
    check_city_access, get_admin_cities, log_admin_action
)


class TestAdminPermissions:
    """Test admin permission system"""
    
    @pytest.fixture
    def super_admin_user(self, app):
        """Create super admin user for testing"""
        with app.app_context():
            # Create user
            user = User(
                username="super_test",
                email="super@test.com",
                password=generate_password_hash("test123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            # Create admin profile
            admin = Admin(
                user_id=user.id,
                role="super_admin",
                assigned_cities=["Mumbai", "Delhi", "Bangalore"],
                permissions={
                    'verify_coaches': True,
                    'approve_documents': True,
                    'manage_admins': True,
                    'view_analytics': True,
                    'handle_appeals': True,
                    'send_notifications': True,
                    'export_reports': True
                }
            )
            admin.generate_api_credentials()
            db.session.add(admin)
            db.session.commit()
            
            yield user
            
            # Cleanup
            db.session.delete(admin)
            db.session.delete(user)
            db.session.commit()
    
    @pytest.fixture
    def regional_admin_user(self, app):
        """Create regional admin user for testing"""
        with app.app_context():
            # Create user
            user = User(
                username="regional_test",
                email="regional@test.com",
                password=generate_password_hash("test123"),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            
            # Create admin profile
            admin = Admin(
                user_id=user.id,
                role="regional_admin",
                assigned_cities=["Mumbai", "Pune"],
                permissions={
                    'verify_coaches': True,
                    'approve_documents': True,
                    'manage_admins': False,
                    'view_analytics': True,
                    'handle_appeals': True,
                    'send_notifications': False,
                    'export_reports': True
                }
            )
            admin.generate_api_credentials()
            db.session.add(admin)
            db.session.commit()
            
            yield user
            
            # Cleanup
            db.session.delete(admin)
            db.session.delete(user)
            db.session.commit()
    
    @pytest.fixture
    def regular_user(self, app):
        """Create regular user (non-admin) for testing"""
        with app.app_context():
            user = User(
                username="regular_test",
                email="regular@test.com",
                password=generate_password_hash("test123"),
                role="coach"
            )
            db.session.add(user)
            db.session.commit()
            
            yield user
            
            # Cleanup
            db.session.delete(user)
            db.session.commit()


class TestRoleBasedAccess(TestAdminPermissions):
    """Test role-based access control"""
    
    def test_super_admin_dashboard_access(self, client, super_admin_user):
        """Test super admin can access admin dashboard"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(super_admin_user.id)
            sess['_fresh'] = True
        
        response = client.get('/admin-management/dashboard')
        assert response.status_code == 200
        assert b'Super Admin Dashboard' in response.data or b'Admin Dashboard' in response.data
    
    def test_regional_admin_dashboard_access(self, client, regional_admin_user):
        """Test regional admin can access admin dashboard"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(regional_admin_user.id)
            sess['_fresh'] = True
        
        response = client.get('/admin-management/dashboard')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data
    
    def test_regular_user_dashboard_denied(self, client, regular_user):
        """Test regular user cannot access admin dashboard"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(regular_user.id)
            sess['_fresh'] = True
        
        response = client.get('/admin-management/dashboard')
        assert response.status_code == 302  # Redirect
    
    def test_super_admin_manage_admins(self, client, super_admin_user):
        """Test super admin can manage other admins"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(super_admin_user.id)
            sess['_fresh'] = True
        
        response = client.get('/admin-management/admins')
        assert response.status_code == 200
        assert b'Admin Management' in response.data or b'List' in response.data
    
    def test_regional_admin_manage_admins_denied(self, client, regional_admin_user):
        """Test regional admin cannot manage other admins"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(regional_admin_user.id)
            sess['_fresh'] = True
        
        response = client.get('/admin-management/admins')
        assert response.status_code == 302  # Should redirect with error


class TestCityAccessRestrictions(TestAdminPermissions):
    """Test city-based access restrictions"""
    
    def test_super_admin_all_cities_access(self, app, super_admin_user):
        """Test super admin has access to all cities"""
        with app.app_context():
            from flask_login import login_user
            login_user(super_admin_user)
            
            # Super admin should have access to any city
            assert check_city_access("Mumbai") == True
            assert check_city_access("Delhi") == True
            assert check_city_access("Chennai") == True  # Even unassigned cities
    
    def test_regional_admin_assigned_cities_only(self, app, regional_admin_user):
        """Test regional admin only has access to assigned cities"""
        with app.app_context():
            from flask_login import login_user
            login_user(regional_admin_user)
            
            # Should have access to assigned cities
            assert check_city_access("Mumbai") == True
            assert check_city_access("Pune") == True
            
            # Should NOT have access to unassigned cities
            assert check_city_access("Delhi") == False
            assert check_city_access("Bangalore") == False
    
    def test_get_admin_cities_super_admin(self, app, super_admin_user):
        """Test get_admin_cities returns all cities for super admin"""
        with app.app_context():
            from flask_login import login_user
            login_user(super_admin_user)
            
            cities = get_admin_cities()
            # Super admin should get all cities (or None meaning all)
            assert cities is None or len(cities) > 0
    
    def test_get_admin_cities_regional_admin(self, app, regional_admin_user):
        """Test get_admin_cities returns assigned cities for regional admin"""
        with app.app_context():
            from flask_login import login_user
            login_user(regional_admin_user)
            
            cities = get_admin_cities()
            assert cities == ["Mumbai", "Pune"]


class TestPermissionValidation(TestAdminPermissions):
    """Test individual permission validation"""
    
    def test_super_admin_all_permissions(self, app, super_admin_user):
        """Test super admin has all permissions"""
        with app.app_context():
            from flask_login import login_user
            login_user(super_admin_user)
            
            admin = Admin.query.filter_by(user_id=super_admin_user.id).first()
            
            # Super admin should have all permissions
            assert admin.has_permission('verify_coaches') == True
            assert admin.has_permission('approve_documents') == True
            assert admin.has_permission('manage_admins') == True
            assert admin.has_permission('view_analytics') == True
            assert admin.has_permission('handle_appeals') == True
            assert admin.has_permission('send_notifications') == True
            assert admin.has_permission('export_reports') == True
    
    def test_regional_admin_limited_permissions(self, app, regional_admin_user):
        """Test regional admin has limited permissions"""
        with app.app_context():
            from flask_login import login_user
            login_user(regional_admin_user)
            
            admin = Admin.query.filter_by(user_id=regional_admin_user.id).first()
            
            # Regional admin should have limited permissions
            assert admin.has_permission('verify_coaches') == True
            assert admin.has_permission('approve_documents') == True
            assert admin.has_permission('manage_admins') == False  # No admin management
            assert admin.has_permission('view_analytics') == True
            assert admin.has_permission('handle_appeals') == True
            assert admin.has_permission('send_notifications') == False  # No notifications
            assert admin.has_permission('export_reports') == True
    
    def test_permission_decorator_allows_authorized(self, app, super_admin_user):
        """Test permission decorator allows authorized users"""
        with app.app_context():
            from flask_login import login_user
            login_user(super_admin_user)
            
            @require_admin_permission('manage_admins')
            def test_function():
                return "success"
            
            # Should not raise exception
            result = test_function()
            assert result == "success"
    
    def test_permission_decorator_blocks_unauthorized(self, app, regional_admin_user):
        """Test permission decorator blocks unauthorized users"""
        with app.app_context():
            from flask_login import login_user
            login_user(regional_admin_user)
            
            @require_admin_permission('manage_admins')
            def test_function():
                return "success"
            
            # Should raise exception or redirect
            with pytest.raises(Exception):
                test_function()


class TestActivityLogging(TestAdminPermissions):
    """Test admin activity logging"""
    
    def test_log_admin_action_creates_log(self, app, super_admin_user):
        """Test that admin actions are properly logged"""
        with app.app_context():
            from flask_login import login_user
            from models.admin import AdminActivityLog
            
            login_user(super_admin_user)
            admin = Admin.query.filter_by(user_id=super_admin_user.id).first()
            
            # Log an action
            admin.log_activity(
                action="test_action",
                entity_type="test_entity",
                entity_id=123,
                old_value={"test": "old"},
                new_value={"test": "new"}
            )
            
            # Check log was created
            log = AdminActivityLog.query.filter_by(
                admin_id=admin.id,
                action="test_action"
            ).first()
            
            assert log is not None
            assert log.entity_type == "test_entity"
            assert log.entity_id == 123
            assert log.old_value == {"test": "old"}
            assert log.new_value == {"test": "new"}
    
    def test_admin_activity_count_tracking(self, app, super_admin_user):
        """Test that admin activity counts are tracked"""
        with app.app_context():
            from flask_login import login_user
            
            login_user(super_admin_user)
            admin = Admin.query.filter_by(user_id=super_admin_user.id).first()
            
            initial_verifications = admin.total_verifications
            initial_approvals = admin.total_approvals
            
            # Simulate verification activity
            admin.total_verifications += 1
            admin.total_approvals += 1
            db.session.commit()
            
            # Refresh and check
            db.session.refresh(admin)
            assert admin.total_verifications == initial_verifications + 1
            assert admin.total_approvals == initial_approvals + 1


class TestAPICredentials(TestAdminPermissions):
    """Test admin API credentials"""
    
    def test_api_credentials_generated(self, app, super_admin_user):
        """Test that API credentials are generated for admins"""
        with app.app_context():
            admin = Admin.query.filter_by(user_id=super_admin_user.id).first()
            
            assert admin.api_key is not None
            assert admin.api_secret is not None
            assert len(admin.api_key) > 10
            assert len(admin.api_secret) > 10
    
    def test_api_credentials_regeneration(self, app, super_admin_user):
        """Test that API credentials can be regenerated"""
        with app.app_context():
            admin = Admin.query.filter_by(user_id=super_admin_user.id).first()
            
            old_key = admin.api_key
            old_secret = admin.api_secret
            
            # Regenerate credentials
            admin.generate_api_credentials()
            db.session.commit()
            
            # Check new credentials are different
            assert admin.api_key != old_key
            assert admin.api_secret != old_secret
            assert len(admin.api_key) > 10
            assert len(admin.api_secret) > 10


class TestAdminMetrics(TestAdminPermissions):
    """Test admin performance metrics"""
    
    def test_approval_rate_calculation(self, app, super_admin_user):
        """Test approval rate calculation"""
        with app.app_context():
            admin = Admin.query.filter_by(user_id=super_admin_user.id).first()
            
            # Set test values
            admin.total_approvals = 80
            admin.total_rejections = 20
            db.session.commit()
            
            # Test approval rate
            approval_rate = admin.get_approval_rate()
            assert approval_rate == 80.0  # 80/(80+20) * 100
    
    def test_approval_rate_no_decisions(self, app, regional_admin_user):
        """Test approval rate when no decisions made"""
        with app.app_context():
            admin = Admin.query.filter_by(user_id=regional_admin_user.id).first()
            
            # Reset to zero
            admin.total_approvals = 0
            admin.total_rejections = 0
            db.session.commit()
            
            # Should return 0 when no decisions made
            approval_rate = admin.get_approval_rate()
            assert approval_rate == 0.0


# Integration Tests
class TestAdminIntegration(TestAdminPermissions):
    """Integration tests for admin system"""
    
    def test_admin_creation_workflow(self, client, super_admin_user):
        """Test complete admin creation workflow"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(super_admin_user.id)
            sess['_fresh'] = True
        
        # Test create admin form
        response = client.get('/admin-management/admin/create')
        assert response.status_code == 200
        
        # Test admin creation
        response = client.post('/admin-management/admin/create', data={
            'email': 'newadmin@test.com',
            'name': 'New Admin',
            'cities': ['Mumbai', 'Delhi']
        })
        assert response.status_code == 302  # Redirect after creation
        
        # Verify admin was created
        with client.application.app_context():
            new_user = User.query.filter_by(email='newadmin@test.com').first()
            assert new_user is not None
            assert new_user.role == 'admin'
            
            new_admin = Admin.query.filter_by(user_id=new_user.id).first()
            assert new_admin is not None
            assert new_admin.role == 'regional_admin'
            assert 'Mumbai' in new_admin.assigned_cities
            assert 'Delhi' in new_admin.assigned_cities
    
    def test_admin_edit_workflow(self, client, super_admin_user, regional_admin_user):
        """Test admin editing workflow"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(super_admin_user.id)
            sess['_fresh'] = True
        
        with client.application.app_context():
            admin = Admin.query.filter_by(user_id=regional_admin_user.id).first()
            admin_id = admin.id
        
        # Test edit form
        response = client.get(f'/admin-management/admin/{admin_id}/edit')
        assert response.status_code == 200
        
        # Test admin update
        response = client.post(f'/admin-management/admin/{admin_id}/edit', data={
            'cities': ['Mumbai', 'Pune', 'Nashik'],
            'verify_coaches': 'on',
            'approve_documents': 'on',
            'view_analytics': 'on'
        })
        assert response.status_code == 302  # Redirect after update
        
        # Verify admin was updated
        with client.application.app_context():
            updated_admin = Admin.query.get(admin_id)
            assert 'Nashik' in updated_admin.assigned_cities
            assert updated_admin.permissions['verify_coaches'] == True
            assert updated_admin.permissions['view_analytics'] == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])