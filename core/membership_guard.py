"""
Membership Guard Middleware
Enforces membership requirements for job applications and postings
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request, current_app
from flask_login import current_user
from models.user import User
from models.membership import UserSubscription, MembershipPlan
from datetime import datetime


def require_membership(required_feature=None, user_type=None):
    """
    Decorator to require active membership for specific features
    
    Args:
        required_feature: Feature that requires membership (e.g., 'job_applications', 'job_posting')
        user_type: Type of user ('coach', 'employer')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in (Flask-Login)
            if not current_user.is_authenticated:
                flash('Please log in to access this feature.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Check membership status
            membership_status = check_membership_access(current_user, required_feature, user_type)
            
            if not membership_status['has_access']:
                flash(membership_status['message'], 'warning')
                return redirect(url_for('membership.plans'))
            
            # Check usage limits if applicable
            if required_feature and not check_usage_limits(current_user, required_feature):
                flash('You have reached your monthly limit for this feature. Please upgrade your membership.', 'warning')
                return redirect(url_for('membership.plans'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_membership_access(user, required_feature=None, user_type=None):
    """
    Check if user has membership access for a specific feature
    
    Args:
        user: User object
        required_feature: Feature to check access for
        user_type: Type of user ('coach', 'employer')
    
    Returns:
        dict: {'has_access': bool, 'message': str, 'plan': MembershipPlan}
    """
    try:
        # Get user's current subscription
        subscription = UserSubscription.query.filter_by(user_id=user.id).first()
        
        # If no subscription, user is on free plan
        if not subscription:
            # Create default free subscription
            free_plan = get_or_create_free_plan(user_type or user.role)
            if free_plan:
                subscription = create_free_subscription(user.id, free_plan.id)
            else:
                return {
                    'has_access': False,
                    'message': 'Unable to determine membership status. Please contact support.',
                    'plan': None
                }
        
        # Check if subscription is active
        if not subscription.is_active():
            return {
                'has_access': False,
                'message': 'Your membership has expired. Please renew to continue using this feature.',
                'plan': subscription.plan
            }
        
        # Check feature access
        if required_feature:
            feature_access = check_feature_access(subscription.plan, required_feature)
            if not feature_access['has_access']:
                return {
                    'has_access': False,
                    'message': feature_access['message'],
                    'plan': subscription.plan
                }
        
        return {
            'has_access': True,
            'message': 'Access granted',
            'plan': subscription.plan
        }
        
    except Exception as e:
        current_app.logger.error(f"Error checking membership access: {str(e)}")
        return {
            'has_access': False,
            'message': 'Error checking membership status. Please try again.',
            'plan': None
        }


def check_feature_access(plan, feature):
    """
    Check if a membership plan has access to a specific feature
    
    Args:
        plan: MembershipPlan object
        feature: Feature name to check
    
    Returns:
        dict: {'has_access': bool, 'message': str}
    """
    feature_map = {
        'job_applications': {
            'feature_key': 'browse_jobs',
            'message': 'You need an active membership to apply for jobs.'
        },
        'job_posting': {
            'feature_key': 'post_jobs',
            'message': 'You need an active membership to post jobs.'
        },
        'direct_messaging': {
            'feature_key': 'direct_messaging',
            'message': 'Direct messaging is available with Premium membership and above.'
        },
        'analytics': {
            'feature_key': 'analytics',
            'message': 'Analytics are available with Premium membership and above.'
        },
        'featured_profile': {
            'feature_key': 'featured_profile',
            'message': 'Featured profiles are available with Premium membership and above.'
        },
        'bulk_messaging': {
            'feature_key': 'bulk_messaging',
            'message': 'Bulk messaging is available with Premium membership and above.'
        }
    }
    
    if feature not in feature_map:
        return {'has_access': True, 'message': 'Feature access granted'}
    
    feature_config = feature_map[feature]
    feature_key = feature_config['feature_key']
    
    # Check if plan has the feature
    if plan.has_feature(feature_key):
        return {'has_access': True, 'message': 'Feature access granted'}
    
    return {
        'has_access': False,
        'message': feature_config['message']
    }


def check_usage_limits(user, feature):
    """
    Check if user has exceeded usage limits for a feature
    
    Args:
        user: User object
        feature: Feature to check limits for
    
    Returns:
        bool: True if within limits, False if exceeded
    """
    try:
        subscription = UserSubscription.query.filter_by(user_id=user.id).first()
        if not subscription or not subscription.is_active():
            return False
        
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if feature == 'job_applications':
            # Check monthly application limit
            if subscription.plan.monthly_applications == 999999:  # Unlimited
                return True
            
            # Count applications this month
            from models.application import Application
            monthly_applications = Application.query.filter(
                Application.user_id == user.id,
                Application.applied_date >= current_month
            ).count()
            
            return monthly_applications < subscription.plan.monthly_applications
        
        elif feature == 'job_posting':
            # Check monthly job posting limit
            if subscription.plan.monthly_job_posts == 999999:  # Unlimited
                return True
            
            # Count job posts this month
            from models.job import Job
            monthly_posts = Job.query.filter(
                Job.employer_id == user.id,
                Job.posted_date >= current_month
            ).count()
            
            return monthly_posts < subscription.plan.monthly_job_posts
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error checking usage limits: {str(e)}")
        return False


def get_or_create_free_plan(user_type):
    """
    Get or create the free membership plan for a user type
    
    Args:
        user_type: 'coach' or 'employer'
    
    Returns:
        MembershipPlan: Free plan for the user type
    """
    try:
        # Try to get existing free plan
        free_plan = MembershipPlan.query.filter_by(
            name='Free',
            user_type=user_type,
            is_active=True
        ).first()
        
        if free_plan:
            return free_plan
        
        # Create free plan if it doesn't exist
        default_plans = MembershipPlan.get_default_plans()
        if user_type in default_plans and 'free' in default_plans[user_type]:
            plan_data = default_plans[user_type]['free']
            
            free_plan = MembershipPlan(
                name=plan_data['name'],
                user_type=user_type,
                price=plan_data['price'],
                duration_days=plan_data['duration_days'],
                features=plan_data['features'],
                monthly_applications=plan_data.get('monthly_applications'),
                monthly_job_posts=plan_data.get('monthly_job_posts'),
                is_active=True,
                display_order=0
            )
            
            from core.extensions import db
            db.session.add(free_plan)
            db.session.commit()
            
            return free_plan
        
        return None
        
    except Exception as e:
        current_app.logger.error(f"Error getting/creating free plan: {str(e)}")
        return None


def create_free_subscription(user_id, plan_id):
    """
    Create a free subscription for a user
    
    Args:
        user_id: User ID
        plan_id: Plan ID
    
    Returns:
        UserSubscription: Created subscription
    """
    try:
        from datetime import date, timedelta
        from core.extensions import db
        
        # Create subscription with very long duration for free plan
        subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            status='active',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=999999),  # Effectively unlimited
            auto_renew=False,
            payment_method='free'
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return subscription
        
    except Exception as e:
        current_app.logger.error(f"Error creating free subscription: {str(e)}")
        return None


def get_user_membership_info(user):
    """
    Get comprehensive membership information for a user
    
    Args:
        user: User object
    
    Returns:
        dict: Membership information
    """
    try:
        subscription = UserSubscription.query.filter_by(user_id=user.id).first()
        
        if not subscription:
            # User has no subscription, return free plan info
            free_plan = get_or_create_free_plan(user.role)
            return {
                'has_subscription': False,
                'plan_name': 'Free',
                'plan_type': user.role,
                'is_active': True,
                'days_remaining': 999999,
                'features': free_plan.features if free_plan else {},
                'monthly_applications': 3 if user.role == 'coach' else None,
                'monthly_job_posts': 1 if user.role == 'employer' else None,
                'can_upgrade': True
            }
        
        return {
            'has_subscription': True,
            'plan_name': subscription.plan.name,
            'plan_type': subscription.plan.user_type,
            'is_active': subscription.is_active(),
            'days_remaining': subscription.days_remaining(),
            'features': subscription.plan.features,
            'monthly_applications': subscription.plan.monthly_applications,
            'monthly_job_posts': subscription.plan.monthly_job_posts,
            'can_upgrade': subscription.plan.name != 'Pro' and subscription.plan.name != 'Enterprise',
            'auto_renew': subscription.auto_renew,
            'end_date': subscription.end_date
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting membership info: {str(e)}")
        return {
            'has_subscription': False,
            'plan_name': 'Unknown',
            'plan_type': user.role,
            'is_active': False,
            'days_remaining': 0,
            'features': {},
            'can_upgrade': True
        }


# Convenience decorators for common use cases
def require_coach_membership(f):
    """Require active coach membership"""
    return require_membership('job_applications', 'coach')(f)


def require_employer_membership(f):
    """Require active employer membership"""
    return require_membership('job_posting', 'employer')(f)


def require_premium_feature(feature_name):
    """Require premium membership for specific feature"""
    def decorator(f):
        return require_membership(feature_name)(f)
    return decorator