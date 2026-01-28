"""
Basic functionality tests to verify setup
"""
import pytest


class TestBasicSetup:
    """Test basic application setup"""
    
    def test_app_exists(self, app):
        """Test that the Flask app is created"""
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_database_connection(self, app):
        """Test database connection works"""
        with app.app_context():
            from core.extensions import db
            # Simple query to test connection
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1")).fetchone()
                assert result[0] == 1
    
    def test_home_page_loads(self, client):
        """Test home page loads"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_login_page_loads(self, client):
        """Test login page loads"""
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_register_page_loads(self, client):
        """Test register page loads"""
        response = client.get('/register')
        assert response.status_code == 200


class TestUserModel:
    """Test User model basic functionality"""
    
    def test_create_user(self, app):
        """Test creating a user"""
        with app.app_context():
            from models.user import User
            from core.extensions import db
            from werkzeug.security import generate_password_hash
            
            user = User(
                username='testuser',
                email='test@example.com',
                role='coach',
                password=generate_password_hash('testpass')
            )
            db.session.add(user)
            db.session.commit()
            
            # Verify user was created
            saved_user = User.query.filter_by(email='test@example.com').first()
            assert saved_user is not None
            assert saved_user.username == 'testuser'
            assert saved_user.role == 'coach'
    
    def test_user_password_hashing(self, app):
        """Test password hashing works"""
        with app.app_context():
            from models.user import User
            from core.extensions import db
            from werkzeug.security import generate_password_hash, check_password_hash
            
            password = 'testpassword123'
            hashed = generate_password_hash(password)
            
            user = User(
                username='testuser2',
                email='test2@example.com',
                role='coach',
                password=hashed
            )
            db.session.add(user)
            db.session.commit()
            
            # Verify password checking works
            saved_user = User.query.filter_by(email='test2@example.com').first()
            assert check_password_hash(saved_user.password, password)
            assert not check_password_hash(saved_user.password, 'wrongpassword')


class TestProfileModel:
    """Test Profile model basic functionality"""
    
    def test_create_profile(self, app):
        """Test creating a profile"""
        with app.app_context():
            from models.user import User
            from models.profile import Profile
            from core.extensions import db
            from werkzeug.security import generate_password_hash
            
            # Create user first
            user = User(
                username='profiletest',
                email='profile@example.com',
                role='coach',
                password=generate_password_hash('testpass')
            )
            db.session.add(user)
            db.session.commit()
            
            # Create profile
            profile = Profile(
                user_id=user.id,
                full_name='Test Coach',
                sport='Football',
                experience_years=5
            )
            db.session.add(profile)
            db.session.commit()
            
            # Verify profile was created
            saved_profile = Profile.query.filter_by(user_id=user.id).first()
            assert saved_profile is not None
            assert saved_profile.full_name == 'Test Coach'
            assert saved_profile.sport == 'Football'