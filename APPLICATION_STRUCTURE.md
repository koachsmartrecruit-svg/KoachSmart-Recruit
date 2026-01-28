# Khelo Coach Application - Complete Structure

## Project Overview

Khelo Coach is a comprehensive sports coaching platform that connects coaches with employers (academies, clubs, schools). The platform includes profile management, job matching, resume building, communication tools, and payment processing.

## Architecture

```
khelo-coach-new/
├── app.py                          # Application entry point
├── core/                           # Core application modules
│   ├── app_factory.py             # Flask app factory
│   ├── extensions.py              # Flask extensions
│   ├── constants.py               # Application constants
│   └── access_guard.py            # Access control middleware
├── models/                         # Database models
│   ├── user.py                    # User model
│   ├── profile.py                 # Coach profile model
│   ├── hirer.py                   # Employer profile model
│   ├── job.py                     # Job posting model
│   ├── application.py             # Job application model
│   ├── message.py                 # Chat message model
│   └── rewards.py                 # Rewards/referral model
├── routes/                         # Route handlers
│   ├── auth_routes.py             # Authentication routes
│   ├── coach_routes.py            # Coach-specific routes
│   ├── employer_routes.py         # Employer-specific routes
│   ├── admin_routes.py            # Admin routes
│   ├── onboarding_routes.py       # Profile onboarding
│   ├── chat_routes.py             # Chat functionality
│   ├── payment_routes.py          # Payment processing
│   └── public_routes.py           # Public pages
├── services/                       # Business logic services
│   ├── ai_service.py              # AI matching service
│   ├── email_service.py           # Email notifications
│   ├── file_service.py            # File upload handling
│   ├── sheets_service.py          # Google Sheets integration
│   ├── reward_service.py          # Referral system
│   └── otp_service.py             # OTP verification
├── templates/                      # Jinja2 templates
│   ├── base.html                  # Base template
│   ├── home.html                  # Landing page
│   ├── login.html                 # Login page
│   ├── register.html              # Registration page
│   ├── coach_listing.html         # Coach dashboard
│   ├── employer_dashboard.html    # Employer dashboard
│   ├── resume_builder.html        # Resume builder
│   └── components/                # Reusable components
├── static/                         # Static assets
│   ├── css/style.css              # Main stylesheet
│   ├── images/                    # Images
│   ├── uploads/                   # User uploads
│   ├── resumes/                   # Generated resumes
│   └── certs/                     # Certificates
├── validators/                     # Input validation
│   ├── common_validator.py        # Common validations
│   ├── phone_validator.py         # Phone validation
│   └── document_validator.py      # Document validation
├── tests/                          # Test suite
│   ├── conftest.py                # Test configuration
│   ├── test_auth.py               # Authentication tests
│   ├── test_profile.py            # Profile tests
│   ├── test_jobs.py               # Job management tests
│   ├── test_dashboard.py          # Dashboard tests
│   └── test_resume_builder.py     # Resume builder tests
├── migrations/                     # Database migrations
├── credentials/                    # API credentials
├── instance/                       # Instance-specific files
│   └── khelo_coach.db             # SQLite database
├── requirements.txt                # Python dependencies
├── requirements-test.txt           # Testing dependencies
├── .env                           # Environment variables
└── README.md                      # Project documentation
```

## Core Components

### 1. User Management System

**Models:**
- `User`: Base user model with authentication
- `Profile`: Coach profile with skills, experience, documents
- `Hirer`: Employer profile with company information

**Features:**
- Registration with email verification
- Role-based access (coach, employer, admin)
- Profile completion tracking
- Document upload and verification
- Password reset functionality

### 2. Job Management System

**Models:**
- `Job`: Job postings with requirements and details
- `Application`: Job applications with match scoring

**Features:**
- Job posting creation and management
- AI-powered job matching
- Application tracking and status updates
- Filtering and search functionality
- Screening questions support

### 3. Dashboard System

**Coach Dashboard:**
- Profile completion status
- Job recommendations
- Application history
- Performance metrics
- Quick actions (resume builder, profile edit)

**Employer Dashboard:**
- Posted jobs management
- Applications received
- Candidate filtering
- Interview scheduling
- Company profile management

**Admin Dashboard:**
- User management and verification
- Job moderation
- System analytics
- Content management

### 4. Resume Builder

**Features:**
- AI-powered resume generation
- Multi-language support (Hindi/English)
- Text parsing and information extraction
- Professional template formatting
- PDF generation and download
- Integration with profile data

### 5. Communication System

**Features:**
- Real-time chat between coaches and employers
- File sharing in conversations
- Email notifications
- Interview scheduling
- Application status updates

### 6. Payment System

**Features:**
- Subscription plans for premium features
- Stripe payment integration
- Payment history tracking
- Webhook handling for payment events
- Referral rewards system

## Database Schema

### Core Tables

```sql
-- Users table
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Coach profiles
CREATE TABLE profile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    full_name VARCHAR(150),
    phone VARCHAR(20),
    bio TEXT,
    sport VARCHAR(100),
    experience_years INTEGER,
    city VARCHAR(100),
    resume_path VARCHAR(300),
    is_verified BOOLEAN DEFAULT FALSE,
    views INTEGER DEFAULT 0
);

-- Job postings
CREATE TABLE job (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    sport VARCHAR(100),
    location VARCHAR(200),
    salary_range VARCHAR(100),
    employer_id INTEGER REFERENCES user(id),
    is_active BOOLEAN DEFAULT TRUE,
    posted_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Job applications
CREATE TABLE application (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES job(id),
    user_id INTEGER REFERENCES user(id),
    match_score INTEGER,
    status VARCHAR(50) DEFAULT 'Applied',
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout
- `POST /forgot-password` - Password reset request
- `POST /reset-password` - Password reset confirmation

### Coach Routes
- `GET /dashboard` - Coach dashboard
- `GET /jobs` - Job listings with filters
- `POST /job/apply/<id>` - Apply to job
- `GET /profile/edit` - Edit profile page
- `GET /resume-builder` - Resume builder page
- `POST /text-to-resume` - Resume generation API

### Employer Routes
- `GET /employer/dashboard` - Employer dashboard
- `POST /employer/job/new` - Create job posting
- `GET /employer/applications` - View applications
- `POST /employer/application/<id>/status` - Update application status

### Admin Routes
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - User management
- `GET /admin/jobs` - Job management
- `POST /admin/verify/<user_id>` - Verify user profile

## Key Features Implementation

### 1. Profile Completion Calculation

```python
def calculate_profile_completion(profile):
    total_fields = 10
    completed_fields = 0
    
    if profile.full_name: completed_fields += 1
    if profile.phone: completed_fields += 1
    if profile.bio: completed_fields += 1
    if profile.sport: completed_fields += 1
    if profile.experience_years: completed_fields += 1
    if profile.city: completed_fields += 1
    if profile.resume_path: completed_fields += 1
    if profile.certifications: completed_fields += 1
    if profile.working_type: completed_fields += 1
    if profile.is_verified: completed_fields += 1
    
    return int((completed_fields / total_fields) * 100)
```

### 2. Job Matching Algorithm

```python
def calculate_match_score(profile, job):
    score = 0
    reasons = []
    
    # Sport match (40% weight)
    if profile.sport == job.sport:
        score += 40
        reasons.append(f"Perfect sport match: {job.sport}")
    
    # Location match (30% weight)
    if profile.city and job.location:
        if profile.city.lower() in job.location.lower():
            score += 30
            reasons.append(f"Location match: {job.location}")
    
    # Experience match (20% weight)
    if profile.experience_years:
        if profile.experience_years >= 3:
            score += 20
            reasons.append("Good experience level")
    
    # Verification bonus (10% weight)
    if profile.is_verified:
        score += 10
        reasons.append("Verified profile")
    
    return min(score, 100), "; ".join(reasons)
```

### 3. Resume Text Parsing

```python
def parse_resume_text(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    resume_data = {
        "full_name": "Professional Coach",
        "headline": "Sports Coach",
        "summary": "Experienced sports coach with passion for developing athletes.",
        "skills": ["Coaching", "Team Management", "Player Development"],
        "experience": [],
        "certifications": [],
        "achievements": []
    }
    
    # Extract name
    for line in lines:
        if any(word in line.lower() for word in ['नाम', 'name', 'मैं']):
            words = line.split()
            if len(words) > 2:
                resume_data["full_name"] = " ".join(words[-2:])
    
    # Extract certifications
    for line in lines:
        if any(word in line.lower() for word in ['certified', 'level']):
            resume_data["certifications"].append(line)
    
    return resume_data
```

## Security Implementation

### 1. Authentication & Authorization

```python
from flask_login import login_required, current_user
from functools import wraps

def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@coach_bp.route('/dashboard')
@role_required('coach')
def dashboard():
    # Coach-only route
    pass
```

### 2. Input Validation

```python
from validators.common_validator import validate_email, validate_phone

def validate_profile_data(data):
    errors = []
    
    if not validate_email(data.get('email')):
        errors.append('Invalid email format')
    
    if not validate_phone(data.get('phone')):
        errors.append('Invalid phone number')
    
    return errors
```

### 3. File Upload Security

```python
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_file_upload(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Additional security checks
        return filename
    return None
```

## Performance Optimizations

### 1. Database Indexing

```python
class Job(db.Model):
    __table_args__ = (
        db.Index('idx_job_sport_location', 'sport', 'location'),
        db.Index('idx_job_active', 'is_active'),
        db.Index('idx_job_employer', 'employer_id'),
    )
```

### 2. Query Optimization

```python
# Use eager loading to reduce N+1 queries
jobs = Job.query.options(
    db.joinedload(Job.employer),
    db.joinedload(Job.applications)
).filter_by(is_active=True).all()
```

### 3. Caching Strategy

```python
from flask_caching import Cache

cache = Cache()

@cache.memoize(timeout=300)
def get_job_statistics():
    return {
        'total_jobs': Job.query.count(),
        'active_jobs': Job.query.filter_by(is_active=True).count(),
        'total_applications': Application.query.count()
    }
```

## Deployment Architecture

### Production Stack
- **Web Server**: Nginx (reverse proxy, static files)
- **Application Server**: Gunicorn (WSGI server)
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache**: Redis (session storage, caching)
- **File Storage**: AWS S3 or local storage
- **Email**: SendGrid or SMTP
- **Monitoring**: Application logs, health checks

### Configuration Management
- Environment-specific settings
- Secret management
- Database connection pooling
- SSL/TLS configuration
- Rate limiting and security headers

This comprehensive structure provides a solid foundation for the Khelo Coach platform with scalability, security, and maintainability in mind.