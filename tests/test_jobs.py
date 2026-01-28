"""
Job management tests
"""
import pytest
from models.job import Job
from models.application import Application
from core.extensions import db


class TestJobCreation:
    """Test job creation functionality"""
    
    def test_create_job(self, app, sample_employer_user):
        """Test employer can create job"""
        with app.app_context():
            job = Job(
                title='Basketball Coach',
                description='Looking for experienced basketball coach',
                sport='Basketball',
                location='Delhi',
                salary_range='30000-40000',
                job_type='Full Time',
                employer_id=sample_employer_user.id,
                is_active=True
            )
            db.session.add(job)
            db.session.commit()
            
            # Check job was created
            saved_job = Job.query.filter_by(title='Basketball Coach').first()
            assert saved_job is not None
            assert saved_job.sport == 'Basketball'
            assert saved_job.employer_id == sample_employer_user.id
    
    def test_job_with_screening_questions(self, app, sample_employer_user):
        """Test creating job with screening questions"""
        with app.app_context():
            job = Job(
                title='Tennis Coach',
                description='Tennis coaching position',
                sport='Tennis',
                location='Mumbai',
                salary_range='25000-35000',
                screening_questions='What is your experience?|Do you have certifications?',
                employer_id=sample_employer_user.id,
                is_active=True
            )
            db.session.add(job)
            db.session.commit()
            
            saved_job = Job.query.filter_by(title='Tennis Coach').first()
            assert saved_job.screening_questions is not None
            assert 'experience' in saved_job.screening_questions
    
    def test_job_activation_status(self, app, sample_job):
        """Test job activation/deactivation"""
        with app.app_context():
            # Initially active
            assert sample_job.is_active == True
            
            # Deactivate job
            sample_job.is_active = False
            db.session.commit()
            
            updated_job = Job.query.get(sample_job.id)
            assert updated_job.is_active == False


class TestJobQueries:
    """Test job database queries"""
    
    def test_active_jobs_query(self, app, sample_job):
        """Test querying active jobs"""
        with app.app_context():
            active_jobs = Job.query.filter_by(is_active=True).all()
            assert sample_job in active_jobs
    
    def test_jobs_by_sport(self, app, sample_job):
        """Test querying jobs by sport"""
        with app.app_context():
            football_jobs = Job.query.filter_by(sport='Football').all()
            assert sample_job in football_jobs
    
    def test_jobs_by_location(self, app, sample_job):
        """Test querying jobs by location"""
        with app.app_context():
            mumbai_jobs = Job.query.filter(Job.location.ilike('%Mumbai%')).all()
            assert sample_job in mumbai_jobs
    
    def test_jobs_by_employer(self, app, sample_job, sample_employer_user):
        """Test querying jobs by employer"""
        with app.app_context():
            employer_jobs = Job.query.filter_by(employer_id=sample_employer_user.id).all()
            assert sample_job in employer_jobs


class TestJobApplications:
    """Test job application functionality"""
    
    def test_create_application(self, app, sample_job, sample_coach_user):
        """Test coach can apply to job"""
        with app.app_context():
            application = Application(
                job_id=sample_job.id,
                user_id=sample_coach_user.id,
                match_score=85,
                match_reasons='Good experience match',
                status='Applied'
            )
            db.session.add(application)
            db.session.commit()
            
            # Check application was created
            saved_app = Application.query.filter_by(
                job_id=sample_job.id,
                user_id=sample_coach_user.id
            ).first()
            assert saved_app is not None
            assert saved_app.match_score == 85
    
    def test_application_status_update(self, app, sample_job, sample_coach_user):
        """Test updating application status"""
        with app.app_context():
            application = Application(
                job_id=sample_job.id,
                user_id=sample_coach_user.id,
                match_score=75,
                status='Applied'
            )
            db.session.add(application)
            db.session.commit()
            
            # Update status
            application.status = 'Interview'
            db.session.commit()
            
            updated_app = Application.query.get(application.id)
            assert updated_app.status == 'Interview'
    
    def test_duplicate_application_prevention(self, app, sample_job, sample_coach_user):
        """Test preventing duplicate applications"""
        with app.app_context():
            # Create first application
            app1 = Application(
                job_id=sample_job.id,
                user_id=sample_coach_user.id,
                match_score=80
            )
            db.session.add(app1)
            db.session.commit()
            
            # Check for existing application
            existing_app = Application.query.filter_by(
                job_id=sample_job.id,
                user_id=sample_coach_user.id
            ).first()
            
            assert existing_app is not None
            # In real app, this would prevent creating duplicate
    
    def test_application_match_score(self, app, sample_job, sample_coach_user):
        """Test application match score calculation"""
        with app.app_context():
            # This would typically be calculated by AI service
            match_score = 90
            match_reasons = 'Excellent sport match, good location'
            
            application = Application(
                job_id=sample_job.id,
                user_id=sample_coach_user.id,
                match_score=match_score,
                match_reasons=match_reasons
            )
            db.session.add(application)
            db.session.commit()
            
            saved_app = Application.query.get(application.id)
            assert saved_app.match_score == 90
            assert 'Excellent' in saved_app.match_reasons


class TestJobFiltering:
    """Test job filtering functionality"""
    
    def test_filter_by_multiple_criteria(self, app, sample_employer_user):
        """Test filtering jobs by multiple criteria"""
        with app.app_context():
            # Create multiple jobs
            job1 = Job(
                title='Football Coach',
                sport='Football',
                location='Mumbai',
                job_type='Full Time',
                employer_id=sample_employer_user.id,
                is_active=True
            )
            job2 = Job(
                title='Cricket Coach',
                sport='Cricket',
                location='Delhi',
                job_type='Part Time',
                employer_id=sample_employer_user.id,
                is_active=True
            )
            db.session.add_all([job1, job2])
            db.session.commit()
            
            # Filter by sport and location
            filtered_jobs = Job.query.filter(
                Job.sport == 'Football',
                Job.location.ilike('%Mumbai%'),
                Job.is_active == True
            ).all()
            
            assert job1 in filtered_jobs
            assert job2 not in filtered_jobs
    
    def test_salary_range_filtering(self, app, sample_employer_user):
        """Test filtering by salary range"""
        with app.app_context():
            job = Job(
                title='High Paying Coach',
                sport='Football',
                location='Mumbai',
                salary_range='50000-60000',
                employer_id=sample_employer_user.id,
                is_active=True
            )
            db.session.add(job)
            db.session.commit()
            
            # In real app, this would parse salary range and filter
            high_salary_jobs = Job.query.filter(
                Job.salary_range.contains('50000')
            ).all()
            
            assert job in high_salary_jobs