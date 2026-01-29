"""
Membership and Subscription Models
Handles membership plans, subscriptions, and billing
"""

from core.extensions import db
from datetime import datetime, timedelta


class MembershipPlan(db.Model):
    """Membership plan definitions"""
    __tablename__ = "membership_plan"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 'Free', 'Premium', 'Pro'
    user_type = db.Column(db.String(50), nullable=False)  # 'coach', 'employer'
    
    # Pricing
    price = db.Column(db.Numeric(10, 2), default=0)
    currency = db.Column(db.String(10), default='INR')
    
    # Duration
    duration_days = db.Column(db.Integer, default=30)
    
    # Features (JSON)
    features = db.Column(db.JSON, default={})
    
    # Limits
    monthly_applications = db.Column(db.Integer, nullable=True)  # For coaches
    monthly_job_posts = db.Column(db.Integer, nullable=True)  # For employers
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship("UserSubscription", backref="plan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MembershipPlan {self.name} for {self.user_type}>"
    
    def has_feature(self, feature_name):
        """Check if plan has specific feature"""
        return self.features.get(feature_name, False)
    
    @staticmethod
    def get_default_plans():
        """Get default membership plans"""
        return {
            'coach': {
                'free': {
                    'name': 'Free',
                    'price': 0,
                    'duration_days': 999999,  # Unlimited
                    'features': {
                        'browse_jobs': True,
                        'applications_per_month': 3,
                        'featured_profile': False,
                        'direct_messaging': False,
                        'analytics': False,
                        'coaching_tools': False,
                        'revenue_sharing': False,
                        'priority_support': False
                    },
                    'monthly_applications': 3
                },
                'premium': {
                    'name': 'Premium',
                    'price': 299,
                    'duration_days': 30,
                    'features': {
                        'browse_jobs': True,
                        'applications_per_month': 999999,  # Unlimited
                        'featured_profile': True,
                        'direct_messaging': True,
                        'analytics': True,
                        'coaching_tools': False,
                        'revenue_sharing': False,
                        'priority_support': False
                    },
                    'monthly_applications': 999999
                },
                'pro': {
                    'name': 'Pro',
                    'price': 599,
                    'duration_days': 30,
                    'features': {
                        'browse_jobs': True,
                        'applications_per_month': 999999,
                        'featured_profile': True,
                        'direct_messaging': True,
                        'analytics': True,
                        'coaching_tools': True,
                        'revenue_sharing': True,
                        'priority_support': True
                    },
                    'monthly_applications': 999999
                }
            },
            'employer': {
                'free': {
                    'name': 'Free',
                    'price': 0,
                    'duration_days': 999999,
                    'features': {
                        'browse_coaches': True,
                        'post_jobs': True,
                        'job_posts_per_month': 1,
                        'featured_jobs': False,
                        'bulk_messaging': False,
                        'analytics': False,
                        'api_access': False,
                        'dedicated_manager': False
                    },
                    'monthly_job_posts': 1
                },
                'premium': {
                    'name': 'Premium',
                    'price': 999,
                    'duration_days': 30,
                    'features': {
                        'browse_coaches': True,
                        'post_jobs': True,
                        'job_posts_per_month': 999999,
                        'featured_jobs': True,
                        'bulk_messaging': True,
                        'analytics': True,
                        'api_access': False,
                        'dedicated_manager': False
                    },
                    'monthly_job_posts': 999999
                },
                'enterprise': {
                    'name': 'Enterprise',
                    'price': 0,  # Custom pricing
                    'duration_days': 30,
                    'features': {
                        'browse_coaches': True,
                        'post_jobs': True,
                        'job_posts_per_month': 999999,
                        'featured_jobs': True,
                        'bulk_messaging': True,
                        'analytics': True,
                        'api_access': True,
                        'dedicated_manager': True
                    },
                    'monthly_job_posts': 999999
                }
            }
        }


class UserSubscription(db.Model):
    """User subscription to membership plans"""
    __tablename__ = "user_subscription"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("membership_plan.id"), nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='active')  # 'active', 'expired', 'cancelled', 'suspended'
    
    # Dates
    start_date = db.Column(db.Date, default=datetime.utcnow)
    end_date = db.Column(db.Date, nullable=False)
    
    # Renewal
    auto_renew = db.Column(db.Boolean, default=True)
    
    # Payment
    payment_method = db.Column(db.String(50))  # 'card', 'upi', 'wallet'
    payment_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="subscription")
    
    def __repr__(self):
        return f"<UserSubscription {self.user_id} - {self.plan.name}>"
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and self.end_date >= datetime.utcnow().date()
    
    def is_expired(self):
        """Check if subscription has expired"""
        return self.end_date < datetime.utcnow().date()
    
    def days_remaining(self):
        """Get days remaining in subscription"""
        if self.is_expired():
            return 0
        return (self.end_date - datetime.utcnow().date()).days
    
    def renew(self):
        """Renew subscription for another period"""
        self.start_date = datetime.utcnow().date()
        self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        self.status = 'active'
        db.session.commit()
    
    def cancel(self):
        """Cancel subscription"""
        self.status = 'cancelled'
        db.session.commit()
    
    def suspend(self):
        """Suspend subscription (e.g., for payment issues)"""
        self.status = 'suspended'
        db.session.commit()


class SubscriptionHistory(db.Model):
    """History of subscription changes and payments"""
    __tablename__ = "subscription_history"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("membership_plan.id"), nullable=False)
    
    # Action
    action = db.Column(db.String(50), nullable=False)  # 'purchase', 'renew', 'upgrade', 'downgrade', 'cancel'
    
    # Payment
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='INR')
    status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'failed', 'refunded'
    
    # Transaction
    transaction_id = db.Column(db.String(100), unique=True, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    
    # Metadata
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="subscription_history")
    plan = db.relationship("MembershipPlan")
    
    def __repr__(self):
        return f"<SubscriptionHistory {self.action} for User {self.user_id}>"


class OnboardingProgress(db.Model):
    """Track user onboarding progress"""
    __tablename__ = "onboarding_progress"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    
    # Progress
    current_step = db.Column(db.Integer, default=1)
    completed_steps = db.Column(db.JSON, default=[])  # [1, 2, 3]
    
    # Rewards
    coins_earned = db.Column(db.Integer, default=0)
    badges_earned = db.Column(db.JSON, default=[])  # ['orange']
    
    # Completion
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="onboarding_progress")
    
    def __repr__(self):
        return f"<OnboardingProgress User {self.user_id} - Step {self.current_step}>"
    
    def mark_step_complete(self, step, coins=0, badge=None):
        """Mark a step as complete"""
        if step not in self.completed_steps:
            self.completed_steps.append(step)
        
        self.coins_earned += coins
        if badge and badge not in self.badges_earned:
            self.badges_earned.append(badge)
        
        # Update user coins
        self.user.coins += coins
        
        db.session.commit()
    
    def complete_onboarding(self):
        """Mark onboarding as complete"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        self.user.onboarding_completed = True
        self.user.onboarding_completed_at = datetime.utcnow()
        db.session.commit()
    
    def get_progress_percentage(self):
        """Get onboarding progress percentage"""
        total_steps = 3  # Personal, Professional, Location
        completed = len(self.completed_steps)
        return (completed / total_steps) * 100
