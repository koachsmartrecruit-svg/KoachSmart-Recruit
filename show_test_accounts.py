#!/usr/bin/env python3
"""
Show Test Accounts in Neon Database
Display all test accounts with their details
"""

from core.app_factory import create_app
from core.extensions import db
from models.user import User
from models.profile import Profile
from models.job import Job

def show_test_accounts():
    """Show all test accounts in a readable format"""
    
    app = create_app()
    
    with app.app_context():
        print("🎯 TEST ACCOUNTS IN NEON DATABASE")
        print("=" * 70)
        
        # Show coach accounts
        print("\n👨‍🏫 COACH ACCOUNTS:")
        print("-" * 50)
        
        test_coach_emails = [
            "rajesh.kumar.coach@gmail.com",
            "priya.sharma.badminton@gmail.com", 
            "arjun.singh.football@gmail.com",
            "sneha.patel.swimming@gmail.com",
            "vikram.reddy.basketball@gmail.com"
        ]
        
        for email in test_coach_emails:
            user = User.query.filter_by(email=email).first()
            if user:
                profile = Profile.query.filter_by(user_id=user.id).first()
                print(f"✅ {user.username}")
                print(f"   Email: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Role: {user.role}")
                print(f"   Onboarding: {'✅ Complete' if user.onboarding_completed else '⏳ Incomplete'}")
                print(f"   Membership: {user.membership_status}")
                print(f"   Premium: {'✅ Yes' if user.premium_subscription else '❌ No'}")
                if profile:
                    print(f"   Sport: {profile.sport}")
                    print(f"   Location: {profile.city}")
                print()
        
        # Show employer accounts
        print("🏢 EMPLOYER ACCOUNTS:")
        print("-" * 50)
        
        test_employer_emails = [
            "admin@elitesportsacademy.gmail.com",
            "hiring@championstrainingcenter.gmail.com",
            "careers@victorysportsinstitute.gmail.com", 
            "jobs@aquaexcellenceacademy.gmail.com",
            "recruitment@courtmasterssports.gmail.com"
        ]
        
        for email in test_employer_emails:
            user = User.query.filter_by(email=email).first()
            if user:
                print(f"✅ {user.username}")
                print(f"   Email: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Role: {user.role}")
                print(f"   Onboarding: {'✅ Complete' if user.employer_onboarding_completed else '⏳ Incomplete'}")
                print(f"   Membership: {user.membership_status}")
                print()
        
        # Show jobs created by test employers
        print("💼 JOBS POSTED BY TEST EMPLOYERS:")
        print("-" * 50)
        
        for email in test_employer_emails:
            user = User.query.filter_by(email=email).first()
            if user:
                jobs = Job.query.filter_by(employer_id=user.id).all()
                if jobs:
                    print(f"🏢 {user.username}:")
                    for job in jobs:
                        status = "🟢 Active" if job.is_active else "🔴 Inactive"
                        print(f"   • {job.title} ({job.sport}) - {status}")
                    print()
        
        # Database summary
        print("📊 DATABASE SUMMARY:")
        print("-" * 50)
        total_users = User.query.count()
        total_coaches = User.query.filter_by(role='coach').count()
        total_employers = User.query.filter_by(role='employer').count()
        total_jobs = Job.query.count()
        active_jobs = Job.query.filter_by(is_active=True).count()
        
        print(f"Total Users: {total_users}")
        print(f"Total Coaches: {total_coaches}")
        print(f"Total Employers: {total_employers}")
        print(f"Total Jobs: {total_jobs}")
        print(f"Active Jobs: {active_jobs}")
        
        print("\n🔐 LOGIN CREDENTIALS:")
        print("-" * 50)
        print("Password for ALL test accounts: TestPass123!")
        print("You can login with any of the emails shown above.")

def show_neon_access_instructions():
    """Show instructions for accessing Neon database directly"""
    print("\n🔗 HOW TO VIEW DATA IN NEON CONSOLE:")
    print("=" * 70)
    print("1. Go to https://console.neon.tech/")
    print("2. Login to your Neon account")
    print("3. Select your project")
    print("4. Go to 'SQL Editor' or 'Tables' tab")
    print("5. Run these queries to see your data:")
    print()
    print("   -- View all users")
    print("   SELECT id, username, email, role FROM \"user\" ORDER BY id DESC LIMIT 20;")
    print()
    print("   -- View test coach accounts")
    print("   SELECT id, username, email, role FROM \"user\" ")
    print("   WHERE email LIKE '%coach@gmail.com' OR email LIKE '%badminton@gmail.com' ")
    print("   OR email LIKE '%football@gmail.com' OR email LIKE '%swimming@gmail.com' ")
    print("   OR email LIKE '%basketball@gmail.com';")
    print()
    print("   -- View test employer accounts")
    print("   SELECT id, username, email, role FROM \"user\" ")
    print("   WHERE email LIKE '%elitesportsacademy%' OR email LIKE '%championstrainingcenter%' ")
    print("   OR email LIKE '%victorysportsinstitute%' OR email LIKE '%aquaexcellenceacademy%' ")
    print("   OR email LIKE '%courtmasterssports%';")
    print()
    print("   -- View all jobs")
    print("   SELECT id, title, sport, is_active, employer_id FROM job ORDER BY id DESC;")
    print()
    print("   -- View profiles")
    print("   SELECT id, full_name, sport, city FROM profile ORDER BY id DESC LIMIT 10;")

if __name__ == "__main__":
    show_test_accounts()
    show_neon_access_instructions()