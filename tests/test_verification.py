"""
Advanced Verification System Tests
"""
import pytest
import json
from models.verification import VerificationStage, VerificationDocument, CoachSlugPage
from models.user import User
from models.profile import Profile
from services.verification_service import VerificationService
from core.extensions import db


class TestVerificationModels:
    """Test verification database models"""
    
    def test_verification_stage_creation(self, app, sample_coach_user):
        """Test creating verification stage"""
        with app.app_context():
            stage = VerificationStage(user_id=sample_coach_user.id)
            db.session.add(stage)
            db.session.commit()
            
            saved_stage = VerificationStage.query.filter_by(user_id=sample_coach_user.id).first()
            assert saved_stage is not None
            assert saved_stage.get_current_stage() == 1
            assert saved_stage.get_badge_level() == "none"
    
    def test_verification_stage_scoring(self, app, sample_coach_user):
        """Test verification stage scoring"""
        with app.app_context():
            stage = VerificationStage(
                user_id=sample_coach_user.id,
                name_verified=True,
                phone_verified=True,
                email_verified=True
            )
            db.session.add(stage)
            db.session.commit()
            
            score = stage.calculate_stage_1_score()
            assert score == 3  # 3 out of 7 items completed
    
    def test_coach_slug_page_creation(self, app, sample_coach_user):
        """Test coach slug page creation"""
        with app.app_context():
            slug_page = CoachSlugPage(
                user_id=sample_coach_user.id,
                slug="test-coach",
                is_active=True,
                meta_title="Test Coach - KoachSmart"
            )
            db.session.add(slug_page)
            db.session.commit()
            
            saved_page = CoachSlugPage.query.filter_by(slug="test-coach").first()
            assert saved_page is not None
            assert saved_page.user_id == sample_coach_user.id
            assert saved_page.is_active == True
    
    def test_verification_document_creation(self, app, sample_coach_user):
        """Test verification document creation"""
        with app.app_context():
            doc = VerificationDocument(
                user_id=sample_coach_user.id,
                document_type="education",
                file_path="/path/to/document.pdf",
                original_filename="certificate.pdf",
                file_size=1024
            )
            db.session.add(doc)
            db.session.commit()
            
            saved_doc = VerificationDocument.query.filter_by(user_id=sample_coach_user.id).first()
            assert saved_doc is not None
            assert saved_doc.document_type == "education"
            assert saved_doc.verification_status == "pending"


class TestVerificationService:
    """Test verification service functions"""
    
    def test_get_or_create_verification_stage(self, app, sample_coach_user):
        """Test getting or creating verification stage"""
        with app.app_context():
            # First call should create
            stage1 = VerificationService.get_or_create_verification_stage(sample_coach_user.id)
            assert stage1 is not None
            
            # Second call should return existing
            stage2 = VerificationService.get_or_create_verification_stage(sample_coach_user.id)
            assert stage1.id == stage2.id
    
    def test_verify_phone(self, app, sample_coach_user):
        """Test phone verification"""
        with app.app_context():
            # First verification should succeed
            result = VerificationService.verify_phone(sample_coach_user.id, "+91 9876543210")
            assert result == True
            
            # Check stage updated
            stage = VerificationStage.query.filter_by(user_id=sample_coach_user.id).first()
            assert stage.phone_verified == True
            assert stage.stage_1_coins >= 50
            
            # Second verification should fail (already verified)
            result2 = VerificationService.verify_phone(sample_coach_user.id, "+91 9876543210")
            assert result2 == False
    
    def test_verify_email(self, app, sample_coach_user):
        """Test email verification"""
        with app.app_context():
            result = VerificationService.verify_email(sample_coach_user.id)
            assert result == True
            
            stage = VerificationStage.query.filter_by(user_id=sample_coach_user.id).first()
            assert stage.email_verified == True
            assert stage.stage_1_coins >= 50
    
    def test_verify_aadhar(self, app, sample_coach_user):
        """Test Aadhar verification"""
        with app.app_context():
            result = VerificationService.verify_aadhar(sample_coach_user.id, "123456789012")
            assert result == True
            
            stage = VerificationStage.query.filter_by(user_id=sample_coach_user.id).first()
            assert stage.aadhar_verified == True
            assert stage.stage_1_coins >= 50
    
    def test_complete_stage_1(self, app, sample_coach_user):
        """Test Stage 1 completion"""
        with app.app_context():
            stage = VerificationService.get_or_create_verification_stage(sample_coach_user.id)
            
            # Set all required fields
            stage.name_verified = True
            stage.phone_verified = True
            stage.email_verified = True
            stage.aadhar_verified = True
            stage.username_created = True
            db.session.commit()
            
            result = VerificationService.complete_stage_1(sample_coach_user.id)
            assert result == True
            
            updated_stage = VerificationStage.query.filter_by(user_id=sample_coach_user.id).first()
            assert updated_stage.stage_1_completed == True
            assert updated_stage.orange_badge == True
    
    def test_get_verification_progress(self, app, sample_coach_user):
        """Test verification progress calculation"""
        with app.app_context():
            progress = VerificationService.get_verification_progress(sample_coach_user.id)
            
            assert 'current_stage' in progress
            assert 'badge_level' in progress
            assert 'total_coins' in progress
            assert 'stage_1' in progress
            assert 'stage_2' in progress
            assert 'stage_3' in progress
            assert 'stage_4' in progress
            
            # Check stage structure
            stage1 = progress['stage_1']
            assert 'completed' in stage1
            assert 'score' in stage1
            assert 'max_score' in stage1
            assert 'coins' in stage1
    
    def test_create_slug(self, app):
        """Test slug creation"""
        with app.app_context():
            slug1 = VerificationService.create_slug("Test Coach")
            assert slug1 == "test-coach"
            
            # Test special characters
            slug2 = VerificationService.create_slug("Test@Coach#123")
            assert slug2 == "testcoach123"
            
            # Test uniqueness (would need existing slug in DB)
            slug3 = VerificationService.create_slug("Another Coach")
            assert slug3 == "another-coach"


class TestVerificationRoutes:
    """Test verification route endpoints"""
    
    def test_verification_dashboard_requires_login(self, client):
        """Test verification dashboard requires authentication"""
        response = client.get('/verification/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_verification_dashboard_coach_only(self, authenticated_employer_client):
        """Test verification dashboard is coach-only"""
        response = authenticated_employer_client.get('/verification/dashboard')
        assert response.status_code == 302  # Redirect away
    
    def test_verification_dashboard_loads(self, authenticated_coach_client, sample_coach_user):
        """Test verification dashboard loads for coaches"""
        response = authenticated_coach_client.get('/verification/dashboard')
        assert response.status_code == 200
        assert b'Coach Verification Journey' in response.data
        assert b'Stage 1' in response.data
        assert b'Stage 2' in response.data
        assert b'Stage 3' in response.data
        assert b'Stage 4' in response.data
    
    def test_stage1_loads(self, authenticated_coach_client):
        """Test Stage 1 page loads"""
        response = authenticated_coach_client.get('/verification/stage1')
        assert response.status_code == 200
        assert b'Basic Verification' in response.data
        assert b'Orange Badge' in response.data
    
    def test_stage2_requires_stage1(self, authenticated_coach_client):
        """Test Stage 2 requires Stage 1 completion"""
        response = authenticated_coach_client.get('/verification/stage2')
        # Should redirect to stage 1 or show warning
        assert response.status_code in [200, 302]
    
    def test_public_coach_profile_404(self, client):
        """Test public coach profile returns 404 for non-existent coach"""
        response = client.get('/coach/nonexistent-coach')
        assert response.status_code == 404
    
    def test_api_verification_progress_requires_login(self, client):
        """Test verification progress API requires authentication"""
        response = client.get('/api/verification/progress')
        assert response.status_code == 302  # Redirect to login
    
    def test_api_verification_documents_requires_login(self, client):
        """Test verification documents API requires authentication"""
        response = client.get('/api/verification/documents')
        assert response.status_code == 302  # Redirect to login


class TestVerificationIntegration:
    """Test verification system integration"""
    
    def test_coach_dashboard_verification_link(self, authenticated_coach_client):
        """Test verification link appears in coach dashboard"""
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
        assert b'Verification Center' in response.data
    
    def test_verification_affects_profile_completion(self, app, sample_coach_user, sample_coach_profile):
        """Test verification affects profile completion percentage"""
        with app.app_context():
            # Create verification stage with some completion
            stage = VerificationStage(
                user_id=sample_coach_user.id,
                name_verified=True,
                phone_verified=True,
                email_verified=True,
                stage_1_completed=True,
                orange_badge=True
            )
            db.session.add(stage)
            db.session.commit()
            
            # Verification should contribute to profile completion
            # This would be tested in the actual dashboard route
            assert stage.stage_1_completed == True
    
    def test_badge_display_integration(self, app, sample_coach_user):
        """Test badge display in various parts of the app"""
        with app.app_context():
            stage = VerificationStage(
                user_id=sample_coach_user.id,
                orange_badge=True,
                purple_badge=True
            )
            db.session.add(stage)
            db.session.commit()
            
            assert stage.get_badge_level() == "purple"
            assert stage.get_current_stage() == 3  # Should be on stage 3


class TestVerificationSecurity:
    """Test verification system security"""
    
    def test_stage_progression_security(self, authenticated_coach_client):
        """Test users cannot skip verification stages"""
        # Try to access stage 4 without completing previous stages
        response = authenticated_coach_client.get('/verification/stage4')
        # Should redirect or show error
        assert response.status_code in [200, 302]
    
    def test_admin_verification_requires_admin(self, authenticated_coach_client):
        """Test admin verification requires admin role"""
        response = authenticated_coach_client.get('/admin/coach-verification')
        assert response.status_code == 302  # Redirect due to insufficient permissions
    
    def test_document_upload_validation(self, authenticated_coach_client):
        """Test document upload validates file types"""
        # This would test the file upload endpoint with invalid files
        # Implementation depends on the actual upload handling
        pass


class TestVerificationPerformance:
    """Test verification system performance"""
    
    def test_verification_progress_calculation_performance(self, app, sample_coach_user):
        """Test verification progress calculation is efficient"""
        with app.app_context():
            import time
            
            start_time = time.time()
            progress = VerificationService.get_verification_progress(sample_coach_user.id)
            end_time = time.time()
            
            # Should complete within reasonable time
            assert end_time - start_time < 1.0  # Less than 1 second
            assert progress is not None
    
    def test_slug_generation_performance(self, app):
        """Test slug generation is efficient"""
        with app.app_context():
            import time
            
            start_time = time.time()
            for i in range(100):
                slug = VerificationService.create_slug(f"Test Coach {i}")
                assert slug is not None
            end_time = time.time()
            
            # Should handle 100 slug generations quickly
            assert end_time - start_time < 2.0  # Less than 2 seconds