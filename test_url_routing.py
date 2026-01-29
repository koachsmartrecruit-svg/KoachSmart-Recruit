#!/usr/bin/env python3
"""
Test script to verify URL routing is working correctly
"""

from flask import Flask
from routes.coach_routes import coach_bp
from routes.onboarding_routes import onboarding_bp
from routes.admin_routes import admin_bp
from routes.verification_routes import verification_bp

def test_url_routing():
    """Test that all URL routing works correctly"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-key'
    app.config['SERVER_NAME'] = 'localhost:5000'
    
    # Register blueprints
    app.register_blueprint(coach_bp, url_prefix='/coach')
    app.register_blueprint(onboarding_bp, url_prefix='/onboarding')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(verification_bp, url_prefix='/verification')
    
    with app.test_request_context():
        try:
            from flask import url_for
            
            # Test the fixed URL
            onboarding_url = url_for('onboarding.onboarding_unified')
            print(f"✅ onboarding.onboarding_unified -> {onboarding_url}")
            
            # Test admin verification URLs
            admin_verification_url = url_for('admin.admin_coach_verification')
            print(f"✅ admin.admin_coach_verification -> {admin_verification_url}")
            
            admin_detail_url = url_for('admin.admin_coach_verification_detail', user_id=1)
            print(f"✅ admin.admin_coach_verification_detail -> {admin_detail_url}")
            
            # Test verification URLs
            verification_stage1_url = url_for('verification.stage1')
            print(f"✅ verification.stage1 -> {verification_stage1_url}")
            
            verification_dashboard_url = url_for('verification.verification_dashboard')
            print(f"✅ verification.verification_dashboard -> {verification_dashboard_url}")
            
            print("\n🎉 All URL routing tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ URL routing error: {e}")
            return False

if __name__ == "__main__":
    print("🧪 Testing URL Routing...")
    print("=" * 40)
    
    success = test_url_routing()
    
    if success:
        print("\n✅ URL routing fix successful!")
        print("The /profile/edit route should now work correctly.")
        print("\n📝 Fixed Issues:")
        print("   • Changed url_for('onboarding.unified') to url_for('onboarding.onboarding_unified')")
        print("   • This matches the actual function name in onboarding_routes.py")
        print("   • The /coach/profile/edit route will now redirect properly")
    else:
        print("\n❌ URL routing issues detected.")