#!/usr/bin/env python3
"""
Automated test script for the Advanced Verification System
Run this to quickly test core verification functionality
"""
import requests
import sys
import json
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_RESULTS = []

def test_endpoint(name, path, expected_status=200, method='GET', data=None, headers=None):
    """Test a single endpoint"""
    try:
        url = urljoin(BASE_URL, path)
        if method == 'GET':
            response = requests.get(url, timeout=10, headers=headers)
        elif method == 'POST':
            response = requests.post(url, data=data, timeout=10, headers=headers)
        
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
        
        return success, response
    except requests.exceptions.RequestException as e:
        TEST_RESULTS.append({
            'name': name,
            'path': path,
            'expected': expected_status,
            'actual': f"ERROR: {e}",
            'success': False
        })
        print(f"❌ FAIL {name}: {e}")
        return False, None

def test_verification_system():
    """Test the verification system endpoints"""
    print("🏆 Testing Advanced Verification System")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"❌ Server is not running at {BASE_URL}")
        print("Please start the application first: py app.py")
        return False
    
    print("\n📋 Testing Verification Routes...")
    
    # Test verification routes (should redirect to login for unauthenticated users)
    test_endpoint("Verification Dashboard", "/verification/dashboard", expected_status=302)
    test_endpoint("Stage 1", "/verification/stage1", expected_status=302)
    test_endpoint("Stage 2", "/verification/stage2", expected_status=302)
    test_endpoint("Stage 3", "/verification/stage3", expected_status=302)
    test_endpoint("Stage 4", "/verification/stage4", expected_status=302)
    
    print("\n📋 Testing Public Coach Profiles...")
    
    # Test public profile (should return 404 for non-existent coach)
    test_endpoint("Public Profile (Non-existent)", "/coach/nonexistent-coach", expected_status=404)
    
    print("\n📋 Testing Admin Verification Routes...")
    
    # Test admin routes (should redirect to login)
    test_endpoint("Admin Coach Verification", "/admin/coach-verification", expected_status=302)
    
    print("\n📋 Testing API Endpoints...")
    
    # Test API endpoints (should redirect for unauthenticated)
    test_endpoint("Verification Progress API", "/api/verification/progress", expected_status=302)
    test_endpoint("Verification Documents API", "/api/verification/documents", expected_status=302)
    
    return True

def test_database_models():
    """Test verification database models"""
    print("\n💾 Testing Verification Database Models...")
    
    try:
        # Test model imports
        from models.verification import VerificationStage, VerificationDocument, CoachSlugPage
        print("✅ Verification models imported successfully")
        
        from services.verification_service import VerificationService
        print("✅ Verification service imported successfully")
        
        from routes.verification_routes import verification_bp
        print("✅ Verification routes imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Model import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_template_files():
    """Test verification template files exist"""
    print("\n📄 Testing Verification Templates...")
    
    import os
    templates = [
        "templates/verification/dashboard.html",
        "templates/verification/stage1.html",
        "templates/verification/public_profile.html",
        "templates/admin_coach_verification.html"
    ]
    
    all_exist = True
    for template in templates:
        if os.path.exists(template):
            print(f"✅ {template} exists")
        else:
            print(f"❌ {template} missing")
            all_exist = False
    
    return all_exist

def test_service_functions():
    """Test verification service functions"""
    print("\n🔧 Testing Verification Service Functions...")
    
    try:
        from services.verification_service import VerificationService
        
        # Test service methods exist
        methods = [
            'get_or_create_verification_stage',
            'verify_phone',
            'verify_email',
            'verify_aadhar',
            'complete_stage_1',
            'complete_stage_2',
            'complete_stage_3',
            'complete_stage_4',
            'get_verification_progress'
        ]
        
        for method in methods:
            if hasattr(VerificationService, method):
                print(f"✅ VerificationService.{method} exists")
            else:
                print(f"❌ VerificationService.{method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Service function test failed: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive verification system test"""
    print("🚀 Khelo Coach - Advanced Verification System Test")
    print("=" * 60)
    
    # Test components
    tests = [
        ("Database Models", test_database_models),
        ("Template Files", test_template_files),
        ("Service Functions", test_service_functions),
        ("Web Endpoints", test_verification_system)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Tests...")
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SYSTEM TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall Result: {passed}/{total} test categories passed")
    
    if passed == total:
        print("\n🎉 ALL VERIFICATION SYSTEM TESTS PASSED!")
        print("\n🔗 Next Steps:")
        print("1. Start the application: py app.py")
        print("2. Register as a coach")
        print("3. Go to Dashboard → Verification Center")
        print("4. Complete all 4 verification stages")
        print("5. Test admin verification management")
        print("6. Check your public coach profile")
        
        print("\n📋 Manual Testing:")
        print("- Follow VERIFICATION_TEST_CHECKLIST.md for detailed testing")
        print("- Test each verification stage thoroughly")
        print("- Verify badge awarding and coin distribution")
        print("- Test public profile functionality")
        print("- Test admin verification management")
    else:
        print("\n⚠️  Some verification system components failed.")
        print("Check the error messages above and fix any issues.")
        
        failed_tests = [name for name, result in results.items() if not result]
        print(f"\nFailed components: {', '.join(failed_tests)}")
    
    # Web endpoint summary
    if TEST_RESULTS:
        print(f"\n🌐 Web Endpoint Results:")
        web_passed = sum(1 for result in TEST_RESULTS if result['success'])
        web_total = len(TEST_RESULTS)
        print(f"✅ Passed: {web_passed}/{web_total}")
        
        if web_passed < web_total:
            print("❌ Failed endpoints:")
            for result in TEST_RESULTS:
                if not result['success']:
                    print(f"  - {result['name']}: {result['actual']}")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)