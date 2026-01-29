"""
Test configuration and fixtures for KoachSmart admin testing
"""

import pytest
import tempfile
import os
from core.app_factory import create_app
from core.extensions import db


@pytest.fixture
def app():
    """Create application for testing"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    # Test configuration
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'LOGIN_DISABLED': False,
        # Disable mail for testing
        'MAIL_SUPPRESS_SEND': True,
        'MAIL_DEFAULT_SENDER': 'test@example.com',
    }
    
    # Create app with test config
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        
        # Cleanup
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers():
    """Common authentication headers for API testing"""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }