# KoachSmart-Recruit

KoachSmart-Recruit is an AI-assisted hiring platform that connects sports academies with verified coaches, combining job posting, intelligent matching, real-time chat, and subscription billing.

## 🚀 Quick Start (15-Minute Setup)

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd khelo-coach-new
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env  # Configure your API keys and database URL
   ```

3. **Run Application**
   ```bash
   python app.py
   ```
   Access at: http://127.0.0.1:5000

## 📋 Changelog

### 2026-01-31 - Enhanced Onboarding & Location System

#### 🎯 **Major Features Implemented**
- **✅ Comprehensive 3-Step Onboarding System**
  - Mandatory onboarding enforcement via middleware
  - Progress tracking with step indicators and completion rewards
  - Badge system: Orange → Purple → Blue Verified progression
  - Coin rewards: 50-500 coins per milestone

- **✅ LocationIQ API Integration**
  - Migrated from Country State City API to LocationIQ
  - Dynamic country/state/city dropdowns with real-time loading
  - Geocoding and reverse geocoding capabilities
  - Fallback data for offline/demo mode

- **✅ Enhanced Language Proficiency System**
  - Multi-level language selection: Basic, Intermediate, Fluent
  - Read/Write/Speak proficiency tracking
  - Improved job matching based on language skills

- **✅ Referral System Implementation**
  - Automatic referral code generation
  - Milestone-based reward distribution (1000+ coins)
  - Comprehensive tracking and leaderboard functionality

#### 🔧 **Technical Improvements**
- **Database Schema Fixes**
  - Fixed `experience_years` column type mismatch (INTEGER → VARCHAR)
  - Applied comprehensive migration for all onboarding fields
  - Resolved PostgreSQL compatibility issues

- **Access Control Enhancement**
  - Updated access guards to allow API routes
  - Implemented onboarding completion enforcement
  - Protected coach routes until onboarding completion

- **UI/UX Improvements**
  - Simplified range fields (removed duplicate serviceable_area)
  - Conditional field display based on job type selection
  - Enhanced language selection with proficiency cards
  - Dynamic form validation and error handling

#### 🛡️ **Security & Code Quality**
- **Environment Variable Management**
  - All API keys properly externalized to .env
  - Zero hardcoded credentials in codebase
  - Secure configuration loading

- **Clean Code Implementation**
  - Self-descriptive function naming (e.g., `calculate_onboarding_progress`)
  - Functions kept under 30-line rule
  - Comprehensive error handling and logging

#### 🐛 **Bug Fixes**
- Fixed JavaScript error in location dropdowns (HTML vs JSON response)
- Resolved database connection issues with Neon PostgreSQL
- Fixed OTP verification system for demo mode
- Corrected route registration and blueprint conflicts

#### 📊 **Performance & Monitoring**
- Optimized location API calls with caching
- Enhanced error logging and debugging
- Improved database query efficiency
- Added comprehensive API status endpoints

---

## What this app does (non-technical)

- **Academies/employers can:**
  - Create accounts, post coaching jobs with location and detailed requirements
  - See ranked applicants with automatic "match score" and explanation
  - Update application status and send email notifications
  - Access premium features with subscription plans

- **Coaches can:**
  - Complete comprehensive 3-step onboarding with verification
  - Build rich coaching profiles with document uploads
  - Browse and filter jobs by sport, location, salary, and distance
  - Apply with custom resumes and screening question answers
  - Earn badges and coins through platform engagement

- **Platform features:**
  - In-app 1:1 chat with file sharing and real-time features
  - Subscription plans (Basic, Pro) using Stripe
  - Referral system with milestone rewards
  - Super-admin verification and platform-wide stats

## 🏗️ Architecture & Tech Stack

### **Backend Framework**
- **Flask** with modular blueprint architecture
- **Flask-Login** for authentication and session management
- **Flask-SocketIO** for real-time chat functionality
- **Flask-Mail** for email notifications

### **Database & ORM**
- **SQLAlchemy** ORM with PostgreSQL (Neon)
- **Alembic** for database migrations
- Optimized queries with relationship loading

### **Authentication & Security**
- Email/password + Google OAuth (Authlib)
- JWT tokens for API authentication
- Environment-based secret management
- CSRF protection and input validation

### **External Integrations**
- **Stripe** for subscription billing and webhooks
- **LocationIQ** for location services and geocoding
- **Google Sheets API** for data mirroring
- **Email services** for notifications and OTP

### **Document Processing**
- **PyPDF2** and **python-docx** for resume parsing
- Custom text extraction and keyword matching
- Secure file upload and storage

## 📊 Data Model (Simplified)

### **Core Entities**
- **`User`**: Authentication, roles, subscription status, onboarding progress
- **`Profile`**: Coach-specific data, verification status, documents, location
- **`Job`**: Employer job postings with requirements and location data
- **`Application`**: Coach-job relationships with match scores and status

### **Enhanced Features**
- **`ReferralSystem`**: Referral tracking and reward distribution
- **`Language`**: Multi-level language proficiency tracking
- **`Message`**: Real-time chat with file sharing capabilities
- **`Review`**: Employer feedback and rating system

## 🤖 AI and Automation

### **Intelligent Match Scoring**
- Multi-factor scoring: sport match, experience, location, certifications
- Keyword overlap analysis between requirements and qualifications
- Human-readable explanations for match scores

### **Dynamic Salary Suggestions**
- Sport-based salary recommendations
- Location-adjusted pricing (metro vs non-metro)
- Experience and job type considerations

### **Profile Completeness Analysis**
- 0-100% completion scoring
- Document upload tracking
- Verification status integration

## 🔄 Main User Flows

### **Coach Journey**
1. **Registration** → Email/Google OAuth signup
2. **3-Step Onboarding** → Basic info, location, professional details
3. **Profile Building** → Document uploads, verification
4. **Job Discovery** → Browse, filter, apply with match scores
5. **Communication** → Real-time chat with employers
6. **Progress Tracking** → Applications, interviews, rewards

### **Employer Journey**
1. **Registration** → Account creation and verification
2. **Subscription** → Choose Basic/Pro plan via Stripe
3. **Job Posting** → Create detailed job requirements
4. **Candidate Review** → AI-ranked applicants with scores
5. **Interview Process** → Status updates and communication
6. **Hiring Decision** → Final selection and feedback

### **Admin Operations**
1. **Verification Management** → Coach document review
2. **Platform Analytics** → User engagement and metrics
3. **Content Moderation** → Job and profile quality control

## ⚙️ Environment Configuration

### **Required Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Stripe Integration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email Configuration
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Google OAuth & Sheets
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_SHEETS_CREDENTIALS=path/to/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-sheet-id

# Location Services
LOCATIONIQ_API_KEY=pk.your-locationiq-key

# AI Services
OPENROUTER_API_KEY=sk-or-v1-your-key
```

## 🚀 Running Locally

### **Development Setup**
1. **Environment Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Configure DATABASE_URL in .env
   python -c "from core.app_factory import create_app; app = create_app(); app.app_context().push(); from core.extensions import db; db.create_all()"
   ```

3. **Run Application**
   ```bash
   python app.py
   ```

### **Production Deployment**
- Use WSGI server (Gunicorn recommended)
- Configure environment variables securely
- Set up SSL/TLS certificates
- Enable database connection pooling
- Configure monitoring and logging

## 🛡️ Security & Compliance

### **Data Protection**
- All sensitive data encrypted at rest
- API keys stored in secure environment variables
- Input validation and sanitization
- CSRF protection enabled

### **Access Control**
- Role-based permissions (Coach, Employer, Admin)
- Route-level authentication guards
- Session management with secure cookies

### **Code Quality Standards**
- **Clean Code Mandate**: Self-descriptive naming, 30-line function limit
- **Documentation Layer**: Comprehensive README and inline comments
- **IP Fortification**: Zero hardcoded credentials, dependency auditing

## 📈 Performance & Monitoring

### **Optimization Features**
- Database query optimization with eager loading
- API response caching for location data
- Efficient file upload handling
- Real-time features with WebSocket optimization

### **Monitoring & Logging**
- Comprehensive error logging
- Performance metrics tracking
- User engagement analytics
- System health monitoring

## 🤝 Contributing

### **Development Guidelines**
1. Follow the Guardrail Protocol for code quality
2. Maintain self-documenting code with clear naming
3. Keep functions under 30 lines
4. Add comprehensive error handling
5. Update documentation with changes

### **Code Review Process**
- All changes require review
- Automated linting and formatting
- Security vulnerability scanning
- Performance impact assessment

---

## 📞 Support & Contact

For technical support or questions about the platform, please refer to the documentation or contact the development team.

**Last Updated**: January 31, 2026  
**Version**: 2.0.0 - Enhanced Onboarding & Location System