# create_seed.py
# Place this file in the same folder as your app.py and run: python create_seed.py
# It will create sample users, profiles, jobs and applications.

from werkzeug.security import generate_password_hash
from app import app, db, User, Profile, Job, Application
from datetime import datetime

def seed():
    with app.app_context():
        print("Seeding database...")

        # OPTIONAL: Uncomment to wipe existing tables (CAREFUL)
        # db.drop_all()
        # db.create_all()

        # Helper to avoid duplicates
        def get_or_create_user(email, username, role, password=None, picture=None):
            u = User.query.filter_by(email=email).first()
            if u:
                return u
            u = User(
                username=username,
                email=email,
                role=role,
                profile_pic=picture,
                password=generate_password_hash(password) if password else None
            )
            db.session.add(u)
            db.session.flush()  # get id for profile relation
            return u

        # --- Create Recruiters / Employers ---
        emp1 = get_or_create_user("recruiter1@example.com", "CoachHire Pvt", "employer", "password123")
        emp2 = get_or_create_user("recruiter2@example.com", "Elite Academies", "employer", "password123")

        # --- Create Coaches ---
        coach1 = get_or_create_user("coach1@example.com", "Rahul Sharma", "coach", "password123")
        coach2 = get_or_create_user("coach2@example.com", "Maya Patel", "coach", "password123")
        coach3 = get_or_create_user("coach3@example.com", "Arjun Verma", "coach", "password123")

        # Commit users so we have IDs
        db.session.commit()

        # Create Profiles for coaches if missing
        def ensure_profile(u, full_name, sport, exp, bio, city="Mumbai"):
            p = Profile.query.filter_by(user_id=u.id).first()
            if p:
                return p
            p = Profile(
                user_id=u.id,
                full_name=full_name,
                phone="9999999999",
                sport=sport,
                experience_years=exp,
                certifications="Level 1, First Aid",
                bio=bio,
                city=city,
                is_verified=(exp >= 3),
                views=0
            )
            db.session.add(p)
            return p

        p1 = ensure_profile(coach1, "Rahul Sharma", "Cricket", 5,
                            "Experienced cricket coach focused on batting and fielding.")
        p2 = ensure_profile(coach2, "Maya Patel", "Badminton", 2,
                            "Former state player; coaching juniors and adults.")
        p3 = ensure_profile(coach3, "Arjun Verma", "Football", 1,
                            "Enthusiastic football coach specialized in youth programs.")

        db.session.commit()

        # Create sample jobs by employers
        def create_job(employer, title, sport, location, desc, salary="25000"):
            j = Job(
                employer_id=employer.id,
                title=title,
                sport=sport,
                location=location,
                lat=None,
                lng=None,
                description=desc,
                requirements="Coaching certificate | Experience preferred",
                screening_questions="Do you have a bike? | Years of coaching?",
                is_active=True,
                salary_range=salary,
                job_type="Part Time",
                working_hours="4 PM - 8 PM",
                posted_date=datetime.utcnow()
            )
            db.session.add(j)
            return j

        job1 = create_job(emp1, "Junior Cricket Coach", "Cricket", "Bandra, Mumbai",
                          "Looking for a junior coach for weekend batches.")
        job2 = create_job(emp2, "Badminton Coach - Weekend", "Badminton", "Pune",
                          "Coach required for weekend academy coaching.")

        db.session.commit()

        # Create sample applications: coach1 applies to job1, coach2 to job2
        def create_application(job, user, status="Applied", match_score=80):
            existing = Application.query.filter_by(job_id=job.id, user_id=user.id).first()
            if existing:
                return existing
            a = Application(
                job_id=job.id,
                user_id=user.id,
                status=status,
                match_score=match_score,
                custom_resume_path=None,
                screening_answers="Yes|5",
            )
            db.session.add(a)
            return a

        app1 = create_application(job1, coach1, status="Applied", match_score=85)
        app2 = create_application(job2, coach2, status="Shortlisted", match_score=72)

        db.session.commit()

        print("Seed complete. Created:")
        print(f" - Employers: {emp1.email}, {emp2.email}")
        print(f" - Coaches: {coach1.email}, {coach2.email}, {coach3.email}")
        print(f" - Jobs: {job1.title} (by {emp1.email}), {job2.title} (by {emp2.email})")
        print(f" - Applications: {app1.id}, {app2.id}")

if __name__ == "__main__":
    seed()
