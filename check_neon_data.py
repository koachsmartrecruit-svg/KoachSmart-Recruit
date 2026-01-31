#!/usr/bin/env python3
"""
Check Neon Database Contents
Verify what data is actually in the database
"""

from core.app_factory import create_app
from core.extensions import db
from models.user import User
from models.profile import Profile
from models.job import Job
from models.application import Application
from sqlalchemy import text

def check_database_contents():
    """Check what's actually in the Neon database"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Checking Neon Database Contents...")
        print("=" * 60)
        
        try:
            # Check database connection
            result = db.session.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database Connected: {version[:50]}...")
            print()
            
            # Check Users table
            print("👥 USERS TABLE:")
            print("-" * 40)
            users = User.query.all()
            print(f"Total Users: {len(users)}")
            
            coaches = User.query.filter_by(role='coach').all()
            employers = User.query.filter_by(role='employer').all()
            
            print(f"Coaches: {len(coaches)}")
            print(f"Employers: {len(employers)}")
            print()
            
            # Show recent users
            print("Recent Users:")
            recent_users = User.query.order_by(User.id.desc()).limit(10).all()
            for user in recent_users:
                print(f"  ID: {user.id}, Email: {user.email}, Role: {user.role}")
            print()
            
            # Check Profiles table
            print("📋 PROFILES TABLE:")
            print("-" * 40)
            profiles = Profile.query.all()
            print(f"Total Profiles: {len(profiles)}")
            
            # Show recent profiles
            print("Recent Profiles:")
            recent_profiles = Profile.query.order_by(Profile.id.desc()).limit(5).all()
            for profile in recent_profiles:
                print(f"  ID: {profile.id}, Name: {profile.full_name}, Sport: {profile.sport}")
            print()
            
            # Check Jobs table
            print("💼 JOBS TABLE:")
            print("-" * 40)
            jobs = Job.query.all()
            print(f"Total Jobs: {len(jobs)}")
            
            active_jobs = Job.query.filter_by(is_active=True).all()
            print(f"Active Jobs: {len(active_jobs)}")
            
            # Show recent jobs
            print("Recent Jobs:")
            recent_jobs = Job.query.order_by(Job.id.desc()).limit(5).all()
            for job in recent_jobs:
                print(f"  ID: {job.id}, Title: {job.title}, Sport: {job.sport}, Active: {job.is_active}")
            print()
            
            # Check Applications table
            print("📝 APPLICATIONS TABLE:")
            print("-" * 40)
            applications = Application.query.all()
            print(f"Total Applications: {len(applications)}")
            
            # Show recent applications
            print("Recent Applications:")
            recent_apps = Application.query.order_by(Application.id.desc()).limit(5).all()
            for app in recent_apps:
                print(f"  ID: {app.id}, Job ID: {app.job_id}, User ID: {app.user_id}, Status: {app.status}")
            print()
            
            # Check for our test accounts specifically
            print("🔍 CHECKING FOR TEST ACCOUNTS:")
            print("-" * 40)
            
            test_emails = [
                "rajesh.kumar.coach@gmail.com",
                "priya.sharma.badminton@gmail.com", 
                "admin@elitesportsacademy.gmail.com",
                "hiring@championstrainingcenter.gmail.com"
            ]
            
            for email in test_emails:
                user = User.query.filter_by(email=email).first()
                if user:
                    print(f"  ✅ Found: {email} (ID: {user.id}, Role: {user.role})")
                else:
                    print(f"  ❌ Missing: {email}")
            
            print()
            
            # Check table schemas
            print("📊 TABLE SCHEMAS:")
            print("-" * 40)
            
            # Check if tables exist
            tables_to_check = ['user', 'profile', 'job', 'application']
            for table_name in tables_to_check:
                try:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.fetchone()[0]
                    print(f"  {table_name}: {count} records")
                except Exception as e:
                    print(f"  {table_name}: ERROR - {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database Error: {e}")
            return False

def show_database_url():
    """Show the database URL being used"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        # Hide password for security
        if '@' in db_url:
            parts = db_url.split('@')
            if len(parts) == 2:
                user_part = parts[0].split('://')[-1]
                if ':' in user_part:
                    user = user_part.split(':')[0]
                    masked_url = db_url.replace(user_part, f"{user}:****")
                    print(f"🔗 Database URL: {masked_url}")
                else:
                    print(f"🔗 Database URL: {db_url}")
            else:
                print(f"🔗 Database URL: {db_url}")
        else:
            print(f"🔗 Database URL: {db_url}")
    else:
        print("❌ No DATABASE_URL found in environment")

if __name__ == "__main__":
    print("🔍 Neon Database Inspection Tool")
    print("=" * 60)
    
    show_database_url()
    print()
    
    success = check_database_contents()
    
    if success:
        print("✅ Database inspection completed!")
    else:
        print("❌ Database inspection failed!")