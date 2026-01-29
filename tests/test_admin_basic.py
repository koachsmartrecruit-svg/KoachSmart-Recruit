"""
Basic Admin Permission Tests
Simple tests to verify admin system functionality
"""

import pytest
import tempfile
import os
from werkzeug.security import generate_password_hash

from core.app_factory import create_app
from core.extensions import db
from models.user import User
from models.admin import Admin


@pytest.fixture
def test_app():
    """Create test app with SQLite database"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    # Test configuration
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'MAIL_SUPPRESS_SEND': True,
    }
    
    # Create app with test config
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        
        # Cleanup
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


def test_admin_creation(test_app):
    """Test basic admin creation"""
    with test_app.app_context():
        # Create user
        user = User(
            username="test_admin",
            email="test@admin.com",
            password=generate_password_hash("test123"),
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
        
        # Create admin profile
        admin = Admin(
            user_id=user.id,
            role="super_admin",
            assigned_cities=["Mumbai", "Delhi"]
        )
        admin.generate_api_credentials()
        db.session.add(admin)
        db.session.commit()
        
        # Test admin was created
        assert admin.id is not None
        assert admin.role == "super_admin"
        assert "Mumbai" in admin.assigned_cities
        assert admin.api_key is not None
        assert admin.api_secret is not None


def test_admin_permissions(test_app):
    """Test admin permission system"""
    with test_app.app_context():
        # Create user
        user = User(
            username="test_regional",
            email="regional@test.com",
            password=generate_password_hash("test123"),
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
        
        # Create regional admin
        admin = Admin(
            user_id=user.id,
            role="regional_admin",
            assigned_cities=["Mumbai"],
            permissions={
                'verify_coaches': True,
                'manage_admins': False,
                'view_analytics': True
            }
        )
        db.session.add(admin)
        db.session.commit()
        
        # Test permissions
        assert admin.has_permission('verify_coaches') == True
        assert admin.has_permission('manage_admins') == False
        assert admin.has_permission('view_analytics') == True
        
        # Test city access
        assert admin.can_access_city('Mumbai') == True
        assert admin.can_access_city('Delhi') == False


def test_super_admin_permissions(test_app):
    """Test super admin has all permissions"""
    with test_app.app_context():
        # Create user
        user = User(
            username="super_test",
            email="super@test.com",
            password=generate_password_hash("test123"),
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
        
        # Create super admin
        admin = Admin(
            user_id=user.id,
            role="super_admin"
        )
        db.session.add(admin)
        db.session.commit()
        
        # Super admin should have all permissions
        assert admin.has_permission('verify_coaches') == True
        assert admin.has_permission('manage_admins') == True
        assert admin.has_permission('view_analytics') == True
        assert admin.has_permission('any_permission') == True
        
        # Super admin should access all cities
        assert admin.can_access_city('Mumbai') == True
        assert admin.can_access_city('Delhi') == True
        assert admin.can_access_city('Any City') == True


def test_approval_rate_calculation(test_app):
    """Test approval rate calculation"""
    with test_app.app_context():
        # Create user
        user = User(
            username="metrics_test",
            email="metrics@test.com",
            password=generate_password_hash("test123"),
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
        
        # Create admin
        admin = Admin(
            user_id=user.id,
            role="regional_admin",
            total_approvals=80,
            total_rejections=20
        )
        db.session.add(admin)
        db.session.commit()
        
        # Test approval rate
        approval_rate = admin.get_approval_rate()
        assert approval_rate == 80.0  # 80/(80+20) * 100
        
        # Test zero case
        admin.total_approvals = 0
        admin.total_rejections = 0
        db.session.commit()
        
        approval_rate = admin.get_approval_rate()
        assert approval_rate == 0.0


def test_activity_logging(test_app):
    """Test admin activity logging"""
    with test_app.app_context():
        # Create user
        user = User(
            username="log_test",
            email="log@test.com",
            password=generate_password_hash("test123"),
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
        
        # Create admin
        admin = Admin(
            user_id=user.id,
            role="super_admin"
        )
        db.session.add(admin)
        db.session.commit()
        
        # Log activity
        log = admin.log_activity(
            action="test_action",
            entity_type="test_entity",
            entity_id=123,
            old_value={"status": "old"},
            new_value={"status": "new"}
        )
        
        # Test log was created
        assert log is not None
        assert log.action == "test_action"
        assert log.entity_type == "test_entity"
        assert log.entity_id == 123
        assert log.old_value == {"status": "old"}
        assert log.new_value == {"status": "new"}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])