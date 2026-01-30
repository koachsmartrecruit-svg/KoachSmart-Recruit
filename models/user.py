from flask_login import UserMixin
from datetime import datetime
from core.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    # Identity
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(50), default="coach")
    google_id = db.Column(db.String(255), unique=True)
    profile_pic = db.Column(db.Text)

    # Subscription
    subscription_status = db.Column(db.String(50), default="free")
    stripe_customer_id = db.Column(db.String(255))

    # Gamification
    points = db.Column(db.Integer, default=0)
    coins = db.Column(db.Integer, default=0)

    # Verification badges
    phone_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    aadhar_verified = db.Column(db.Boolean, default=False)
    location_verified = db.Column(db.Boolean, default=False)
    education_verified = db.Column(db.Boolean, default=False)
    professional_verified = db.Column(db.Boolean, default=False)
    
    # Badge system
    badges = db.Column(db.Text, default="")  # Comma-separated badge names

    # Coach onboarding
    onboarding_step = db.Column(db.Integer, default=1)
    onboarding_completed = db.Column(db.Boolean, default=False)
    onboarding_completed_at = db.Column(db.DateTime, nullable=True)

    # Employer onboarding
    employer_onboarding_step = db.Column(db.Integer, default=1)
    employer_onboarding_completed = db.Column(db.Boolean, default=False)
    
    # Membership
    membership_status = db.Column(db.String(50), default='free')
    membership_expires_at = db.Column(db.DateTime, nullable=True)

    # Enhanced onboarding fields
    preferred_language = db.Column(db.String(50), default='english')
    digital_id = db.Column(db.String(100), unique=True)
    
    # Enhanced referral system
    referral_code = db.Column(db.String(20), unique=True)
    referred_by = db.Column(db.String(20))
    referred_by_code = db.Column(db.String(20))  # Enhanced referral tracking
    referral_bonus_claimed = db.Column(db.Boolean, default=False)
    
    # Premium features
    premium_subscription = db.Column(db.Boolean, default=False)
    premium_expires_at = db.Column(db.DateTime)
    cv_builder_access = db.Column(db.Boolean, default=False)

    # Relationships
    profile = db.relationship(
        "Profile", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    jobs = db.relationship("Job", backref="employer", lazy=True)
    applications = db.relationship("Application", backref="applicant", lazy=True)
    reward_logs = db.relationship("RewardLedger", backref="user", lazy=True)
