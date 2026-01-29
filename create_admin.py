#!/usr/bin/env python3
"""
Create admin user for KoachSmart platform
"""
import os
import sys
from werkzeug.security import generate_password_hash

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_admin_user():
    """Create admin user"""
    try:
        from core.app_factory import create_app
        from core.extensions import db
        from models.user import User
        from models.profile import Profile
        from services.referral_service import generate_referral_code
        
        app = create_app()
        
        with app.app_context():
            # First, create tables if they don't exist
            db.create_all()
            print("✅ Database tables verified/created")
            
            # Check if admin already exists
            existing_admin = User.query.filter_by(email='admin@koachsmart.com').first()
            if existing_admin:
                print(f"❌ Admin user already exists: {existing_admin.username} ({existing_admin.email})")
                print(f"   Role: {existing_admin.role}")
                print(f"   ID: {existing_admin.id}")
                return
            
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@koachsmart.com',
                password=generate_password_hash('admin123'),  # Change this password!
                role='admin',
                subscription_status='premium',
                onboarding_completed=True,
                referral_code=generate_referral_code(),
                coins=10000,  # Give admin some coins
                points=5000   # Give admin some points
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Create admin profile
            admin_profile = Profile(
                user_id=admin_user.id,
                full_name='System Administrator',
                bio='KoachSmart Platform Administrator',
                city='Mumbai',
                state='Maharashtra'
            )
            
            db.session.add(admin_profile)
            db.session.commit()
            
            print("✅ Admin user created successfully!")
            print(f"   Username: {admin_user.username}")
            print(f"   Email: {admin_user.email}")
            print(f"   Password: admin123 (CHANGE THIS!)")
            print(f"   Role: {admin_user.role}")
            print(f"   ID: {admin_user.id}")
            
            # Show login URL
            print(f"\n🔗 Login at: http://127.0.0.1:5000/login")
            print(f"🔗 Admin Panel: http://127.0.0.1:5000/super-admin")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project directory")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

def create_google_admin_user(email, name):
    """Create admin user for Google OAuth"""
    try:
        from core.app_factory import create_app
        from core.extensions import db
        from models.user import User
        from models.profile import Profile
        from services.referral_service import generate_referral_code
        
        app = create_app()
        
        with app.app_context():
            # First, create tables if they don't exist
            db.create_all()
            
            # Check if admin already exists
            existing_admin = User.query.filter_by(email=email).first()
            if existing_admin:
                # Update role to admin
                existing_admin.role = 'admin'
                existing_admin.subscription_status = 'premium'
                db.session.commit()
                print(f"✅ Updated existing user to admin: {existing_admin.username} ({existing_admin.email})")
                return
            
            # Create admin user (no password for Google OAuth)
            admin_user = User(
                username=email.split('@')[0],
                email=email,
                role='admin',
                subscription_status='premium',
                onboarding_completed=True,
                referral_code=generate_referral_code(),
                coins=10000,
                points=5000
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Create admin profile
            admin_profile = Profile(
                user_id=admin_user.id,
                full_name=name,
                bio='KoachSmart Platform Administrator',
                city='Mumbai',
                state='Maharashtra'
            )
            
            db.session.add(admin_profile)
            db.session.commit()
            
            print("✅ Google admin user created successfully!")
            print(f"   Username: {admin_user.username}")
            print(f"   Email: {admin_user.email}")
            print(f"   Role: {admin_user.role}")
            print(f"   Login: Use Google OAuth at http://127.0.0.1:5000/login")
            
    except Exception as e:
        print(f"❌ Error creating Google admin user: {e}")

def check_database():
    """Check database connection and tables"""
    try:
        from core.app_factory import create_app
        from core.extensions import db
        from sqlalchemy import inspect
        
        app = create_app()
        
        with app.app_context():
            # Test database connection
            db.engine.execute("SELECT 1")
            print("✅ Database connection successful")
            
            # List existing tables
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n📋 Existing tables ({len(tables)}):")
            for table in sorted(tables):
                print(f"   - {table}")
                
            # Check user table structure if it exists
            if 'user' in tables:
                columns = inspector.get_columns('user')
                print(f"\n📋 User table columns:")
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
            else:
                print("\n⚠️  User table does not exist")
                
    except Exception as e:
        print(f"❌ Database check failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'google':
            # Create Google OAuth admin
            email = input("Enter admin email: ").strip()
            name = input("Enter admin name: ").strip()
            create_google_admin_user(email, name)
        elif sys.argv[1] == 'check':
            # Check database
            check_database()
    else:
        # Create regular admin
        create_admin_user()