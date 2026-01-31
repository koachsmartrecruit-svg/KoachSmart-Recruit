from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets
import string

# Google OAuth imports
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

from core.extensions import db
from models.user import User
from models.profile import Profile
from services.stats_service import get_coach_stats

# ---------------------------
# Blueprint
# ---------------------------
auth_bp = Blueprint("auth", __name__)

# ---------------------------
# Register
# ---------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing = User.query.filter_by(
            email=request.form.get("email")
        ).first()

        if existing:
            flash("Email already exists")
            return redirect(url_for("auth.register"))

        # Get referral code from form if provided
        referral_code_input = request.form.get("referral_code", "").strip()
        
        user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            role="coach",
            password=generate_password_hash(
                request.form.get("password")
            )
        )

        db.session.add(user)
        db.session.commit()

        # Generate referral code for the new user
        if not user.referral_code:
            # Simple referral code generation
            import secrets
            user.referral_code = secrets.token_hex(4).upper()
            db.session.commit()
        
        # Apply referral if code was provided
        if referral_code_input:
            referring_user = User.query.filter_by(referral_code=referral_code_input).first()
            if referring_user and referring_user.id != user.id:
                user.referred_by = referring_user.referral_code  # Use referral code, not ID
                db.session.commit()
                flash(f"🎉 Referral applied! Your referrer will earn rewards when you complete onboarding.", "success")
            else:
                flash("Invalid referral code, but your account was created successfully.", "warning")

        profile = Profile(
            user_id=user.id,
            full_name=user.username
        )
        db.session.add(profile)
        db.session.commit()

        login_user(user)

        return redirect(url_for("payment.show_plans"))

    # Get real-time stats for the register page
    stats = get_coach_stats()
    return render_template("register.html", stats=stats)


# ---------------------------
# Login
# ---------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            email=request.form.get("email")
        ).first()

        if user and user.password and check_password_hash(
            user.password,
            request.form.get("password")
        ):
            login_user(user)
            
            # Redirect based on user role
            if user.role == "admin":
                # All admins go to the new admin management dashboard
                return redirect(url_for("admin_mgmt.dashboard"))
            elif user.role == "employer":
                return redirect(url_for("employer.dashboard"))
            else:  # coach or default
                return redirect(url_for("coach.dashboard"))

        flash("Invalid credentials")

    # Get real-time stats for the login page
    stats = get_coach_stats()
    return render_template("login.html", stats=stats)


# ---------------------------
# Logout
# ---------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("public.home"))


# ---------------------------
# Google OAuth Configuration
# ---------------------------
def get_google_oauth_flow():
    """Create Google OAuth flow"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:5000")
    
    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials not configured")
    
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"{base_url}/authorize/google"]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/userinfo.email", 
                "https://www.googleapis.com/auth/userinfo.profile", 
                "openid"],
        redirect_uri=f"{base_url}/authorize/google"
    )
    
    # Allow HTTP for development (disable HTTPS requirement)
    if os.getenv("FLASK_ENV") == "development" or "127.0.0.1" in base_url or "localhost" in base_url:
        import os as os_module
        os_module.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    
    return flow


def is_google_oauth_configured():
    """Check if Google OAuth is properly configured"""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    
    # Check if credentials are set
    return bool(client_id and client_secret)


def process_google_user(google_id, email, name, picture):
    """Process Google user login/registration"""
    if not email:
        flash("Could not get email from Google. Please try again.", "error")
        return redirect(url_for("auth.login"))
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    
    if user:
        # Update Google ID if not set
        if not user.google_id:
            user.google_id = google_id
            db.session.commit()
        
        login_user(user)
        flash(f"Welcome back, {user.username}!", "success")
        
        # Redirect based on role
        if user.role == "admin":
            return redirect(url_for("admin_mgmt.dashboard"))
        elif user.role == "employer":
            return redirect(url_for("employer.dashboard"))
        else:
            return redirect(url_for("coach.dashboard"))
    
    else:
        # Create new user
        username = email.split('@')[0]  # Use email prefix as username
        
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User(
            username=username,
            email=email,
            role="coach",  # Default role
            google_id=google_id,
            profile_pic=picture
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate referral code for the new user
        if not user.referral_code:
            import secrets
            user.referral_code = secrets.token_hex(4).upper()
            db.session.commit()
        
        # Create profile
        profile = Profile(
            user_id=user.id,
            full_name=name or username
        )
        db.session.add(profile)
        db.session.commit()
        
        login_user(user)
        flash(f"Welcome to KoachSmart, {user.username}! Your account has been created.", "success")
        
        # Redirect to role selection or onboarding
        return redirect(url_for("auth.select_role"))


# ---------------------------
# Google Auth
# ---------------------------
@auth_bp.route("/login/google")
def login_google():
    """Initiate Google OAuth login"""
    try:
        # Check if Google OAuth is configured
        if not is_google_oauth_configured():
            flash("Google login is not configured. Please use email/password login.", "warning")
            return redirect(url_for("auth.login"))
        
        flow = get_google_oauth_flow()
        
        # Generate state for security
        state = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        session['oauth_state'] = state
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        
        current_app.logger.info(f"Redirecting to Google OAuth: {authorization_url}")
        return redirect(authorization_url)
        
    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {e}")
        flash("Google login is temporarily unavailable. Please use email/password login.", "error")
        return redirect(url_for("auth.login"))


@auth_bp.route("/authorize/google")
def authorize_google():
    """Handle Google OAuth callback"""
    try:
        # Verify state parameter
        if request.args.get('state') != session.get('oauth_state'):
            flash("Invalid OAuth state. Please try again.", "error")
            return redirect(url_for("auth.login"))
        
        # Check for error in callback
        if request.args.get('error'):
            error = request.args.get('error')
            if error == 'access_denied':
                flash("Google login was cancelled.", "info")
            else:
                flash("Google login failed. Please try again.", "error")
            return redirect(url_for("auth.login"))
        
        # Check if Google OAuth is configured
        if not is_google_oauth_configured():
            flash("Google login is not configured.", "error")
            return redirect(url_for("auth.login"))
        
        flow = get_google_oauth_flow()
        
        # Handle the authorization response
        try:
            flow.fetch_token(authorization_response=request.url)
        except Exception as token_error:
            current_app.logger.error(f"Token fetch error: {token_error}")
            flash("Failed to authenticate with Google. Please try again.", "error")
            return redirect(url_for("auth.login"))
        
        # Get user info from Google
        credentials = flow.credentials
        request_session = google_requests.Request()
        
        # Verify the token
        try:
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                request_session,
                os.getenv("GOOGLE_CLIENT_ID")
            )
        except Exception as verify_error:
            current_app.logger.error(f"Token verification error: {verify_error}")
            flash("Failed to verify Google authentication. Please try again.", "error")
            return redirect(url_for("auth.login"))
        
        # Extract user information
        google_id = id_info.get('sub')
        email = id_info.get('email')
        name = id_info.get('name')
        picture = id_info.get('picture')
        
        if not email:
            flash("Could not get email from Google. Please try again.", "error")
            return redirect(url_for("auth.login"))
        
        return process_google_user(google_id, email, name, picture)
    
    except Exception as e:
        current_app.logger.error(f"Google OAuth callback error: {e}")
        flash("Google login failed. Please try again or use email/password login.", "error")
        return redirect(url_for("auth.login"))
    
    finally:
        # Clean up session
        session.pop('oauth_state', None)


# ---------------------------
# Password Reset
# ---------------------------
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("Password reset link sent (mock)")
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html")

@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password_mock():
    return render_template("reset_password.html")


# ---------------------------
# Role Selection
# ---------------------------
@auth_bp.route("/select-role", methods=["GET", "POST"])
@login_required
def select_role():
    if request.method == "POST":
        role = request.form.get("role")
        current_user.role = role
        db.session.commit()
        
        # Redirect based on selected role
        if role == "admin":
            return redirect(url_for("admin_mgmt.dashboard"))
        elif role == "employer":
            return redirect(url_for("employer.dashboard"))
        else:
            return redirect(url_for("coach.dashboard"))
    
    return render_template("select_role.html")