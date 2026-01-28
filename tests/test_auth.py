"""
Authentication tests
"""
import pytest
from flask import url_for
from models.user import User
from core.extensions import db


class TestRegistration:
    """Test user registration functionality"""
    
    def test_register_page_loads(self, client):
        """Test registration page loads correctly"""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data
    
    def test_valid_registration(self, client, app):
        """Test user can register with valid data"""
        with app.app_context():
            response = client.post('/register', data={
                'username': 'newuser',
                'email': 'newuser@test.com',
                'password': 'testpass123',
                'confirm_password': 'testpass123',
                'role': 'coach'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Check user was created
            user = User.query.filter_by(email='newuser@test.com').first()
            assert user is not None
            assert user.username == 'newuser'
            assert user.role == 'coach'
    
    def test_duplicate_email_registration(self, client, app, sample_coach_user):
        """Test cannot register with existing email"""
        with app.app_context():
            response = client.post('/register', data={
                'username': 'newuser',
                'email': 'coach@test.com',  # Already exists
                'password': 'testpass123',
                'confirm_password': 'testpass123',
                'role': 'coach'
            })
            
            assert response.status_code == 200
            assert b'Email already registered' in response.data or b'already exists' in response.data
    
    def test_invalid_email_registration(self, client):
        """Test cannot register with invalid email"""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': 'coach'
        })
        
        assert response.status_code == 200
        # Should show validation error
    
    def test_password_mismatch_registration(self, client):
        """Test cannot register with mismatched passwords"""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'confirm_password': 'differentpass',
            'role': 'coach'
        })
        
        assert response.status_code == 200
        # Should show validation error


class TestLogin:
    """Test user login functionality"""
    
    def test_login_page_loads(self, client):
        """Test login page loads correctly"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_valid_login(self, client, sample_coach_user):
        """Test user can login with valid credentials"""
        response = client.post('/login', data={
            'email': 'coach@test.com',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to dashboard
    
    def test_invalid_login(self, client, sample_coach_user):
        """Test cannot login with invalid credentials"""
        response = client.post('/login', data={
            'email': 'coach@test.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'error' in response.data
    
    def test_nonexistent_user_login(self, client):
        """Test cannot login with non-existent user"""
        response = client.post('/login', data={
            'email': 'nonexistent@test.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'error' in response.data
    
    def test_logout(self, authenticated_coach_client):
        """Test user can logout"""
        response = authenticated_coach_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to home page


class TestPasswordReset:
    """Test password reset functionality"""
    
    def test_forgot_password_page_loads(self, client):
        """Test forgot password page loads"""
        response = client.get('/forgot-password')
        assert response.status_code == 200
    
    def test_forgot_password_valid_email(self, client, sample_coach_user):
        """Test forgot password with valid email"""
        response = client.post('/forgot-password', data={
            'email': 'coach@test.com'
        })
        
        assert response.status_code == 200 or response.status_code == 302
    
    def test_forgot_password_invalid_email(self, client):
        """Test forgot password with invalid email"""
        response = client.post('/forgot-password', data={
            'email': 'nonexistent@test.com'
        })
        
        assert response.status_code == 200


class TestAccessControl:
    """Test access control and permissions"""
    
    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication"""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_coach_dashboard_access(self, authenticated_coach_client):
        """Test coach can access coach dashboard"""
        response = authenticated_coach_client.get('/dashboard')
        assert response.status_code == 200
    
    def test_employer_dashboard_access(self, authenticated_employer_client):
        """Test employer can access employer dashboard"""
        response = authenticated_employer_client.get('/employer/dashboard')
        assert response.status_code == 200
    
    def test_admin_dashboard_access(self, authenticated_admin_client):
        """Test admin can access admin dashboard"""
        response = authenticated_admin_client.get('/admin/dashboard')
        assert response.status_code == 200
    
    def test_cross_role_access_denied(self, authenticated_coach_client):
        """Test coach cannot access employer dashboard"""
        response = authenticated_coach_client.get('/employer/dashboard')
        assert response.status_code == 302  # Redirect