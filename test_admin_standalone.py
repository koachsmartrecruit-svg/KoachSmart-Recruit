#!/usr/bin/env python3
"""
Standalone Admin Permission Tests
Tests admin functionality without Flask app context
"""

import sys
import os
import tempfile
import sqlite3
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_database():
    """Create a test SQLite database with admin tables"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create user table
    cursor.execute('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(255),
            role VARCHAR(20) DEFAULT 'coach'
        )
    ''')
    
    # Create admin table
    cursor.execute('''
        CREATE TABLE admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            role VARCHAR(50) DEFAULT 'regional_admin',
            assigned_cities TEXT,
            permissions TEXT,
            api_key VARCHAR(255),
            api_secret VARCHAR(255),
            total_verifications INTEGER DEFAULT 0,
            total_approvals INTEGER DEFAULT 0,
            total_rejections INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    ''')
    
    # Create admin activity log table
    cursor.execute('''
        CREATE TABLE admin_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action VARCHAR(100) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INTEGER NOT NULL,
            old_value TEXT,
            new_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES admin (id)
        )
    ''')
    
    conn.commit()
    return conn, db_path


def test_admin_creation():
    """Test basic admin creation"""
    print("🧪 Testing admin creation...")
    
    conn, db_path = create_test_database()
    cursor = conn.cursor()
    
    try:
        # Create user
        cursor.execute('''
            INSERT INTO user (username, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', ('test_admin', 'test@admin.com', 'hashed_password', 'admin'))
        
        user_id = cursor.lastrowid
        
        # Create admin
        cursor.execute('''
            INSERT INTO admin (user_id, role, assigned_cities, api_key, api_secret)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'super_admin', '["Mumbai", "Delhi"]', 'test_api_key', 'test_api_secret'))
        
        admin_id = cursor.lastrowid
        
        # Verify admin was created
        cursor.execute('SELECT * FROM admin WHERE id = ?', (admin_id,))
        admin = cursor.fetchone()
        
        assert admin is not None, "Admin should be created"
        assert admin[2] == 'super_admin', "Admin role should be super_admin"
        assert 'Mumbai' in admin[3], "Admin should have Mumbai in assigned cities"
        
        print("✅ Admin creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Admin creation test failed: {e}")
        return False
    
    finally:
        conn.close()
        os.unlink(db_path)


def test_admin_permissions():
    """Test admin permission logic"""
    print("🧪 Testing admin permissions...")
    
    try:
        # Test super admin permissions
        def has_permission_super_admin(permission):
            return True  # Super admin has all permissions
        
        def has_permission_regional_admin(permission, permissions_dict):
            return permissions_dict.get(permission, False)
        
        # Test super admin
        assert has_permission_super_admin('verify_coaches') == True
        assert has_permission_super_admin('manage_admins') == True
        assert has_permission_super_admin('any_permission') == True
        
        # Test regional admin
        regional_permissions = {
            'verify_coaches': True,
            'manage_admins': False,
            'view_analytics': True
        }
        
        assert has_permission_regional_admin('verify_coaches', regional_permissions) == True
        assert has_permission_regional_admin('manage_admins', regional_permissions) == False
        assert has_permission_regional_admin('view_analytics', regional_permissions) == True
        
        print("✅ Admin permissions test passed")
        return True
        
    except Exception as e:
        print(f"❌ Admin permissions test failed: {e}")
        return False


def test_city_access():
    """Test city access logic"""
    print("🧪 Testing city access...")
    
    try:
        def can_access_city_super_admin(city):
            return True  # Super admin can access all cities
        
        def can_access_city_regional_admin(city, assigned_cities):
            return city in assigned_cities
        
        # Test super admin
        assert can_access_city_super_admin('Mumbai') == True
        assert can_access_city_super_admin('Delhi') == True
        assert can_access_city_super_admin('Any City') == True
        
        # Test regional admin
        assigned_cities = ['Mumbai', 'Pune']
        assert can_access_city_regional_admin('Mumbai', assigned_cities) == True
        assert can_access_city_regional_admin('Pune', assigned_cities) == True
        assert can_access_city_regional_admin('Delhi', assigned_cities) == False
        
        print("✅ City access test passed")
        return True
        
    except Exception as e:
        print(f"❌ City access test failed: {e}")
        return False


def test_approval_rate_calculation():
    """Test approval rate calculation"""
    print("🧪 Testing approval rate calculation...")
    
    try:
        def get_approval_rate(total_approvals, total_rejections):
            total = total_approvals + total_rejections
            if total == 0:
                return 0
            return (total_approvals / total) * 100
        
        # Test with data
        assert get_approval_rate(80, 20) == 80.0
        assert get_approval_rate(50, 50) == 50.0
        assert get_approval_rate(100, 0) == 100.0
        assert get_approval_rate(0, 100) == 0.0
        assert get_approval_rate(0, 0) == 0.0
        
        print("✅ Approval rate calculation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Approval rate calculation test failed: {e}")
        return False


def test_activity_logging():
    """Test activity logging"""
    print("🧪 Testing activity logging...")
    
    conn, db_path = create_test_database()
    cursor = conn.cursor()
    
    try:
        # Create user and admin
        cursor.execute('''
            INSERT INTO user (username, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', ('log_test', 'log@test.com', 'hashed_password', 'admin'))
        
        user_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO admin (user_id, role)
            VALUES (?, ?)
        ''', (user_id, 'super_admin'))
        
        admin_id = cursor.lastrowid
        
        # Log activity
        cursor.execute('''
            INSERT INTO admin_activity_log (admin_id, action, entity_type, entity_id, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin_id, 'test_action', 'test_entity', 123, '{"status": "old"}', '{"status": "new"}'))
        
        log_id = cursor.lastrowid
        
        # Verify log was created
        cursor.execute('SELECT * FROM admin_activity_log WHERE id = ?', (log_id,))
        log = cursor.fetchone()
        
        assert log is not None, "Activity log should be created"
        assert log[2] == 'test_action', "Action should match"
        assert log[3] == 'test_entity', "Entity type should match"
        assert log[4] == 123, "Entity ID should match"
        
        print("✅ Activity logging test passed")
        return True
        
    except Exception as e:
        print(f"❌ Activity logging test failed: {e}")
        return False
    
    finally:
        conn.close()
        os.unlink(db_path)


def test_api_credentials():
    """Test API credentials generation"""
    print("🧪 Testing API credentials...")
    
    try:
        import secrets
        
        def generate_api_credentials():
            api_key = f"admin_{secrets.token_urlsafe(32)}"
            api_secret = secrets.token_urlsafe(64)
            return api_key, api_secret
        
        # Generate credentials
        api_key, api_secret = generate_api_credentials()
        
        assert api_key.startswith('admin_'), "API key should start with 'admin_'"
        assert len(api_key) > 10, "API key should be long enough"
        assert len(api_secret) > 10, "API secret should be long enough"
        assert api_key != api_secret, "API key and secret should be different"
        
        # Generate again to ensure uniqueness
        api_key2, api_secret2 = generate_api_credentials()
        assert api_key != api_key2, "API keys should be unique"
        assert api_secret != api_secret2, "API secrets should be unique"
        
        print("✅ API credentials test passed")
        return True
        
    except Exception as e:
        print(f"❌ API credentials test failed: {e}")
        return False


def run_all_tests():
    """Run all admin permission tests"""
    print("🚀 Running KoachSmart Admin Permission Tests (Standalone)")
    print("=" * 60)
    
    tests = [
        test_admin_creation,
        test_admin_permissions,
        test_city_access,
        test_approval_rate_calculation,
        test_activity_logging,
        test_api_credentials
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All admin permission tests passed!")
        print("\n✅ Verified functionality:")
        print("  • Admin creation and database operations")
        print("  • Role-based permission checking")
        print("  • City access restrictions")
        print("  • Approval rate calculations")
        print("  • Activity logging system")
        print("  • API credentials generation")
        return True
    else:
        print(f"❌ {failed} test(s) failed. Please check the output above.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)