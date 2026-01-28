"""
Test configuration and fixtures
"""
import pytest
import tempfile
import os
from werkzeug.security import generate_password_hash
from core.app_factory import create_app
from core.extensions import db
from models.user import User
from models.profile import Profile
from models.job import Job
from models.hirer import Hirer


@pytest.fixture
def app():
    """Create application for testing"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers():
    """Authentication headers for API tests"""
    return {'Content-Type': 'application/json'}


@pytest.fixture
def sample_coach_user(app):
    """Create a sample coach user"""
    with app.app_context():
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f'testcoach_{unique_id}',
            email=f'coach_{unique_id}@test.com',
            role='coach',
            phone_verified=True,
            onboarding_completed=True,
            password=generate_password_hash('testpass123')
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_employer_user(app):
    """Create a sample employer user"""
    with app.app_context():
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f'testemployer_{unique_id}',
            email=f'employer_{unique_id}@test.com',
            role='employer',
            phone_verified=True,
            employer_onboarding_completed=True,
            password=generate_password_hash('testpass123')
        )
        db.session.add(user)
        db.session.commit()
        
        # Create hirer profile (separate from user)
        hirer = Hirer(
            institute_name='Test Company',
            contact_person_name='Test Person',
            email=f'employer_{unique_id}@test.com',
            contact_number='1234567890',
            business_type='Academy'
        )
        db.session.add(hirer)
        db.session.commit()
        return user


@pytest.fixture
def sample_admin_user(app):
    """Create a sample admin user"""
    with app.app_context():
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f'testadmin_{unique_id}',
            email=f'admin_{unique_id}@test.com',
            role='admin',
            phone_verified=True,
            password=generate_password_hash('testpass123')
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_coach_profile(app, sample_coach_user):
    """Create a sample coach profile"""
    with app.app_context():
        profile = Profile(
            user_id=sample_coach_user.id,
            full_name='Test Coach',
            phone='1234567890',
            bio='Experienced football coach',
            sport='Football',
            experience_years=5,
            city='Mumbai',
            state='Maharashtra',
            country='India'
        )
        db.session.add(profile)
        db.session.commit()
        return profile


@pytest.fixture
def sample_job(app, sample_employer_user):
    """Create a sample job posting"""
    with app.app_context():
        job = Job(
            title='Football Coach',
            description='Looking for experienced football coach',
            sport='Football',
            location='Mumbai',
            salary_range='25000-35000',
            job_type='Full Time',
            employer_id=sample_employer_user.id,
            is_active=True
        )
        db.session.add(job)
        db.session.commit()
        return job


@pytest.fixture
def authenticated_coach_client(client, sample_coach_user):
    """Client with authenticated coach user"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_coach_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def authenticated_employer_client(client, sample_employer_user):
    """Client with authenticated employer user"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_employer_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def authenticated_admin_client(client, sample_admin_user):
    """Client with authenticated admin user"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_admin_user.id)
        sess['_fresh'] = True
    return client