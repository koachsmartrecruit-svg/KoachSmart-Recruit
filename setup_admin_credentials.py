"""
Setup Admin Credentials
Creates fresh admin accounts with known passwords
"""

from core.app_factory import create_app
from core.extensions import db
from models.user import User
from models.admin import Admin, AdminActivityLog
from werkzeug.security import generate_password_hash

def setup_admins():
    app = create_app()
    
    with app.app_context():
        print("Setting up admin credentials...")
        
        # Delete old data
        try:
            AdminActivityLog.query.delete()
            Admin.query.delete()
            User.query.filter(User.email.in_(['super@admin.com', 'regional@admin.com'])).delete()
            db.session.commit()
            print("✓ Cleaned old data")
        except Exception as e:
            db.session.rollback()
            print(f"Note: {e}")
        
        # Create Super Admin
        print("\nCreating Super Admin...")
        user1 = User(
            username='superadmin',
            email='super@admin.com',
            password=generate_password_hash('Admin@123'),
            role='admin'
        )
        db.session.add(user1)
        db.session.flush()
        
        admin1 = Admin(user_id=user1.id, role='super_admin')
        admin1.generate_api_credentials()
        db.session.add(admin1)
        db.session.commit()
        
        print(f"✓ Super Admin Created")
        print(f"  Email: super@admin.com")
        print(f"  Password: Admin@123")
        print(f"  API Key: {admin1.api_key[:30]}...")
        
        # Create Regional Admin
        print("\nCreating Regional Admin...")
        user2 = User(
            username='regionaladmin',
            email='regional@admin.com',
            password=generate_password_hash('Admin@123'),
            role='admin'
        )
        db.session.add(user2)
        db.session.flush()
        
        admin2 = Admin(
            user_id=user2.id,
            role='regional_admin',
            assigned_cities=['Mumbai', 'Pune', 'Nagpur']
        )
        admin2.generate_api_credentials()
        db.session.add(admin2)
        db.session.commit()
        
        print(f"✓ Regional Admin Created")
        print(f"  Email: regional@admin.com")
        print(f"  Password: Admin@123")
        print(f"  Cities: Mumbai, Pune, Nagpur")
        print(f"  API Key: {admin2.api_key[:30]}...")
        
        print("\n" + "="*60)
        print("✓ SETUP COMPLETE - Ready to test!")
        print("="*60)

if __name__ == "__main__":
    setup_admins()
