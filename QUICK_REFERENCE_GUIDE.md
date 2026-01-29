# Quick Reference Guide - System Architecture

## 🎯 Key Concepts at a Glance

### Admin Hierarchy
```
Super Admin (Platform Owner)
├── Manage all admins
├── View all cities
├── Financial oversight
└── System configuration

Regional Admin (City-Level)
├── Verify coaches in assigned city
├── Approve/reject documents
├── Handle local issues
└── Generate local reports
```

### User Journey

```
COACH JOURNEY:
Registration → Mandatory Onboarding → Free Tier Access → Purchase Membership → Apply for Jobs

EMPLOYER JOURNEY:
Registration → Mandatory Onboarding → Free Tier Access → Purchase Membership → Post Jobs
```

### Onboarding vs Verification

| Aspect | Onboarding | Verification |
|--------|-----------|--------------|
| Mandatory | YES | NO |
| Purpose | Profile completion | Badge progression |
| Coins | 200 | 3500 |
| Badges | Orange (1) | Purple, Blue, Green (3) |
| Admin Role | None | Regional Admin |
| Time | 15-30 min | Days/Weeks |

### Membership Tiers

**Coach**:
- Free: 3 apps/month
- Premium (₹299/mo): Unlimited apps + featured profile
- Pro (₹599/mo): All features + revenue sharing

**Employer**:
- Free: 1 job/month
- Premium (₹999/mo): Unlimited jobs + featured listings
- Enterprise: Custom pricing + API access

---

## 📊 Database Models

### Admin Models
```python
Admin
├── user_id (FK)
├── role ('super_admin' or 'regional_admin')
├── assigned_cities (JSON)
├── permissions (JSON)
├── api_key
├── api_secret
└── activity_logs (relationship)

AdminActivityLog
├── admin_id (FK)
├── action
├── entity_type
├── entity_id
├── old_value (JSON)
└── new_value (JSON)
```

### Membership Models
```python
MembershipPlan
├── name
├── user_type ('coach' or 'employer')
├── price
├── duration_days
└── features (JSON)

UserSubscription
├── user_id (FK)
├── plan_id (FK)
├── status
├── start_date
├── end_date
└── auto_renew

OnboardingProgress
├── user_id (FK)
├── current_step
├── completed_steps (JSON)
├── coins_earned
└── badges_earned (JSON)
```

---

## 🔑 Key Features

### Admin Features
- ✅ Create and manage regional admins
- ✅ Assign cities to admins
- ✅ Track admin activities
- ✅ View performance metrics
- ✅ Generate reports
- ✅ Manage API credentials

### Onboarding Features
- ✅ Mandatory for all users
- ✅ 3 steps (Personal, Professional, Location)
- ✅ Coin rewards (200 total)
- ✅ Orange badge on completion
- ✅ Progress tracking
- ✅ Cannot skip

### Membership Features
- ✅ Multiple tiers
- ✅ Auto-renewal
- ✅ Feature restrictions
- ✅ Payment integration
- ✅ Subscription history
- ✅ Upgrade/downgrade

### Location Features
- ✅ No service radius for academies
- ✅ No service radius for coaches
- ✅ City-based matching
- ✅ Availability type selection
- ✅ Flexible scheduling

---

## 🚀 Quick Start

### Create Super Admin
```python
from models.user import User
from models.admin import Admin
from core.extensions import db

# Create user
user = User(
    username='superadmin',
    email='admin@koachsmart.com',
    password=generate_password_hash('password'),
    role='admin'
)
db.session.add(user)
db.session.commit()

# Create admin profile
admin = Admin(
    user_id=user.id,
    role='super_admin'
)
admin.generate_api_credentials()
db.session.add(admin)
db.session.commit()

print(f"API Key: {admin.api_key}")
print(f"API Secret: {admin.api_secret}")
```

### Create Regional Admin
```python
# Create user
user = User(
    username='mumbai_admin',
    email='mumbai@koachsmart.com',
    password=generate_password_hash('password'),
    role='admin'
)
db.session.add(user)
db.session.commit()

# Create admin profile
admin = Admin(
    user_id=user.id,
    role='regional_admin',
    assigned_cities=['Mumbai', 'Pune']
)
admin.generate_api_credentials()
db.session.add(admin)
db.session.commit()
```

### Create Membership Plans
```python
from models.membership import MembershipPlan

# Coach Premium Plan
plan = MembershipPlan(
    name='Premium',
    user_type='coach',
    price=299,
    duration_days=30,
    features={
        'browse_jobs': True,
        'applications_per_month': 999999,
        'featured_profile': True,
        'direct_messaging': True,
        'analytics': True,
        'coaching_tools': False,
        'revenue_sharing': False,
        'priority_support': False
    },
    monthly_applications=999999
)
db.session.add(plan)
db.session.commit()
```

### Subscribe User to Plan
```python
from models.membership import UserSubscription
from datetime import datetime, timedelta

subscription = UserSubscription(
    user_id=user_id,
    plan_id=plan_id,
    status='active',
    start_date=datetime.utcnow().date(),
    end_date=datetime.utcnow().date() + timedelta(days=30),
    auto_renew=True
)
db.session.add(subscription)
db.session.commit()
```

---

## 🔐 Access Control

### Middleware Usage
```python
# Check onboarding
@app.before_request
def check_onboarding():
    if current_user.is_authenticated and not current_user.onboarding_completed:
        return redirect(url_for('onboarding.onboarding_unified'))

# Check membership
@app.before_request
def check_membership():
    if request.endpoint == 'coach.apply_job':
        subscription = UserSubscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        if not subscription:
            return redirect(url_for('membership.plans'))

# Check admin access
@app.before_request
def check_admin_access():
    if 'admin' in request.endpoint:
        admin = Admin.query.filter_by(user_id=current_user.id).first()
        if not admin or not admin.is_active:
            return redirect(url_for('public.home'))
```

---

## 📈 Metrics & Reporting

### Admin Performance Metrics
- Total verifications
- Approval rate
- Average verification time
- User satisfaction score
- Appeals handled
- Activity frequency

### Subscription Metrics
- Active subscriptions
- Churn rate
- Revenue
- Upgrade rate
- Renewal rate

### Onboarding Metrics
- Completion rate
- Average time to complete
- Drop-off points
- Coins distributed
- Badges awarded

---

## 🔄 Workflows

### Admin Verification Workflow
```
Coach Uploads Document
    ↓
Document in Pending Queue
    ↓
Regional Admin Reviews
    ↓
Admin Approves/Rejects
    ↓
Coach Notified
    ↓
Badge Awarded (if approved)
    ↓
Activity Logged
```

### Subscription Workflow
```
User Selects Plan
    ↓
Payment Processing
    ↓
Payment Verified
    ↓
Subscription Created
    ↓
Features Unlocked
    ↓
Auto-renewal Scheduled
    ↓
Renewal Reminder (7 days before)
    ↓
Auto-renewal or Downgrade
```

### Onboarding Workflow
```
User Completes Step 1
    ↓
Coins Awarded (50)
    ↓
User Completes Step 2
    ↓
Coins Awarded (100)
    ↓
User Completes Step 3
    ↓
Coins Awarded (50)
    ↓
Orange Badge Awarded
    ↓
Onboarding Marked Complete
    ↓
Access to Features Unlocked
```

---

## 🛠️ Configuration

### Environment Variables
```env
# Admin
SUPER_ADMIN_EMAIL=admin@koachsmart.com
SUPER_ADMIN_PASSWORD=secure_password

# Membership
PAYMENT_GATEWAY=razorpay
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
```

### Default Plans
```python
COACH_PLANS = {
    'free': {'price': 0, 'apps_per_month': 3},
    'premium': {'price': 299, 'apps_per_month': 999999},
    'pro': {'price': 599, 'apps_per_month': 999999}
}

EMPLOYER_PLANS = {
    'free': {'price': 0, 'jobs_per_month': 1},
    'premium': {'price': 999, 'jobs_per_month': 999999},
    'enterprise': {'price': 0, 'jobs_per_month': 999999}  # Custom
}
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue**: Admin can't access city
```python
# Solution: Check assigned_cities
admin = Admin.query.get(admin_id)
print(admin.assigned_cities)
admin.add_city('Mumbai')
db.session.commit()
```

**Issue**: User can't apply for job
```python
# Solution: Check onboarding and membership
user = User.query.get(user_id)
print(f"Onboarding: {user.onboarding_completed}")
subscription = UserSubscription.query.filter_by(user_id=user_id, status='active').first()
print(f"Subscription: {subscription}")
```

**Issue**: Subscription not renewing
```python
# Solution: Check auto_renew flag
subscription = UserSubscription.query.get(sub_id)
print(f"Auto-renew: {subscription.auto_renew}")
subscription.auto_renew = True
db.session.commit()
```

---

## 📚 Documentation Links

- [System Architecture Plan](SYSTEM_ARCHITECTURE_PLAN.md)
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md)
- [Admin Verification Guide](ADMIN_VERIFICATION_GUIDE.md)
- [API Documentation](API_DOCUMENTATION.md) (to be created)

---

## 🎓 Learning Resources

### For Developers
- Admin role hierarchy implementation
- Middleware for access control
- Payment gateway integration
- Database migrations
- Activity logging

### For Admins
- Creating and managing regional admins
- Verifying coaches
- Viewing analytics
- Generating reports
- Handling appeals

### For Users
- Completing onboarding
- Purchasing membership
- Applying for jobs
- Tracking applications
- Managing profile

---

## 📞 Contact & Support

For questions or issues:
1. Check this guide first
2. Review the implementation roadmap
3. Check the system architecture plan
4. Contact development team

---

**Last Updated**: January 29, 2026
**Version**: 1.0
**Status**: Ready for Implementation