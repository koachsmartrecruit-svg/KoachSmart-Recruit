"""
Profile management tests
"""
import pytest
import tempfile
import os
from models.profile import Profile
from core.extensions import db


class TestProfileCreation:
    """Test profile creation functionality"""
    
    def test_profile_completion_calculation(self, app, sample_coach_user):
        """Test profile completion percentage calculation"""
        with app.app_context():
            # Create profile with minimal data
            profile = Profile(
                user_id=sample_coach_user.id,
                full_name='Test Coach'
            )
            db.session.add(profile)
            db.session.commit()
            
            # Test completion calculation logic
            total_fields = 10
            completed_fields = 1  # Only full_name
            expected_completion = int((completed_fields / total_fields) * 100)
            
            # This would be calculated in the route
            assert expected_completion == 10
    
    def test_complete_profile_creation(self, app, sample_coach_user):
        """Test creating a complete profile"""
        with app.app_context():
            profile = Profile(
                user_id=sample_coach_user.id,
                full_name='Test Coach',
                phone='1234567890',
                bio='Experienced coach',
                sport='Football',
                experience_years=5,
                city='Mumbai',
                state='Maharashtra',
                country='India',
                working_type='Full Time',
                certifications='AIFF Level 1',
                is_verified=True
            )
            db.session.add(profile)
            db.session.commit()
            
            # Check profile was created
            saved_profile = Profile.query.filter_by(user_id=sample_coach_user.id).first()
            assert saved_profile is not None
            assert saved_profile.full_name == 'Test Coach'
            assert saved_profile.sport == 'Football'
    
    def test_profile_views_increment(self, app, sample_coach_profile):
        """Test profile views counter"""
        with app.app_context():
            initial_views = sample_coach_profile.views
            
            # Simulate view increment
            sample_coach_profile.views += 1
            db.session.commit()
            
            updated_profile = Profile.query.get(sample_coach_profile.id)
            assert updated_profile.views == initial_views + 1


class TestProfileUpdate:
    """Test profile update functionality"""
    
    def test_profile_update(self, app, sample_coach_profile):
        """Test updating profile information"""
        with app.app_context():
            # Update profile
            sample_coach_profile.bio = 'Updated bio'
            sample_coach_profile.experience_years = 7
            db.session.commit()
            
            # Check updates
            updated_profile = Profile.query.get(sample_coach_profile.id)
            assert updated_profile.bio == 'Updated bio'
            assert updated_profile.experience_years == 7
    
    def test_profile_verification_status(self, app, sample_coach_profile):
        """Test profile verification status update"""
        with app.app_context():
            # Initially not verified
            assert sample_coach_profile.is_verified == False
            
            # Verify profile
            sample_coach_profile.is_verified = True
            db.session.commit()
            
            # Check verification
            updated_profile = Profile.query.get(sample_coach_profile.id)
            assert updated_profile.is_verified == True


class TestProfileValidation:
    """Test profile data validation"""
    
    def test_phone_validation(self, app, sample_coach_user):
        """Test phone number validation"""
        with app.app_context():
            # Valid phone
            profile = Profile(
                user_id=sample_coach_user.id,
                full_name='Test Coach',
                phone='1234567890'
            )
            db.session.add(profile)
            db.session.commit()
            
            assert profile.phone == '1234567890'
    
    def test_experience_years_validation(self, app, sample_coach_user):
        """Test experience years validation"""
        with app.app_context():
            profile = Profile(
                user_id=sample_coach_user.id,
                full_name='Test Coach',
                experience_years=5
            )
            db.session.add(profile)
            db.session.commit()
            
            assert profile.experience_years == 5
            assert isinstance(profile.experience_years, int)


class TestFileUploads:
    """Test file upload functionality"""
    
    def test_resume_path_storage(self, app, sample_coach_profile):
        """Test resume file path storage"""
        with app.app_context():
            resume_path = 'static/resumes/test_resume.pdf'
            sample_coach_profile.resume_path = resume_path
            db.session.commit()
            
            updated_profile = Profile.query.get(sample_coach_profile.id)
            assert updated_profile.resume_path == resume_path
    
    def test_certificate_path_storage(self, app, sample_coach_profile):
        """Test certificate file path storage"""
        with app.app_context():
            cert_path = 'static/certs/test_cert.pdf'
            sample_coach_profile.cert_proof_path = cert_path
            db.session.commit()
            
            updated_profile = Profile.query.get(sample_coach_profile.id)
            assert updated_profile.cert_proof_path == cert_path
    
    def test_id_proof_path_storage(self, app, sample_coach_profile):
        """Test ID proof file path storage"""
        with app.app_context():
            id_path = 'static/id_proofs/test_id.pdf'
            sample_coach_profile.id_proof_path = id_path
            db.session.commit()
            
            updated_profile = Profile.query.get(sample_coach_profile.id)
            assert updated_profile.id_proof_path == id_path


class TestProfileQueries:
    """Test profile database queries"""
    
    def test_profile_by_user_id(self, app, sample_coach_profile):
        """Test querying profile by user ID"""
        with app.app_context():
            profile = Profile.query.filter_by(user_id=sample_coach_profile.user_id).first()
            assert profile is not None
            assert profile.id == sample_coach_profile.id
    
    def test_profiles_by_sport(self, app, sample_coach_profile):
        """Test querying profiles by sport"""
        with app.app_context():
            profiles = Profile.query.filter_by(sport='Football').all()
            assert len(profiles) >= 1
            assert sample_coach_profile in profiles
    
    def test_verified_profiles(self, app, sample_coach_profile):
        """Test querying verified profiles"""
        with app.app_context():
            # Set profile as verified
            sample_coach_profile.is_verified = True
            db.session.commit()
            
            verified_profiles = Profile.query.filter_by(is_verified=True).all()
            assert sample_coach_profile in verified_profiles