#!/usr/bin/env python3
"""
Manual test script for Khelo Coach application
Run this to verify core functionality works
"""
import requests
import sys
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_RESULTS = []

def test_endpoint(name, path, expected_status=200, method='GET', data=None):
    """Test a single endpoint"""
    try:
        url = urljoin(BASE_URL, path)
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, data=data, timeout=10)
        
        success = response.status_code == expected_status
        TEST_RESULTS.append({
            'name': name,
            'path': path,
            'expected': expected_status,
            'actual': response.status_code,
            'success': success
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}: {response.status_code} (expected {expected_status})")
        
        return success
    except requests.exceptions.RequestException as e:
        TEST_RESULTS.append({
            'name': name,
            'path': path,
            'expected': expected_status,
            'actual': f"ERROR: {e}",
            'success': False
        })
        print(f"❌ FAIL {name}: {e}")
        return False

def run_tests():
    """Run all manual tests"""
    print("🚀 Starting Khelo Coach Application Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"❌ Server is not running at {BASE_URL}")
        print("Please start the application first: py app.py")
        return False
    
    print("\n📋 Testing Core Pages...")
    
    # Test core pages
    test_endpoint("Home Page", "/")
    test_endpoint("Login Page", "/login")
    test_endpoint("Register Page", "/register")
    test_endpoint("Forgot Password", "/forgot-password")
    
    print("\n📋 Testing Protected Routes (should redirect to login)...")
    
    # Test protected routes (should redirect)
    test_endpoint("Coach Dashboard", "/dashboard", expected_status=302)
    test_endpoint("Employer Dashboard", "/employer/dashboard", expected_status=302)
    test_endpoint("Resume Builder", "/resume-builder", expected_status=302)
    test_endpoint("Job Listings", "/jobs", expected_status=302)
    
    print("\n📋 Testing API Endpoints...")
    
    # Test API endpoints (should redirect or return error for unauthenticated)
    test_endpoint("Resume API", "/text-to-resume", expected_status=302, method='POST', 
                 data={'text': 'test'})
    
    print("\n📋 Testing Static Files...")
    
    # Test static files
    test_endpoint("CSS File", "/static/css/style.css")
    test_endpoint("Favicon", "/static/favicon.ico")
    
    print("\n📋 Testing Error Handling...")
    
    # Test 404 handling
    test_endpoint("404 Page", "/nonexistent-page", expected_status=404)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in TEST_RESULTS if result['success'])
    total = len(TEST_RESULTS)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your application is working correctly.")
        print("\n🔗 Next Steps:")
        print("1. Open http://127.0.0.1:5000 in your browser")
        print("2. Register a new coach account")
        print("3. Complete your profile")
        print("4. Test job applications")
        print("5. Try the resume builder")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nFailed tests:")
        for result in TEST_RESULTS:
            if not result['success']:
                print(f"  - {result['name']}: {result['actual']}")
    
    return passed == total

def test_registration_flow():
    """Test user registration flow"""
    print("\n🔐 Testing Registration Flow...")
    
    # This would require more complex session handling
    # For now, just test that the registration page loads
    success = test_endpoint("Registration Form", "/register")
    
    if success:
        print("✅ Registration page loads correctly")
        print("💡 Manual test: Try registering a new user in your browser")
    
    return success

def test_database_connection():
    """Test database connectivity"""
    print("\n💾 Testing Database Connection...")
    
    try:
        # Import here to avoid issues if app isn't set up
        from core.app_factory import create_app
        from core.extensions import db
        
        app = create_app()
        with app.app_context():
            # Try a simple query
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1")).fetchone()
                if result and result[0] == 1:
                    print("✅ Database connection successful")
                    return True
                else:
                    print("❌ Database query failed")
                    return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Khelo Coach Application - Manual Test Suite")
    print("=" * 50)
    
    # Test database first
    db_success = test_database_connection()
    
    # Test web endpoints
    web_success = run_tests()
    
    # Test registration flow
    reg_success = test_registration_flow()
    
    print("\n" + "=" * 50)
    print("🏁 FINAL RESULTS")
    print("=" * 50)
    
    print(f"💾 Database: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"🌐 Web Endpoints: {'✅ PASS' if web_success else '❌ FAIL'}")
    print(f"🔐 Registration: {'✅ PASS' if reg_success else '❌ FAIL'}")
    
    if db_success and web_success and reg_success:
        print("\n🎉 APPLICATION IS READY!")
        print("Start using your Khelo Coach application at:")
        print(f"👉 {BASE_URL}")
    else:
        print("\n⚠️  Some components need attention.")
        print("Check the error messages above and fix any issues.")
    
    sys.exit(0 if (db_success and web_success and reg_success) else 1)