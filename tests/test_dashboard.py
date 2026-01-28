"""
Dashboard functionality tests
"""
import pytest
from flask import url_for


class TestCoachDashboard:
    """Test coach dashboard functionality"""
    
    def test_coach_dashboard_loads(self, authenticated_coach_client, sample_coach_profile):
        """Test coach dashboard loads without errors"""
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
        assert b'Welcome back' in response.data or b'Dashboard' in response.data
    
    def test_profile_completion_display(self, authenticated_coach_client, sample_coach_profile):
        """Test profile completion percentage displays"""
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
        # Should contain profile completion percentage
        assert b'%' in response.data
    
    def test_job_recommendations_display(self, authenticated_coach_client, sample_job):
        """Test job recommendations appear on dashboard"""
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
        # Should show available jobs
        assert b'job' in response.data.lower() or b'opportunity' in response.data.lower()
    
    def test_application_history_display(self, authenticated_coach_client, app, sample_job, sample_coach_user):
        """Test application history displays correctly"""
        with app.app_context():
            from models.application import Application
            from core.extensions import db
            
            # Create an application
            application = Application(
                job_id=sample_job.id,
                user_id=sample_coach_user.id,
                match_score=85,
                status='Applied'
            )
            db.session.add(application)
            db.session.commit()
        
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
        # Should show application count
    
    def test_quick_actions_present(self, authenticated_coach_client):
        """Test quick action buttons are present"""
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
        # Should have resume builder and other quick actions
        assert b'Resume' in response.data or b'Profile' in response.data
    
    def test_referral_system_display(self, authenticated_coach_client, sample_coach_user):
        """Test referral system displays on dashboard"""
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
        # Should show referral code
        if hasattr(sample_coach_user, 'referral_code'):
            assert sample_coach_user.referral_code.encode() in response.data


class TestEmployerDashboard:
    """Test employer dashboard functionality"""
    
    def test_employer_dashboard_loads(self, authenticated_employer_client):
        """Test employer dashboard loads without errors"""
        response = authenticated_employer_client.get('/employer/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Welcome' in response.data
    
    def test_posted_jobs_display(self, authenticated_employer_client, sample_job):
        """Test posted jobs display on employer dashboard"""
        response = authenticated_employer_client.get('/employer/dashboard')
        assert response.status_code == 200
        # Should show posted jobs
        assert sample_job.title.encode() in response.data or b'job' in response.data.lower()
    
    def test_applications_received_display(self, authenticated_employer_client, app, sample_job, sample_coach_user):
        """Test applications received display"""
        with app.app_context():
            from models.application import Application
            from core.extensions import db
            
            # Create an application to employer's job
            application = Application(
                job_id=sample_job.id,
                user_id=sample_coach_user.id,
                match_score=85,
                status='Applied'
            )
            db.session.add(application)
            db.session.commit()
        
        response = authenticated_employer_client.get('/employer/dashboard')
        assert response.status_code == 200
        # Should show applications received


class TestAdminDashboard:
    """Test admin dashboard functionality"""
    
    def test_admin_dashboard_loads(self, authenticated_admin_client):
        """Test admin dashboard loads without errors"""
        response = authenticated_admin_client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Admin' in response.data or b'Dashboard' in response.data
    
    def test_user_management_access(self, authenticated_admin_client):
        """Test admin can access user management"""
        response = authenticated_admin_client.get('/admin/users')
        assert response.status_code == 200
        assert b'Users' in response.data or b'user' in response.data.lower()
    
    def test_job_management_access(self, authenticated_admin_client):
        """Test admin can access job management"""
        response = authenticated_admin_client.get('/admin/jobs')
        assert response.status_code == 200
        assert b'Jobs' in response.data or b'job' in response.data.lower()


class TestDashboardNavigation:
    """Test dashboard navigation functionality"""
    
    def test_coach_navigation_links(self, authenticated_coach_client):
        """Test coach dashboard navigation links work"""
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
        
        # Test profile edit link
        response = authenticated_coach_client.get('/profile/edit')
        assert response.status_code == 200 or response.status_code == 302
    
    def test_job_application_modal(self, authenticated_coach_client, sample_job):
        """Test job application functionality"""
        # Test applying to a job
        response = authenticated_coach_client.post(f'/job/apply/{sample_job.id}')
        assert response.status_code == 200 or response.status_code == 302
    
    def test_resume_builder_access(self, authenticated_coach_client):
        """Test resume builder access from dashboard"""
        response = authenticated_coach_client.get('/resume-builder')
        assert response.status_code == 200
        assert b'Resume' in response.data


class TestDashboardData:
    """Test dashboard data accuracy"""
    
    def test_profile_views_counter(self, authenticated_coach_client, app, sample_coach_profile):
        """Test profile views counter accuracy"""
        with app.app_context():
            initial_views = sample_coach_profile.views
            
            # Simulate profile view increment
            sample_coach_profile.views += 1
            from core.extensions import db
            db.session.commit()
        
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
        # Views should be displayed
    
    def test_application_count_accuracy(self, authenticated_coach_client, app, sample_job, sample_coach_user):
        """Test application count accuracy"""
        with app.app_context():
            from models.application import Application
            from core.extensions import db
            
            # Create multiple applications
            app1 = Application(job_id=sample_job.id, user_id=sample_coach_user.id, match_score=80)
            db.session.add(app1)
            db.session.commit()
            
            # Check count on dashboard
            applications_count = Application.query.filter_by(user_id=sample_coach_user.id).count()
            assert applications_count >= 1
        
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200


class TestDashboardResponsiveness:
    """Test dashboard mobile responsiveness"""
    
    def test_mobile_dashboard_loads(self, authenticated_coach_client):
        """Test dashboard loads on mobile viewport"""
        # Simulate mobile user agent
        response = authenticated_coach_client.get('/dashboard', headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        })
        assert response.status_code == 200
        # Should contain responsive elements
        assert b'container' in response.data or b'responsive' in response.data
    
    def test_dashboard_css_loads(self, authenticated_coach_client):
        """Test dashboard CSS loads correctly"""
        response = authenticated_coach_client.get('/static/css/style.css')
        assert response.status_code == 200
        assert b'css' in response.headers.get('Content-Type', b'').lower()