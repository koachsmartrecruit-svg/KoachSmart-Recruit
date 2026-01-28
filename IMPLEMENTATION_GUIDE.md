# Khelo Coach Application - Implementation Guide

## Quick Start

### 1. Environment Setup

```bash
# Clone/navigate to project directory
cd khelo-coach-new

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 2. Database Setup

```bash
# Create database tables
python -c "from core.app_factory import create_app; from core.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"

# Or run migration if exists
python migrations/run_migration.py
```

### 3. Environment Variables

Create `.env` file:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/khelo_coach.db
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### 4. Run Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific category
python tests/run_tests.py auth
python tests/run_tests.py profile
python tests/run_tests.py jobs

# Run specific test file
python tests/run_tests.py test_dashboard.py
```

### 5. Start Application

```bash
python app.py
```

Visit: http://127.0.0.1:5000

## Testing Strategy

### Phase 1: Critical Tests (Must Pass)
1. **Authentication Tests**
   ```bash
   python tests/run_tests.py auth
   ```
   - User registration
   - Login/logout
   - Password reset
   - Access control

2. **Profile Tests**
   ```bash
   python tests/run_tests.py profile
   ```
   - Profile creation
   - Profile completion calculation
   - File uploads
   - Data validation

3. **Dashboard Tests**
   ```bash
   python tests/run_tests.py dashboard
   ```
   - Dashboard loading
   - Data display
   - Navigation
   - Role-based access

### Phase 2: Feature Tests (Should Pass)
4. **Job Management Tests**
   ```bash
   python tests/run_tests.py jobs
   ```
   - Job creation
   - Job applications
   - Filtering
   - Status updates

5. **Resume Builder Tests**
   ```bash
   python tests/run_tests.py resume
   ```
   - Resume generation
   - Text parsing
   - Output formatting
   - API functionality

### Phase 3: Integration Tests
6. **End-to-End Tests**
   - Complete user workflows
   - Cross-feature integration
   - Performance testing

## Manual Testing Checklist

### 1. User Registration & Login
- [ ] Register new coach account
- [ ] Register new employer account
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Logout functionality
- [ ] Password reset flow

### 2. Coach Profile Management
- [ ] Complete profile onboarding
- [ ] Upload resume, certificates, ID proof
- [ ] Edit profile information
- [ ] View profile completion percentage
- [ ] Profile verification status

### 3. Job Management
- [ ] Employer creates job posting
- [ ] Coach views job listings
- [ ] Coach applies to jobs
- [ ] Application status updates
- [ ] Job filtering works

### 4. Dashboard Functionality
- [ ] Coach dashboard loads correctly
- [ ] Employer dashboard loads correctly
- [ ] Admin dashboard loads correctly
- [ ] All statistics display correctly
- [ ] Navigation links work

### 5. Resume Builder
- [ ] Resume builder page loads
- [ ] Text input accepts Hindi/English
- [ ] Resume generates correctly
- [ ] PDF download works
- [ ] Resume saves to profile

### 6. Communication Features
- [ ] Chat system works
- [ ] Email notifications sent
- [ ] File uploads in chat
- [ ] Real-time messaging

### 7. Payment System
- [ ] Payment plans display
- [ ] Stripe integration works
- [ ] Payment processing
- [ ] Subscription status updates

## Common Issues & Solutions

### 1. Database Issues
**Problem**: Tables not created
```bash
# Solution: Create tables manually
python -c "from core.app_factory import create_app; from core.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

**Problem**: Migration errors
```bash
# Solution: Reset database
rm instance/khelo_coach.db
python -c "from core.app_factory import create_app; from core.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 2. Template Errors
**Problem**: `UndefinedError: 'variable' is undefined`
- Check route passes all required variables
- Update template to handle missing variables
- Add default values in route

### 3. Import Errors
**Problem**: Module not found
```bash
# Solution: Install missing dependencies
pip install -r requirements.txt

# Or install specific package
pip install flask-login flask-mail
```

### 4. File Upload Issues
**Problem**: File uploads fail
- Check upload directories exist
- Verify file size limits
- Check file permissions

### 5. Email Issues
**Problem**: Emails not sending
- Verify MAIL_USERNAME and MAIL_PASSWORD
- Enable 2FA and use app password for Gmail
- Check firewall/network settings

## Performance Optimization

### 1. Database Optimization
```python
# Add indexes to frequently queried fields
class Job(db.Model):
    # Add indexes
    __table_args__ = (
        db.Index('idx_job_sport', 'sport'),
        db.Index('idx_job_location', 'location'),
        db.Index('idx_job_active', 'is_active'),
    )
```

### 2. Query Optimization
```python
# Use eager loading to reduce queries
jobs = Job.query.options(
    db.joinedload(Job.employer)
).filter_by(is_active=True).all()
```

### 3. Caching
```python
# Add caching for frequently accessed data
from flask_caching import Cache
cache = Cache(app)

@cache.memoize(timeout=300)
def get_active_jobs():
    return Job.query.filter_by(is_active=True).all()
```

## Security Checklist

### 1. Input Validation
- [ ] All forms validate input
- [ ] File uploads are secure
- [ ] SQL injection protection
- [ ] XSS protection

### 2. Authentication
- [ ] Password hashing
- [ ] Session management
- [ ] CSRF protection
- [ ] Rate limiting

### 3. Authorization
- [ ] Role-based access control
- [ ] Resource ownership checks
- [ ] Admin privilege verification

### 4. Data Protection
- [ ] Sensitive data encryption
- [ ] Secure file storage
- [ ] Database security
- [ ] API security

## Deployment Checklist

### 1. Production Environment
- [ ] Set production SECRET_KEY
- [ ] Configure production database
- [ ] Set up email service
- [ ] Configure file storage
- [ ] Set up SSL/HTTPS

### 2. Server Configuration
- [ ] Use production WSGI server (Gunicorn)
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Set up backups

### 3. Performance
- [ ] Enable gzip compression
- [ ] Configure caching
- [ ] Optimize database
- [ ] CDN for static files
- [ ] Monitor performance

## Monitoring & Maintenance

### 1. Application Monitoring
```python
# Add health check endpoint
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow()}
```

### 2. Error Tracking
```python
# Add error logging
import logging
logging.basicConfig(level=logging.INFO)

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return render_template('error.html'), 500
```

### 3. Database Maintenance
```bash
# Regular database backups
sqlite3 instance/khelo_coach.db ".backup backup_$(date +%Y%m%d).db"

# Database optimization
sqlite3 instance/khelo_coach.db "VACUUM;"
```

## Next Steps

1. **Run Phase 1 Tests** - Ensure critical functionality works
2. **Manual Testing** - Test user workflows manually
3. **Fix Issues** - Address any failing tests or bugs
4. **Run Phase 2 Tests** - Test additional features
5. **Performance Testing** - Test with multiple users
6. **Security Review** - Conduct security audit
7. **Deployment** - Deploy to production environment

## Support

For issues or questions:
1. Check test results for specific error messages
2. Review logs in console output
3. Check database for data consistency
4. Verify environment variables are set correctly
5. Ensure all dependencies are installed