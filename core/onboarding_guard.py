"""
Onboarding Guard Middleware
Enforces mandatory 3-step onboarding for coaches before accessing profile/jobs
"""

from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user

def onboarding_guard():
    # ✅ Skip API routes completely
    if request.path.startswith("/api/"):
        return None


def require_onboarding_completion(f):
    """
    Decorator to check if coach has completed onboarding
    
    Usage:
        @require_onboarding_completion
        def coach_dashboard():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only apply to coaches
        if not current_user.is_authenticated or current_user.role != "coach":
            return f(*args, **kwargs)
        
        # Check if onboarding is completed
        if not current_user.onboarding_completed:
            flash("Please complete your 3-step onboarding process to access this feature.", "warning")
            return redirect(url_for("onboarding.onboarding_unified"))
        
        return f(*args, **kwargs)
    
    return decorated_function


def check_onboarding_completion():
    """
    Check if current coach user has completed onboarding
    Returns True if completed or not a coach, False if incomplete
    """
    if not current_user.is_authenticated:
        return True
    
    if current_user.role != "coach":
        return True
    
    return current_user.onboarding_completed


def get_onboarding_progress():
    """
    Get current onboarding progress for coach
    Returns dict with progress information
    """
    if not current_user.is_authenticated or current_user.role != "coach":
        return None
    
    current_step = current_user.onboarding_step or 1
    total_steps = 3  # Updated to 3 steps as per requirements
    
    progress = {
        'current_step': current_step,
        'total_steps': total_steps,
        'completed': current_user.onboarding_completed,
        'progress_percentage': min((current_step - 1) / total_steps * 100, 100),
        'steps_completed': current_step - 1 if not current_user.onboarding_completed else total_steps
    }
    
    return progress


def get_onboarding_rewards():
    """
    Get rewards information for onboarding completion
    """
    return {
        'coins': 200,
        'badge': 'Orange Badge',
        'badge_color': '#FF8C00',
        'description': 'Complete your 3-step onboarding to unlock job applications and earn rewards!'
    }


# Routes that require onboarding completion
PROTECTED_ROUTES = [
    'coach.dashboard',
    'coach.coach_jobs',
    'coach.apply_job',
    'coach.view_applications',
    'coach.edit_profile',
    'coach.view_resume',
    'coach.update_profile',
    'verification.verification_dashboard',
    'verification.stage1',
    'verification.stage2',
    'verification.stage3',
    'verification.stage4'
]


def is_protected_route(endpoint):
    """
    Check if the current route requires onboarding completion
    """
    return endpoint in PROTECTED_ROUTES


def onboarding_guard():
    """
    Global before_request function to check onboarding completion
    """
    # Skip for non-authenticated users
    if not current_user.is_authenticated:
        return
    
    # Skip for non-coaches
    if current_user.role != "coach":
        return
    
    # Skip for onboarding routes themselves
    if request.endpoint and request.endpoint.startswith('onboarding.'):
        return
    
    # Skip for auth routes
    if request.endpoint and request.endpoint.startswith('auth.'):
        return
    
    # Skip for public routes
    if request.endpoint and request.endpoint.startswith('public.'):
        return
    
    # Check if current route is protected
    if request.endpoint and is_protected_route(request.endpoint):
        if not current_user.onboarding_completed:
            flash("Complete your 3-step onboarding to access this feature and earn 200 coins + Orange Badge!", "info")
            return redirect(url_for("onboarding.onboarding_unified"))
    
    return None