#!/usr/bin/env python3
"""
Test admin login functionality
"""
import requests
import sys

def test_admin_login():
    """Test admin login and redirect"""
    base_url = "http://127.0.0.1:5000"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # First, get the login page to establish session
        login_page = session.get(f"{base_url}/login", timeout=5)
        print(f"✅ Login page accessible: {login_page.status_code}")
        
        # Test admin login
        login_data = {
            'email': 'admin@koachsmart.com',
            'password': 'admin123'
        }
        
        # Attempt login
        login_response = session.post(f"{base_url}/login", data=login_data, timeout=5, allow_redirects=False)
        print(f"✅ Login response: {login_response.status_code}")
        
        if login_response.status_code == 302:
            redirect_location = login_response.headers.get('Location', '')
            print(f"✅ Redirect location: {redirect_location}")
            
            if 'super-admin' in redirect_location:
                print("✅ Admin login working correctly - redirects to admin panel")
                
                # Test accessing admin panel
                admin_response = session.get(f"{base_url}/super-admin", timeout=5)
                print(f"✅ Admin panel access: {admin_response.status_code}")
                
                if admin_response.status_code == 200:
                    print("🎉 Admin login and access working perfectly!")
                    return True
                else:
                    print("❌ Admin panel not accessible")
            else:
                print(f"❌ Wrong redirect location: {redirect_location}")
        else:
            print(f"❌ Login failed with status: {login_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the application is running at http://127.0.0.1:5000")
        
    return False

def check_admin_user_exists():
    """Check if admin user exists in database"""
    try:
        import os
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from core.app_factory import create_app
        from models.user import User
        
        app = create_app()
        with app.app_context():
            admin_user = User.query.filter_by(email='admin@koachsmart.com').first()
            if admin_user:
                print(f"✅ Admin user exists: {admin_user.username} ({admin_user.role})")
                return True
            else:
                print("❌ Admin user not found in database")
                print("Run: py create_admin.py")
                return False
                
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Admin Login System")
    print("=" * 40)
    
    # Check if admin user exists
    if not check_admin_user_exists():
        print("\n❌ Admin user not found. Create one first:")
        print("py create_admin.py")
        sys.exit(1)
    
    # Test login
    print("\n🧪 Testing admin login...")
    if test_admin_login():
        print("\n🎉 All tests passed! Admin login is working correctly.")
    else:
        print("\n❌ Admin login test failed. Check the errors above.")