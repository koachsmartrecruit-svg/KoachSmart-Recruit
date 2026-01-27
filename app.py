import os
import math
import time
import json
import random
import re
import stripe
import smtplib
import secrets
from pathlib import Path
from datetime import datetime
from enum import Enum

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, jsonify, current_app, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
from flask_socketio import SocketIO, emit, join_room, leave_room

import PyPDF2
import docx


# Email helpers
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Google Sheets
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def validate_phone(phone):
    return bool(re.fullmatch(r"[6-9]\d{9}", phone or ""))

def validate_pincode(pin):
    return bool(re.fullmatch(r"\d{6}", pin or ""))

def validate_ifsc(ifsc):
    return bool(re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", ifsc or ""))

def validate_pan(pan):
    return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", pan or ""))

def allowed_file(filename):
    allowed = {"pdf", "jpg", "jpeg", "png"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed
# -----------------------------------------------------------------------------
# Load environment
# -----------------------------------------------------------------------------
load_dotenv()

# -----------------------------------------------------------------------------
# Google Sheets config
# -----------------------------------------------------------------------------
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')

# -----------------------------------------------------------------------------
# Flask app + core extensions must be created BEFORE models
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300
}

# Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
app.config['STRIPE_PUBLISHABLE_KEY'] = os.getenv('STRIPE_PUBLISHABLE_KEY')
app.config['STRIPE_PRICE_BASIC'] = os.getenv('STRIPE_PRICE_BASIC')
app.config['STRIPE_PRICE_PRO'] = os.getenv('STRIPE_PRICE_PRO')
app.config['STRIPE_WEBHOOK_SECRET'] = os.getenv('STRIPE_WEBHOOK_SECRET')

# Upload folders
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['CERT_FOLDER'] = 'static/certs'
app.config['RESUME_FOLDER'] = 'static/resumes'
app.config['PROFILE_PIC_FOLDER'] = 'static/profile_pics'
app.config['EXP_PROOF_FOLDER'] = 'static/experience_proofs'
app.config['ID_PROOF_FOLDER'] = 'static/id_proofs'
app.config['TEMP_FOLDER'] = 'static/temp_docs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

for folder in [
    app.config['UPLOAD_FOLDER'],
    app.config['CERT_FOLDER'], app.config['RESUME_FOLDER'],
    app.config['PROFILE_PIC_FOLDER'], app.config['EXP_PROOF_FOLDER'],
    app.config['ID_PROOF_FOLDER'], app.config['TEMP_FOLDER']
]:
    os.makedirs(folder, exist_ok=True)

# Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

# Google OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['GOOGLE_DISCOVERY_URL'] = "https://accounts.google.com/.well-known/openid-configuration"

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
    client_kwargs={'scope': 'openid email profile'},
)
# 2) Add a before_request guard that only enforces onboarding for employers on protected pages
@app.before_request
def enforce_employer_onboarding():
    # Only enforce for logged-in employers
    if not current_user.is_authenticated or current_user.role != 'employer':
        return

    # Allow static assets
    if request.path.startswith('/static'):
        return

    # Public/auth/onboarding pages that should always be accessible
    always_allow_endpoints = {
        # Auth + account
        'login', 'register', 'logout', 'forgot_password', 'reset_password_mock',
        'login_google', 'authorize_google', 'select_role',
        
        # Public pages
        'home', 'about', 'careers', 'success_stories', 'pricing',
        'coach_guide', 'academy_guide', 'safety', 'help_center',
        'about_page', 'error_demo', 'payment_pending',
        
        # Onboarding and plans
        'hirer_onboarding',  # onboarding page itself
        'show_plans',  # plans page (accessible before onboarding)
    }

    # If the requested endpoint is public, allow it
    if request.endpoint in always_allow_endpoints:
        return

    # If onboarding is NOT completed, block all endpoints except allowed ones
    if not current_user.employer_onboarding_completed:
        # If endpoint is not in always_allow list, redirect to onboarding
        if request.endpoint not in always_allow_endpoints:
            return redirect(url_for('hirer_onboarding'))
# DB and login manager BEFORE models
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# -----------------------------------------------------------------------------
# Onboarding enforcement (only for protected app pages)
# -----------------------------------------------------------------------------
@app.before_request
def enforce_onboarding():
    # Only enforce for logged-in coaches
    if not current_user.is_authenticated or current_user.role != 'coach':
        return

    # Pages that should ALWAYS be accessible (public/auth flows)
    always_allow_endpoints = {
        # Auth + account
        'login', 'register', 'logout', 'forgot_password', 'reset_password_mock',
        'login_google', 'authorize_google', 'select_role',

        # Public pages
        'home', 'about', 'careers', 'success_stories', 'pricing',
        'coach_guide', 'academy_guide', 'safety', 'help_center',
        'about_page', 'error_demo', 'payment_pending',

        # Onboarding page itself
        'onboarding_unified',
    }

    # Allow static assets by path
    if request.path.startswith('/static'):
        return

    # If the requested endpoint is public, allow it
    if request.endpoint in always_allow_endpoints:
        return

    # Protected app pages (connected to dashboard/using app features)
    protected_coach_endpoints = {
        'dashboard', 'coach_jobs', 'explore_coaches',
        'apply_job', 'update_status',
        'resume_builder', 'edit_profile', 'delete_profile',
        'new_job', 'job_new', 'job_edit', 'toggle_job_status',
        'submit_review', 'chathome', 'chat',
    }

    # If onboarding is NOT completed and user hits a protected page → redirect
    if (request.endpoint in protected_coach_endpoints) and (not current_user.onboarding_completed):
        return redirect(url_for('onboarding_unified'))
# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------
class ReviewStatus(str, Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"
    not_required = "Not Required"

class HiringMode(str, Enum):
    single = "Single"
    multiple = "Multiple"

# -----------------------------------------------------------------------------
# MODELS (now safely defined because db exists)
# -----------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(50), default='coach')
    google_id = db.Column(db.String(255), unique=True)
    profile_pic = db.Column(db.Text)
    subscription_status = db.Column(db.String(50), default='free')
    stripe_customer_id = db.Column(db.String(255))

    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    jobs = db.relationship('Job', backref='employer', lazy=True)
    applications = db.relationship('Application', backref='applicant', lazy=True)
    reviews_given = db.relationship('Review', backref='reviewer', lazy=True)

    points = db.Column(db.Integer, default=0)
    coins = db.Column(db.Integer, default=0)
    phone_verified = db.Column(db.Boolean, default=False)
    location_verified = db.Column(db.Boolean, default=False)
    education_verified = db.Column(db.Boolean, default=False)
    professional_verified = db.Column(db.Boolean, default=False)

    onboarding_step = db.Column(db.Integer, default=1)
    onboarding_completed = db.Column(db.Boolean, default=False)
    # Hirer (employer) onboarding
    employer_onboarding_step = db.Column(db.Integer, default=1)
    employer_onboarding_completed = db.Column(db.Boolean, default=False)
    # Referral
    referral_code = db.Column(db.String(20), unique=True)
    referred_by = db.Column(db.String(20))
    referral_bonus_claimed = db.Column(db.Boolean, default=False)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    sport = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    certifications = db.Column(db.String(500))
    bio = db.Column(db.Text)
    city = db.Column(db.String(100))
    travel_range = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)

    cert_proof_path = db.Column(db.String(300))
    resume_path = db.Column(db.String(300))
    experience_proof_path = db.Column(db.String(300))
    id_proof_path = db.Column(db.String(300))
    reviews = db.relationship('Review', backref='profile', lazy=True)

    sport_primary = db.Column(db.String(100))
    working_type = db.Column(db.String(50))
    range_km = db.Column(db.Integer)
    notify_outside_range = db.Column(db.Boolean, default=False)
    languages = db.Column(db.Text)  # JSON string

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    sport = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    venue = db.Column(db.String(150))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))

    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)

    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    screening_questions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    salary_range = db.Column(db.String(100))
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    required_skills = db.Column(db.String(300))
    job_type = db.Column(db.String(50), default='Full Time')
    working_hours = db.Column(db.String(100))

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Applied')
    match_score = db.Column(db.Integer)
    match_reasons = db.Column(db.Text)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    custom_resume_path = db.Column(db.String(300))
    screening_answers = db.Column(db.Text)
    job = db.relationship('Job', backref='applications')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class RewardLedger(db.Model):
    __tablename__ = "reward_ledger"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    points_awarded = db.Column(db.Integer, default=0)
    coins_awarded = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='reward_logs')
    __table_args__ = (
        db.UniqueConstraint('user_id', 'action', name='unique_user_action_reward'),
    )

# Hirer + Review (ADMIN multi-level approvals)
class Hirer(db.Model):
    __tablename__ = 'hirer'
    id = db.Column(db.Integer, primary_key=True)
    institute_name = db.Column(db.String(150), nullable=False)
    address_full = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), default="India", nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    alternate_number = db.Column(db.String(15))
    email = db.Column(db.String(150), nullable=False)
    email_otp_status = db.Column(db.String(20), default="Pending")
    phone_otp_status = db.Column(db.String(20), default="Pending")
    google_maps_link = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    hiring_mode = db.Column(db.String(20), nullable=False)
    hiring_count = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
        # -------------------------------
    # Sheet → Basic / Business Details
    # -------------------------------
    contact_person_name = db.Column(db.String(150))     # Contact Person Name
    business_type = db.Column(db.String(100))           # Academy / School / Venue / Event
    gst_number = db.Column(db.String(50))                # GST Number
    years_active = db.Column(db.Integer)                # Years in operation

    # -------------------------------
    # Document uploads
    # -------------------------------
    gst_doc_path = db.Column(db.String(300))             # GST Certificate
    registration_doc_path = db.Column(db.String(300))   # Registration Certificate
    owner_id_doc_path = db.Column(db.String(300))        # Owner ID Proof

    # -------------------------------
    # Location extras
    # -------------------------------
    pincode = db.Column(db.String(10))                   # Postal Code

    # -------------------------------
    # Hiring Preferences
    # -------------------------------
    sports_categories = db.Column(db.Text)              # JSON / comma-separated
    working_type = db.Column(db.String(50))              # Full-time / Part-time / Contract
    budget_range = db.Column(db.String(100))             # Expected budget

    # -------------------------------
    # Risk / Compliance flags
    # -------------------------------
    duplicate_flag = db.Column(db.Boolean, default=False)
    risk_flag = db.Column(db.Boolean, default=False)
    payment_verified = db.Column(db.Boolean, default=False)


class HirerReview(db.Model):
    __tablename__ = 'hirer_review'
    id = db.Column(db.Integer, primary_key=True)
    hirer_id = db.Column(db.Integer, db.ForeignKey('hirer.id'), nullable=False)
    hirer = db.relationship('Hirer', backref=db.backref('review', uselist=False))

    l1_status = db.Column(db.String(20), default=ReviewStatus.pending.value)
    l1_reviewer_id = db.Column(db.Integer)
    l1_note = db.Column(db.Text)
    l1_at = db.Column(db.DateTime)

    l2_status = db.Column(db.String(20), default=ReviewStatus.pending.value)
    l2_reviewer_id = db.Column(db.Integer)
    l2_note = db.Column(db.Text)
    l2_at = db.Column(db.DateTime)

    compliance_status = db.Column(db.String(20), default=ReviewStatus.not_required.value)
    compliance_reviewer_id = db.Column(db.Integer)
    compliance_note = db.Column(db.Text)
    compliance_at = db.Column(db.DateTime)

    docs_address_proof = db.Column(db.Boolean, default=False)
    docs_registration = db.Column(db.Boolean, default=False)
    docs_website = db.Column(db.Boolean, default=False)
    docs_maps_link = db.Column(db.Boolean, default=False)

    final_status = db.Column(db.String(20), default=ReviewStatus.pending.value)
    ready_to_post = db.Column(db.Boolean, default=False)
    final_at = db.Column(db.DateTime)

# -----------------------------------------------------------------------------
# Helpers: rewards, onboarding, OTP, sheets
# -----------------------------------------------------------------------------
def has_reward_been_given(user_id, action):
    return RewardLedger.query.filter_by(user_id=user_id, action=action).first() is not None

def award_reward(user_id, action, points=0, coins=0):
    if points == 0 and coins == 0:
        return False, "No reward configured."
    try:
        if has_reward_been_given(user_id, action):
            return False, "Reward already granted."

        user = User.query.get(user_id)
        if not user:
            return False, "User not found."

        if points:
            user.points += int(points)
        if coins:
            user.coins += int(coins)

        ledger = RewardLedger(
            user_id=user_id,
            action=action,
            points_awarded=points,
            coins_awarded=coins
        )
        db.session.add(ledger)
        db.session.commit()
        return True, "Reward granted successfully."
    except IntegrityError:
        db.session.rollback()
        return False, "Duplicate reward prevented."
    except Exception as e:
        db.session.rollback()
        print("Reward error:", e)
        return False, "Reward failed due to system error."

def assign_badge(user_id, badge_field):
    allowed_badges = {"phone_verified", "location_verified", "education_verified", "professional_verified"}
    if badge_field not in allowed_badges:
        return False, "Invalid badge."
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        if getattr(user, badge_field):
            return False, "Badge already assigned."
        setattr(user, badge_field, True)
        db.session.commit()
        return True, "Badge assigned."
    except Exception as e:
        db.session.rollback()
        print("Badge error:", e)
        return False, "Badge assignment failed."

def generate_referral_code():
    return secrets.token_urlsafe(6).upper()[:8]

def process_referral_signup(new_user, referral_code):
    if not referral_code:
        return
    referrer = User.query.filter_by(referral_code=referral_code).first()
    if not referrer:
        return
    new_user.referred_by = referral_code

def award_referral_bonus(user_id):
    user = User.query.get(user_id)
    if not user or not user.referred_by or user.referral_bonus_claimed:
        return
    referrer = User.query.filter_by(referral_code=user.referred_by).first()
    if not referrer:
        return
    award_reward(user_id=referrer.id, action=f"referral_{user.id}", coins=200, points=50)
    award_reward(user_id=user.id, action="referred_signup_bonus", coins=50, points=10)
    user.referral_bonus_claimed = True
    db.session.commit()
    flash(f"🎉 Bonus: You and your referrer earned rewards!")

def is_onboarding_complete(user):
    if not user:
        return False
    return user.onboarding_completed is True

def get_next_onboarding_step(user):
    if not user:
        return 1
    return user.onboarding_step or 1

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def get_profile_completion(profile):
    if not profile:
        return 0
    score = 0
    if profile.full_name: score += 10
    if profile.user.profile_pic: score += 10
    if profile.sport: score += 10
    if profile.experience_years: score += 10
    if profile.experience_proof_path: score += 10
    if profile.bio: score += 10
    if profile.phone: score += 10
    if profile.certifications: score += 10
    if profile.id_proof_path: score += 10
    if profile.resume_path: score += 10
    return min(score, 100)

@app.context_processor
def inject_globals():
    completion = 0
    if current_user.is_authenticated and current_user.role == 'coach':
        completion = get_profile_completion(current_user.profile)
    return dict(profile_completion=completion)

def send_notification_email(recipient_email, subject, body):
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        return
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient_email])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        print(f"Email failed: {e}")

def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2-lon1)/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return c * 6371

# AI helpers
def calculate_ai_score(job, profile):
    score = 0
    reasons = []
    if not profile:
        return 0, "Profile incomplete"

    if job.sport.lower() in (profile.sport or "").lower():
        score += 40
        reasons.append("Sport Match (+40)")
    if profile.experience_years and profile.experience_years >= 2:
        score += 30
        reasons.append("Experience > 2y (+30)")
    if profile.is_verified:
        score += 20
        reasons.append("Verified Badge (+20)")
    if job.requirements and profile.certifications:
        job_keywords = set(job.requirements.lower().replace(',', '').split())
        cert_keywords = set(profile.certifications.lower().replace(',', '').split())
        common_words = job_keywords.intersection(cert_keywords)
        if common_words:
            score += 10
            matched_terms = list(common_words)[:2]
            reasons.append(f"Cert Match: {', '.join(matched_terms)} (+10)")
    return min(score, 100), " | ".join(reasons)

def predict_salary_ai(sport, location, description, job_type):
    base = 15000
    reason = "Base entry level."
    if sport and sport.lower() == 'cricket':
        base += 10000
        reason = "Cricket (High Demand)"
    elif sport and sport.lower() == 'football':
        base += 5000
        reason = "Football (Growing Demand)"
    if location and any(city in location.lower() for city in ['mumbai', 'delhi', 'bangalore']):
        base += 8000
        reason += " + Metro City"
    desc_lower = description.lower() if description else ""
    if 'head coach' in desc_lower or 'senior' in desc_lower:
        base += 15000
        reason += " + Senior Role"
    if job_type == 'Internship':
        base = base * 0.4
        reason += " (Adjusted for Internship)"
    elif job_type == 'Part Time':
        base = base * 0.6
        reason += " (Pro-rated for Part Time)"
    elif job_type == 'Contract':
        base = base * 1.2
        reason += " (Contract Premium)"
    min_sal = int(base)
    max_sal = int(base * 1.2)
    return (f"{min_sal} - {max_sal}", reason)

def smart_parse_document(filepath):
    text = ""
    ext = filepath.rsplit('.', 1)[1].lower()
    try:
        if ext == 'pdf':
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        elif ext == 'docx':
            doc = docx.Document(filepath)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif ext == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        print(f"Parsing error: {e}")
        return {}
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    data = {'description': '', 'requirements': '', 'title': '', 'location': '', 'sport': '', 'salary': ''}
    current_section = 'description'
    desc_lines = []
    req_lines = []
    expect_next = None
    for line in lines:
        lower_line = line.lower()
        if lower_line.startswith(('job title:', 'title:', 'role:')):
            parts = line.split(':', 1)
            if len(parts) > 1 and parts[1].strip():
                data['title'] = parts[1].strip()
            continue
        if lower_line.strip() in ['job title', 'role']:
            expect_next = 'title'
            continue
        if expect_next == 'title':
            data['title'] = line
            expect_next = None
            continue
        if lower_line.startswith(('location:', 'venue:')):
            data['location'] = line.split(':', 1)[1].strip()
            continue
        if lower_line.startswith(('salary:', 'pay:')):
            data['salary'] = line.split(':', 1)[1].strip()
            continue
        if 'requirements:' in lower_line or 'qualifications:' in lower_line:
            current_section = 'requirements'
            continue
        elif 'responsibilities:' in lower_line or 'job description:' in lower_line:
            current_section = 'description'
            desc_lines.append(line)
            continue
        if current_section == 'requirements':
            req_lines.append(line)
        else:
            desc_lines.append(line)
    full_text_lower = text.lower()
    sports_list = ['Cricket', 'Football', 'Tennis', 'Basketball', 'Badminton', 'Swimming', 'Hockey', 'Athletics']
    for s in sports_list:
        if s.lower() in full_text_lower:
            data['sport'] = s
            break
    if not data['location']:
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Gurugram', 'Pune', 'Hyderabad', 'Chennai', 'Kolkata', 'Ahmedabad']
        for c in cities:
            if c.lower() in full_text_lower:
                data['location'] = c
                break
    if not data['title'] and lines:
        first_line = lines[0]
        if "coach" in first_line.lower() or "trainer" in first_line.lower():
            data['title'] = first_line
    data['description'] = "\n".join(desc_lines).strip()
    data['requirements'] = "\n".join(req_lines).strip()
    return data

def generate_ai_resume_content(profile):
    if not profile:
        return "No profile data."
    summary = f"Passionate and results-driven {profile.sport} Coach with over {profile.experience_years} years of experience. Expert in {profile.sport} techniques."
    return summary

# OTP store
otp_storage = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def send_email_otp(email):
    otp = generate_otp()
    otp_storage[email] = otp
    try:
        sender_email = "koachsmartrecruit@gmail.com"
        sender_password = "paqj jpqt iayw rigv"  # App password
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "KoachSmart - Email Verification OTP"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #2563eb;">Welcome to KoachSmart!</h2>
                <p>Your email verification OTP is:</p>
                <h1 style="color: #2563eb; letter-spacing: 5px;">{otp}</h1>
                <p>This OTP will expire in 10 minutes.</p>
                <p style="color: #666; font-size: 12px;">If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email OTP sent to {email}: {otp}")
        return True
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        return False

def send_phone_otp(phone):
    otp = generate_otp()
    otp_storage[phone] = "123456"  # demo universal OTP
    print(f"📱 Phone OTP for {phone}: 123456")
    return True

def verify_otp(identifier, entered_otp):
    stored_otp = otp_storage.get(identifier)
    if entered_otp == "123456":
        return True
    if stored_otp and stored_otp == entered_otp:
        otp_storage.pop(identifier, None)
        return True
    return False

def get_sheets_service():
    if not GOOGLE_SHEETS_CREDENTIALS or not GOOGLE_SHEETS_SPREADSHEET_ID:
        return None
    creds = Credentials.from_service_account_file(
        GOOGLE_SHEETS_CREDENTIALS,
        scopes=SHEETS_SCOPES
    )
    return build('sheets', 'v4', credentials=creds)

def append_row_to_sheet(values, sheet_range):
    service = get_sheets_service()
    if service is None:
        return
    body = {'values': [values]}
    service.spreadsheets().values().append(
        spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID,
        range=sheet_range,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()

# -----------------------------------------------------------------------------
# Role guard + final status compute
# -----------------------------------------------------------------------------
def require_role(*allowed_roles):
    if not current_user.is_authenticated:
        abort(401)
    if getattr(current_user, 'role', None) not in allowed_roles:
        abort(403)

def compute_final_status(hr: HirerReview, h: Hirer):
    if hr.l1_status == ReviewStatus.rejected.value or hr.l2_status == ReviewStatus.rejected.value or hr.compliance_status == ReviewStatus.rejected.value:
        hr.final_status = ReviewStatus.rejected.value
        hr.ready_to_post = False
        hr.final_at = datetime.utcnow()
        return
    if hr.l1_status == ReviewStatus.approved.value and hr.l2_status == ReviewStatus.approved.value and \
       hr.compliance_status in [ReviewStatus.approved.value, ReviewStatus.not_required.value]:
        hr.final_status = ReviewStatus.approved.value
        hr.ready_to_post = (h.email_otp_status == "Verified" and h.phone_otp_status == "Verified")
        hr.final_at = datetime.utcnow()
        return
    hr.final_status = ReviewStatus.pending.value
    hr.ready_to_post = False
    hr.final_at = None

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route('/coaches')
@login_required
def explore_coaches():
    sport = request.args.get('sport', type=str)
    verified = request.args.get('verified')
    min_exp = request.args.get('min_exp', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = Profile.query.join(Profile.user).filter(User.role == 'coach')
    if sport:
        query = query.filter(Profile.sport.ilike(f"%{sport}%"))
    if verified == '1':
        query = query.filter(Profile.is_verified == True)
    if min_exp is not None:
        query = query.filter(Profile.experience_years >= min_exp)
    query = query.order_by(Profile.is_verified.desc(), Profile.experience_years.desc(), Profile.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    coaches = pagination.items

    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    if user_lat is not None and user_lng is not None:
        for p in coaches:
            # If you later store lat/lng on Profile, you can compute here
            p.distance_km = None

    sports_rows = db.session.query(Profile.sport).filter(Profile.sport != None).distinct().all()
    sports = [s[0] for s in sports_rows if s[0]]
    return render_template('coach_explore.html',
                           coaches=coaches,
                           pagination=pagination,
                           sports=sports,
                           filters=dict(sport=sport, verified=verified, min_exp=min_exp, lat=user_lat, lng=user_lng))

@app.route('/plans')
@login_required
def show_plans():
    return render_template('plans.html')

@app.route('/job/new', methods=['GET', 'POST'])
@login_required
def new_job():
    if current_user.role != 'employer':
        return redirect(url_for('dashboard'))
    predicted_salary = None
    ai_reason = None
    form_data = {}
    if request.method == 'POST':
        if 'predict' in request.form:
            sport = request.form.get('sport')
            location_for_ai = request.form.get('city') or request.form.get('state') or request.form.get('country')
            description = request.form.get('description')
            job_type = request.form.get('job_type')
            predicted_salary, ai_reason = predict_salary_ai(sport, location_for_ai, description, job_type)
            form_data = request.form.to_dict()
            flash(f"AI Suggested Salary: ₹{predicted_salary}/month")
            return render_template('job_new.html', predicted_salary=predicted_salary, ai_reason=ai_reason, form_data=form_data)

        title = request.form.get('title')
        sport = request.form.get('sport')
        description = request.form.get('description')
        country = request.form.get('country')
        state = request.form.get('state')
        city = request.form.get('city')
        venue = request.form.get('venue')

        if not title or not sport or not description or not city:
            flash("Title, sport, city and description are required.")
            form_data = request.form.to_dict()
            return render_template('job_new.html', form_data=form_data)

        location = city
        new_job = Job(
            employer_id=current_user.id,
            title=title,
            sport=sport,
            location=location,
            venue=venue,
            city=city,
            state=state,
            country=country,
            description=description,
            requirements=request.form.get('requirements'),
            screening_questions=request.form.get('screening_questions'),
            salary_range=request.form.get('salary'),
            job_type=request.form.get('job_type'),
            working_hours=request.form.get('working_hours'),
            is_active=True
        )
        db.session.add(new_job)
        db.session.commit()
        flash("Job posted successfully!")
        return redirect(url_for('dashboard'))
    return render_template('job_new.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'coach':
        return redirect(url_for('dashboard'))
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        profile.full_name = request.form.get('full_name')
        profile.phone = request.form.get('phone')
        profile.sport = request.form.get('sport')
        profile.city = request.form.get('city')
        profile.travel_range = request.form.get('travel_range')
        profile.experience_years = int(request.form.get('experience_years') or 0)
        profile.certifications = request.form.get('certifications')
        profile.bio = request.form.get('bio')

        files_map = {
            'profile_image': (app.config['PROFILE_PIC_FOLDER'], 'pic_', 'current_user'),
            'cert_proof': (app.config['CERT_FOLDER'], 'cert_', 'profile'),
            'resume_pdf': (app.config['RESUME_FOLDER'], 'resume_', 'profile'),
            'experience_proof': (app.config['EXP_PROOF_FOLDER'], 'exp_', 'profile'),
            'id_proof': (app.config['ID_PROOF_FOLDER'], 'id_', 'profile')
        }
        for key, (folder, prefix, target) in files_map.items():
            f = request.files.get(key)
            if f and f.filename != '':
                filename = secure_filename(f"{prefix}{current_user.id}_{f.filename}")
                f.save(os.path.join(folder, filename))
                if key == 'profile_image':
                    current_user.profile_pic = url_for('static', filename=f'profile_pics/{filename}')
                elif key == 'id_proof':
                    profile.id_proof_path = filename
                elif key == 'cert_proof':
                    profile.cert_proof_path = filename
                elif key == 'resume_pdf':
                    profile.resume_path = filename
                elif key == 'experience_proof':
                    profile.experience_proof_path = filename
        db.session.commit()
        flash('Profile Updated Successfully!')
        return redirect(url_for('dashboard'))
    return render_template('coach_profile.html', profile=profile)

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize/google')
def authorize_google():
    try:
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token, nonce=None)
        user = User.query.filter_by(email=user_info['email']).first()
        if user:
            login_user(user)
            if user.role == 'employer':
                if not user.employer_onboarding_completed:
                    return redirect(url_for('hirer_onboarding'))
                return redirect(url_for('show_plans'))
            if user.role == 'coach':
                return redirect(url_for('show_plans'))
            return redirect(url_for('dashboard'))
        else:
            session['google_user'] = user_info
            return redirect(url_for('select_role'))
    except Exception as e:
        flash(f"Google Login Failed: {str(e)}")
        return redirect(url_for('login'))

@app.route('/select-role', methods=['GET', 'POST'])
def select_role():
    if 'google_user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        role = request.form.get('role')
        user_info = session['google_user']
        user = User(username=user_info['name'], email=user_info['email'], google_id=user_info['sub'], profile_pic=user_info['picture'], role=role)
        db.session.add(user)
        db.session.commit()
        if role == 'coach':
            db.session.add(Profile(user_id=user.id, full_name=user_info['name']))
            db.session.commit()
        login_user(user)
        session.pop('google_user', None)
        if user.role == 'employer':
            if not user.employer_onboarding_completed:
                return redirect(url_for('hirer_onboarding'))
            return redirect(url_for('show_plans'))
        if user.role == 'coach':
            return redirect(url_for('show_plans'))
        return redirect(url_for('dashboard'))
    return render_template('select_role.html')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        existing = User.query.filter_by(email=request.form.get('email')).first()
        if existing:
            flash('Email already exists')
            return redirect(url_for('register'))
        new_user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            role='coach',
            password=generate_password_hash(request.form.get('password')),
            referral_code=generate_referral_code()
        )
        referral_code = request.form.get('referral_code', '').strip().upper()
        if referral_code:
            process_referral_signup(new_user, referral_code)
        db.session.add(new_user)
        db.session.commit()
        if new_user.role == 'coach':
            db.session.add(Profile(user_id=new_user.id, full_name=new_user.username))
            db.session.commit()
        try:
            append_row_to_sheet([
                str(new_user.id), new_user.username, new_user.email,
                new_user.password or '', new_user.role or '',
                new_user.google_id or '', new_user.profile_pic or '',
                new_user.subscription_status or '', new_user.stripe_customer_id or ''
            ], sheet_range='Users!A2:I2')
        except Exception as e:
            print(f"[Sheets] Failed to append user row: {e}")
        login_user(new_user)
        if new_user.role == 'employer':
            if not new_user.employer_onboarding_completed:
                return redirect(url_for('hirer_onboarding'))
            return redirect(url_for('show_plans'))
        if new_user.role == 'coach':
            return redirect(url_for('show_plans'))
        return redirect(url_for('dashboard'))
    referral_code = request.args.get('ref', '')
    return render_template('register.html', referral_code=referral_code)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        password_valid = False
        if user and user.password and len(user.password) > 10:
            try:
                password_valid = check_password_hash(user.password, request.form.get('password'))
            except (ValueError, AttributeError):
                password_valid = False
        if user and password_valid:

            # 🚫 Block employer login from coach portal
            if user.role == 'employer':
                flash("Please login from Employer Login page.")
                return redirect(url_for('employer_login'))
            login_user(user)
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            if user.role == 'admin':
                return redirect(url_for('super_admin'))
            if user.role == 'employer':
                if not user.employer_onboarding_completed:
                    return redirect(url_for('hirer_onboarding'))
                return redirect(url_for('show_plans'))
            if user.role == 'coach':
                return redirect(url_for('show_plans'))
            return redirect(url_for('dashboard'))
        elif user and not user.password:
            flash('This account was created with Google. Please use "Login with Google".')
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('super_admin'))
    if current_user.role == 'employer':
        my_jobs = Job.query.filter_by(employer_id=current_user.id).order_by(Job.is_active.desc(), Job.posted_date.desc()).all()
        applications = []
        for job in my_jobs:
            applications.extend(job.applications)
        return render_template('admin_dashboard.html', jobs=my_jobs, applications=applications, total_applicants=len(applications))
    else:
        profile = current_user.profile
        views = profile.views if profile else 0
        query = Job.query.filter_by(is_active=True)
        if request.args.get('sport') and request.args.get('sport') != 'All':
            query = query.filter_by(sport=request.args.get('sport'))
        all_jobs = query.all()
        filtered_jobs = []
        user_lat, user_lng, radius = request.args.get('lat', type=float), request.args.get('lng', type=float), request.args.get('radius', type=float)
        if user_lat and user_lng and radius:
            for job in all_jobs:
                if job.lat and job.lng:
                    dist = haversine(user_lat, user_lng, job.lat, job.lng)
                    if dist <= radius:
                        job.distance = round(dist, 1)
                        filtered_jobs.append(job)
        else:
            filtered_jobs = all_jobs
        my_apps = Application.query.filter_by(user_id=current_user.id).all()
        avg_rating = 0
        if profile and profile.reviews:
            total = sum([r.rating for r in profile.reviews])
            avg_rating = round(total / len(profile.reviews), 1)
        return render_template('coach_listing.html', jobs=filtered_jobs, my_apps=my_apps, views=views, avg_rating=avg_rating)

@app.route('/jobs')
@login_required
def coach_jobs():
    if current_user.role != 'coach':
        return redirect(url_for('dashboard'))
    sport = request.args.get('sport')
    city = request.args.get('city')
    min_salary = request.args.get('min_salary', type=int)
    job_type = request.args.get('job_type')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = Job.query.filter_by(is_active=True)
    if sport and sport != 'All':
        query = query.filter(Job.sport.ilike(f"%{sport}%"))
    if city:
        query = query.filter(Job.location.ilike(f"%{city}%"))
    if job_type and job_type != 'All':
        query = query.filter_by(job_type=job_type)
    if min_salary:
        query = query.filter(Job.salary_range.ilike(f"%{min_salary}%"))
    query = query.order_by(Job.posted_date.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    jobs = pagination.items
    sports_rows = db.session.query(Job.sport).filter(Job.sport != None).distinct().all()
    sports = [s[0] for s in sports_rows if s[0]]
    job_types_rows = db.session.query(Job.job_type).filter(Job.job_type != None).distinct().all()
    job_types = [jt[0] for jt in job_types_rows if jt[0]]
    return render_template(
        'coach_jobs.html',
        jobs=jobs,
        pagination=pagination,
        sports=sports,
        job_types=job_types,
        filters=dict(sport=sport, city=city, min_salary=min_salary, job_type=job_type)
    )

@app.route('/job/toggle-status/<int:job_id>')
@login_required
def toggle_job_status(job_id):
    if current_user.role != 'employer':
        return redirect(url_for('dashboard'))
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for('dashboard'))
    job.is_active = not job.is_active
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/job/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if current_user.role != 'coach':
        return redirect(url_for('dashboard'))
    if Application.query.filter_by(job_id=job_id, user_id=current_user.id).first():
        flash("Already applied.")
        return redirect(url_for('dashboard'))
    job = Job.query.get_or_404(job_id)
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if get_profile_completion(profile) < 50:
        flash("Your profile is incomplete!")
        return redirect(url_for('dashboard'))
    resume_path = None
    file = request.files.get('custom_resume')
    if file and file.filename != '':
        filename = secure_filename(f"resume_{current_user.id}_{job_id}_{file.filename}")
        file.save(os.path.join(app.config['RESUME_FOLDER'], filename))
        resume_path = filename
    answers_list = []
    if job.screening_questions:
        qs = job.screening_questions.split('|')
        for i in range(len(qs)):
            ans = request.form.get(f'answer_{i}')
            answers_list.append(ans if ans else "No Answer")
    final_answers_str = "|".join(answers_list) if answers_list else None
    score, match_reasons = calculate_ai_score(job, profile)
    new_app = Application(
        job_id=job_id,
        user_id=current_user.id,
        status='Applied',
        match_score=score,
        match_reasons=match_reasons,
        custom_resume_path=resume_path,
        screening_answers=final_answers_str
    )
    db.session.add(new_app)
    db.session.commit()
    try:
        append_row_to_sheet(
            [
                str(new_app.id),
                str(new_app.job_id),
                str(new_app.user_id),
                new_app.status or '',
                str(new_app.match_score) if new_app.match_score is not None else '',
                new_app.match_reasons or '',
                new_app.applied_date.isoformat() if new_app.applied_date else '',
                new_app.custom_resume_path or '',
                new_app.screening_answers or ''
            ],
            sheet_range='Applications!A2:I2'
        )
    except Exception as e:
        print(f"[Sheets] Failed to append application row: {e}")
    flash(f"Applied! Match: {score}%")
    return redirect(url_for('dashboard'))

@app.route('/application/status/<int:app_id>/<string:new_status>', methods=['GET', 'POST'])
@login_required
def update_status(app_id, new_status):
    if current_user.role != 'employer':
        return redirect(url_for('dashboard'))
    app_obj = Application.query.get_or_404(app_id)
    if app_obj.job.employer_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for('dashboard'))
    app_obj.status = new_status
    db.session.commit()
    app_obj.applicant.profile.views += 1
    db.session.commit()
    meeting_link = ""
    if new_status == 'Interview' and request.method == 'POST':
        meeting_link = request.form.get('meeting_link', '')
    subject = f"Update on your application for {app_obj.job.title}"
    body = f"Hello {app_obj.applicant.username},\n\nStatus: {new_status}."
    if meeting_link:
        body += f"\nLink: {meeting_link}"
    send_notification_email(app_obj.applicant.email, subject, body)
    flash(f"Status updated to {new_status}")
    return redirect(url_for('dashboard'))

@app.route('/submit-review/<int:profile_id>', methods=['POST'])
@login_required
def submit_review(profile_id):
    if current_user.role != 'employer':
        return redirect(url_for('dashboard'))
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')
    new_review = Review(profile_id=profile_id, reviewer_id=current_user.id, rating=rating, comment=comment)
    db.session.add(new_review)
    db.session.commit()
    flash("Review submitted!")
    return redirect(url_for('dashboard'))

@app.route('/verify-coach/<int:profile_id>')
@login_required
def verify_coach(profile_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    profile = Profile.query.get_or_404(profile_id)
    user = User.query.get(profile.user_id)
    profile.is_verified = True
    user.education_verified = True
    db.session.commit()
    award_reward(user_id=user.id, action="education_verified", points=10)
    assign_badge(user_id=user.id, badge_field="education_verified")
    if user.onboarding_step == 3:
        user.onboarding_step = 4
        db.session.commit()
    flash("Coach education verified successfully.")
    return redirect(url_for('super_admin'))

@app.route('/reject-coach/<int:profile_id>')
@login_required
def reject_coach(profile_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    profile = Profile.query.get_or_404(profile_id)
    profile.cert_proof_path = None
    db.session.commit()
    return redirect(url_for('super_admin'))

@app.route('/coach/resume/<int:user_id>')
@login_required
def view_resume(user_id):
    if current_user.role != 'employer':
        return redirect(url_for('dashboard'))
    profile = Profile.query.filter_by(user_id=user_id).first_or_404()
    return render_template('resume_print.html', profile=profile)

@app.route('/tools/resume-builder')
@login_required
def resume_builder():
    if current_user.role != 'coach':
        return redirect(url_for('dashboard'))
    ai_summary = generate_ai_resume_content(current_user.profile)
    return render_template('resume_builder.html', profile=current_user.profile, ai_summary=ai_summary)

@app.route('/profile/delete', methods=['POST'])
@login_required
def delete_profile():
    user = User.query.get(current_user.id)
    if user.profile:
        Review.query.filter_by(profile_id=user.profile.id).delete()
        Application.query.filter_by(user_id=user.id).delete()
        db.session.delete(user.profile)
    if user.role == 'employer':
        Job.query.filter_by(employer_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    logout_user()
    flash('Your account has been permanently deleted.')
    return redirect(url_for('home'))

@app.route('/job/edit/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    if current_user.role != 'employer':
        return redirect(url_for('dashboard'))
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        flash("Unauthorized access!")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        job.title = request.form.get('title')
        job.sport = request.form.get('sport')
        job.location = request.form.get('location')
        job.description = request.form.get('description')
        job.requirements = request.form.get('requirements')
        job.screening_questions = request.form.get('screening_questions')
        job.salary_range = request.form.get('salary')
        job.job_type = request.form.get('job_type')
        job.working_hours = request.form.get('working_hours')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        if lat and lng and lat.strip() != '' and lng.strip() != '':
            job.lat = float(lat)
            job.lng = float(lng)
        db.session.commit()
        flash("Job Updated Successfully!")
        return redirect(url_for('dashboard'))
    return render_template('job_edit.html', job=job)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            flash(f"Password reset link sent to {email}. Please check your inbox.")
            return redirect(url_for('login'))
        else:
            flash("Email not found.")
    return render_template('forgot_password.html')

@app.route('/reset-password-mock', methods=['GET', 'POST'])
def reset_password_mock():
    if request.method == 'POST':
        flash("Your password has been reset! Please login.")
        return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/chat')
@login_required
def chathome():
    contacts = User.query.filter(User.id != current_user.id).all()
    return render_template('chat.html', contacts=contacts, active_contact=None, messages=[], room=None)

@app.route('/chat/<int:receiver_id>')
@login_required
def chat(receiver_id):
    contacts = User.query.filter(User.id != current_user.id).all()
    messages = Message.query.filter(
        (
            (Message.sender_id == current_user.id) &
            (Message.receiver_id == receiver_id)
        ) | (
            (Message.sender_id == receiver_id) &
            (Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp).all()
    ids = sorted([current_user.id, receiver_id])
    room = f"chat_{ids[0]}_{ids[1]}"
    Message.query.filter(
        Message.sender_id == receiver_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).update({Message.is_read: True}, synchronize_session=False)
    db.session.commit()
    return render_template('chat.html', contacts=contacts, active_contact=User.query.get_or_404(receiver_id), messages=messages, room=room)

@app.route("/text-to-resume", methods=["POST"])
def text_to_resume():
    data = request.json
    text = data.get("text", "")
    parsed = parse_resume_text(text)
    return jsonify(parsed)

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = app.config['STRIPE_WEBHOOK_SECRET']
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception:
        return "Invalid signature", 400
    if event['type'] == 'checkout.session.completed':
        data = event['data']['object']
        user = User.query.filter_by(email=data['customer_email']).first()
        if user:
            user.subscription_status = 'active'
            user.stripe_customer_id = data.get('customer')
            db.session.commit()
    if event['type'] in ['customer.subscription.deleted', 'invoice.payment_failed']:
        sub = event['data']['object']
        user = User.query.filter_by(stripe_customer_id=sub.get('customer')).first()
        if user:
            user.subscription_status = 'free'
            db.session.commit()
    return "OK", 200

@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)

@socketio.on('send_message')
def handle_send_message(data):
    room = data.get('room')
    receiver_id = data.get('receiver_id')
    text = data.get('message', '')
    if not room or not receiver_id or not text.strip():
        return
    msg = Message(sender_id=current_user.id, receiver_id=int(receiver_id), content=text.strip())
    db.session.add(msg)
    db.session.commit()
    emit('receive_message', {'content': msg.content, 'sender_id': msg.sender_id, 'timestamp': msg.timestamp.strftime('%I:%M %p')}, room=room)

@socketio.on('typing')
def typing(data):
    emit('typing', {'user_id': current_user.id}, room=data['room'], include_self=False)

@socketio.on('stop_typing')
def stop_typing(data):
    emit('stop_typing', {'user_id': current_user.id}, room=data['room'], include_self=False)

online_users = set()

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        online_users.add(current_user.id)
        emit('presence_update', {'user_id': current_user.id, 'online': True}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        online_users.discard(current_user.id)
        emit('presence_update', {'user_id': current_user.id, 'online': False}, broadcast=True)

@socketio.on('mark_seen')
def handle_mark_seen(data):
    if not current_user.is_authenticated:
        return
    message_ids = data.get('message_ids', [])
    room = data.get('room')
    if not message_ids:
        return
    Message.query.filter(Message.id.in_(message_ids), Message.receiver_id == current_user.id).update({'is_read': True}, synchronize_session=False)
    db.session.commit()
    emit('messages_seen', {'message_ids': message_ids, 'seen_by': current_user.id}, room=room, include_self=False)

@app.route('/chat/upload', methods=['POST'])
@login_required
def chatupload():
    file = request.files.get('file')
    receiver_id = request.form.get('receiver_id')
    if not file or not receiver_id:
        return jsonify({'error': 'Invalid request'}), 400
    uploaddir = Path(current_app.root_path, 'static', 'chatuploads')
    uploaddir.mkdir(parents=True, exist_ok=True)
    original = secure_filename(file.filename)
    name, ext = os.path.splitext(original)
    safename = name[:60] + ext
    filename = f"f{current_user.id}{int(time.time())}{safename}"
    filepath = uploaddir / filename
    file.save(filepath)
    fileurl = url_for('static', filename=f'chatuploads/{filename}')
    msg = Message(sender_id=current_user.id, receiver_id=int(receiver_id), content=f'[file]{fileurl}')
    db.session.add(msg)
    db.session.commit()
    ids = sorted([current_user.id, int(receiver_id)])
    room = f"chat_{ids[0]}_{ids[1]}"
    socketio.emit('receive_message', {'content': msg.content, 'sender_id': msg.sender_id, 'timestamp': msg.timestamp.strftime('%I:%M %p')}, room=room)
    return jsonify({'success': True, 'url': fileurl})

@app.route("/payment/pending")
@login_required
def payment_pending():
    return render_template("payment_pending.html")

@app.route('/about')
def about():
    return render_template('pages/about.html')

@app.route('/careers')
def careers():
    return render_template('pages/careers.html')

@app.route('/success-stories')
def success_stories():
    return render_template('pages/success_stories.html')

@app.route('/pricing')
def pricing():
    return render_template('pages/pricing.html')

@app.route('/coach-guide')
def coach_guide():
    return render_template('pages/coach_guide.html')

@app.route('/academy-guide')
def academy_guide():
    return render_template('pages/academy_guide.html')

@app.route('/safety')
def safety():
    return render_template('pages/safety.html')

@app.route('/help')
def help_center():
    return render_template('pages/help.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500), 500

@app.route('/create-checkout-session/<plan>', methods=['POST'])
@login_required
def create_checkout_session(plan):
    try:
        price_id = None
        if plan == "basic":
            price_id = app.config['STRIPE_PRICE_BASIC']
        elif plan == "pro":
            price_id = app.config['STRIPE_PRICE_PRO']
        else:
            return "Invalid plan", 400
        session_stripe = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=url_for('dashboard', _external=True),
            cancel_url=url_for('show_plans', _external=True),
        )
        return redirect(session_stripe.url, code=303)
    except Exception as e:
        return str(e), 400

@app.route('/super-admin')
@login_required
def super_admin():
    if current_user.role != 'admin':
        flash("Unauthorized")
        return redirect(url_for('dashboard'))
    pending_coaches = Profile.query.filter(Profile.cert_proof_path != None, Profile.is_verified == False).all()
    total_users = User.query.count()
    total_coaches = User.query.filter_by(role='coach').count()
    total_employers = User.query.filter_by(role='employer').count()
    total_admins = User.query.filter_by(role='admin').count()
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(is_active=True).count()
    total_applications = Application.query.count()
    paying_users = User.query.filter(User.subscription_status != 'free').count()
    return render_template(
        'super_admin.html',
        pending_coaches=pending_coaches,
        total_users=total_users,
        total_coaches=total_coaches,
        total_employers=total_employers,
        total_admins=total_admins,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        paying_users=paying_users,
    )

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    users = User.query.order_by(User.id.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:user_id>/role', methods=['POST'])
@login_required
def admin_change_role(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['coach', 'employer', 'admin']:
        user.role = new_role
        db.session.commit()
        flash('Role updated')
    return redirect(url_for('admin_users'))

@app.route('/admin/jobs')
@login_required
def admin_jobs():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    jobs = Job.query.order_by(Job.posted_date.desc()).all()
    return render_template('admin_jobs.html', jobs=jobs)

# Unified Onboarding
@app.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding_unified():
    if current_user.role != 'coach':
        return redirect(url_for('dashboard'))
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    current_step = current_user.onboarding_step or 1

    if current_step == 1 and request.method == 'POST':
        if 'send_phone_otp' in request.form:
            phone = request.form.get('phone', '').strip()
            if phone:
                send_phone_otp(phone)
                flash("📱 OTP sent to your phone!")
            return redirect(url_for('onboarding_unified'))
        if 'send_email_otp' in request.form:
            email = current_user.email
            if email:
                if send_email_otp(email):
                    flash("📧 OTP sent to your email!")
                else:
                    flash("❌ Failed to send email OTP. Please try again.")
            return redirect(url_for('onboarding_unified'))

        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        phone_otp = request.form.get('phone_otp', '').strip()
        email_otp = request.form.get('email_otp', '').strip()

        if not first_name or not last_name or not phone:
            flash("First name, last name, and phone are required.")
            return redirect(url_for('onboarding_unified'))
        if not verify_otp(phone, phone_otp):
            flash("❌ Invalid phone OTP. Please try again.")
            return redirect(url_for('onboarding_unified'))
        if not verify_otp(current_user.email, email_otp):
            flash("❌ Invalid email OTP. Please try again.")
            return redirect(url_for('onboarding_unified'))

        full_name = f"{first_name} {middle_name} {last_name}".strip()
        profile.full_name = full_name
        profile.phone = phone
        db.session.commit()

        award_reward(user_id=current_user.id, action="phone_verified", points=5)
        assign_badge(user_id=current_user.id, badge_field="phone_verified")

        current_user.onboarding_step = 2
        db.session.commit()

        session['show_phone_verified_modal'] = True
        flash("✅ Phone and email verified! Moving to Step 2...")
        return redirect(url_for('onboarding_unified'))

    elif current_step == 2 and request.method == 'POST':
        state = request.form.get('state', '').strip()
        city = request.form.get('city', '').strip()
        address = request.form.get('address', '').strip()
        travel_range = request.form.get('travel_range', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        country = request.form.get('country', '').strip()
        if not state or not city or not travel_range:
            flash("State, city, and travel range are required.")
            return redirect(url_for('onboarding_unified'))
        profile.city = f"{city}, {state}"
        profile.travel_range = travel_range
        profile.state = state
        profile.country = country
        if latitude and longitude:
            try:
                profile.latitude = float(latitude)
                profile.longitude = float(longitude)
            except:
                pass
        if address:
            profile.bio = f"Location: {address}"
        db.session.commit()
        award_reward(user_id=current_user.id, action="location_verified", points=20)
        assign_badge(user_id=current_user.id, badge_field="location_verified")
        current_user.onboarding_step = 3
        db.session.commit()
        session['show_location_verified_modal'] = True
        flash("✅ Location saved! Moving to Step 3...")
        return redirect(url_for('onboarding_unified'))

    elif current_step == 3 and request.method == 'POST':
        qualification = request.form.get('qualification', '').strip()
        specialization = request.form.get('specialization', '').strip()
        cert_file = request.files.get('certificate')
        if not qualification or not cert_file:
            flash("Qualification and certificate file are mandatory.")
            return redirect(url_for('onboarding_unified'))
        filename = secure_filename(f"edu_{current_user.id}_{cert_file.filename}")
        filepath = os.path.join(app.config['CERT_FOLDER'], filename)
        cert_file.save(filepath)
        profile.certifications = f"{qualification} - {specialization}"
        profile.cert_proof_path = filename
        db.session.commit()
        current_user.onboarding_step = 4
        db.session.commit()
        session['show_verification_pending_modal'] = True
        flash("✅ Education certificate submitted! Awaiting admin verification. Moving to Step 4...")
        return redirect(url_for('onboarding_unified'))

    elif current_step == 4 and request.method == 'POST':
        if 'skip_step_4' in request.form:
            current_user.onboarding_step = 5
            db.session.commit()
            flash("⏭️ Skipped sports certification. Moving to final step...")
            return redirect(url_for('onboarding_unified'))
        sport = request.form.get('sport', '').strip()
        organization = request.form.get('organization', '').strip()
        level = request.form.get('level', '').strip()
        cert_file = request.files.get('certificate')
        if cert_file and cert_file.filename:
            filename = secure_filename(f"sportcert_{current_user.id}_{cert_file.filename}")
            filepath = os.path.join(app.config['EXP_PROOF_FOLDER'], filename)
            cert_file.save(filepath)
            profile.experience_proof_path = filename
            db.session.commit()
            flash("✅ Sports certificate submitted for verification!")
        else:
            flash("⚠️ No certificate uploaded. Continuing to next step...")
        current_user.onboarding_step = 5
        db.session.commit()
        return redirect(url_for('onboarding_unified'))

    elif current_step == 5 and request.method == 'POST':
        sport = request.form.get('sport', '').strip()
        working_type = request.form.get('working_type', '').strip()
        range_km = request.form.get('range_km', '').strip()
        notify = bool(request.form.get('notify'))
        language = request.form.get('language', '').strip()
        read = bool(request.form.get('read'))
        write = bool(request.form.get('write'))
        speak = bool(request.form.get('speak'))
        if not sport or not working_type or not range_km:
            flash("Sport, working type, and range are mandatory.")
            return redirect(url_for('onboarding_unified'))
        profile.sport_primary = sport
        profile.working_type = working_type
        profile.range_km = int(range_km)
        profile.notify_outside_range = notify
        # Legacy single-language fields support (if present)
        profile.language = language if hasattr(profile, 'language') else None
        profile.language_read = read if hasattr(profile, 'language_read') else None
        profile.language_write = write if hasattr(profile, 'language_write') else None
        profile.language_speak = speak if hasattr(profile, 'language_speak') else None
        db.session.commit()
        award_reward(user_id=current_user.id, action="sport_added", points=5)
        if language:
            award_reward(user_id=current_user.id, action="language_completed", points=2)
            session['show_language_added_modal'] = True
        award_reward(user_id=current_user.id, action="stage5_completed", coins=100)
        current_user.onboarding_completed = True
        db.session.commit()
        award_referral_bonus(current_user.id)
        session['show_onboarding_complete_modal'] = True
        flash("🎉 Congratulations! Your profile is now complete. Welcome to KoachSmart!")
        return redirect(url_for('dashboard'))

    return render_template('onboarding_unified.html', profile=profile, current_step=current_step)
# 3) Replace your existing /hirer/onboarding route with a coach-like multi-step flow

@app.route("/hirer/onboarding", methods=["GET", "POST"])
def hirer_onboarding():
    if not current_user.is_authenticated:
        return redirect(url_for("employer_login", next=request.path))

    if current_user.role != "employer":
        flash("Unauthorized access")
        return redirect(url_for("dashboard"))
    # Safety
    if current_user.role != "employer":
        flash("Unauthorized access")
        return redirect(url_for("dashboard"))

    # Init session storage
    if not current_user.employer_onboarding_step:
        current_user.employer_onboarding_step = 1
        db.session.commit()

    current_step = current_user.employer_onboarding_step
    if "hirer_onboarding" not in session:
        session["hirer_onboarding"] = {}

    data = session["hirer_onboarding"]

    # ---------------------------
    # STEP FORM SUBMIT
    # ---------------------------
    if request.method == "POST":
        if "send_phone_otp" in request.form:
            phone = request.form.get("contact_number", "").strip()
            if validate_phone(phone):
                send_phone_otp(phone)
                flash("📱 Phone OTP sent successfully.")
            else:
                flash("❌ Invalid phone number.")
            return redirect(url_for("hirer_onboarding"))

        if "send_email_otp" in request.form:
            send_email_otp(current_user.email)
            flash("📧 Email OTP sent successfully.")
            return redirect(url_for("hirer_onboarding"))


        # 🔹 STEP 1
        if current_step == 1:

            institute = request.form.get("institute_name", "").strip()
            phone = request.form.get("contact_number", "").strip()

            if len(institute) < 3:
                flash("Institute name must be at least 3 characters.")
                return redirect(url_for("hirer_onboarding"))

            if not validate_phone(phone):
                flash("Invalid Indian mobile number.")
                return redirect(url_for("hirer_onboarding"))

            # OTP verification
            phone_otp = request.form.get("phone_otp", "")
            email_otp = request.form.get("email_otp", "")

            if not verify_otp(phone, phone_otp):
                flash("Invalid phone OTP.")
                return redirect(url_for("hirer_onboarding"))

            if not verify_otp(current_user.email, email_otp):
                flash("Invalid email OTP.")
                return redirect(url_for("hirer_onboarding"))

            data.update({
                "institute_name": institute,
                "contact_person_name": request.form.get("contact_person_name"),
                "contact_number": phone,
                "alternate_number": request.form.get("alternate_number"),
                "phone_verified": True,
                "email_verified": True,
            })


            session["hirer_onboarding"] = data
            current_user.employer_onboarding_step = 2
            db.session.commit()



        # 🔹 STEP 2
        elif current_step == 2:
            reg_doc = request.files.get("registration_doc")
            owner_doc = request.files.get("owner_id_doc")
            gst_doc = request.files.get("gst_doc")


            if not reg_doc or not allowed_file(reg_doc.filename):
                flash("Registration document is mandatory (PDF/JPG/PNG).")
                return redirect(url_for("hirer_onboarding"))

            if not owner_doc or not allowed_file(owner_doc.filename):
                flash("Owner ID proof is mandatory.")
                return redirect(url_for("hirer_onboarding"))

            data.update({
                "business_type": request.form.get("business_type"),
                "gst_number": request.form.get("gst_number"),
                "years_active": request.form.get("years_active"),
            })

            # Save files
            reg_filename = secure_filename(f"reg_{current_user.id}_{reg_doc.filename}")
            owner_filename = secure_filename(f"id_{current_user.id}_{owner_doc.filename}")

            reg_doc.save(os.path.join(app.config['UPLOAD_FOLDER'], reg_filename))
            owner_doc.save(os.path.join(app.config['UPLOAD_FOLDER'], owner_filename))

            if gst_doc and allowed_file(gst_doc.filename):
                gst_filename = secure_filename(f"gst_{current_user.id}_{gst_doc.filename}")
                gst_doc.save(os.path.join(app.config['UPLOAD_FOLDER'], gst_filename))
                data["gst_doc_path"] = gst_filename


            data["registration_doc_path"] = reg_filename
            data["owner_id_doc_path"] = owner_filename

            session["hirer_onboarding"] = data
            current_user.employer_onboarding_step = 3
            db.session.commit()

        # 🔹 STEP 3
        elif current_step == 3:
            pincode = request.form.get("pincode", "").strip()

            if not validate_pincode(pincode):
                flash("Invalid 6-digit pincode.")
                return redirect(url_for("hirer_onboarding"))

            radius = int(request.form.get("service_radius_km", 0))
            if radius < 1 or radius > 100:
                flash("Service radius must be between 1–100 km.")
                return redirect(url_for("hirer_onboarding"))

            data.update({
                "address_full": request.form.get("address_full"),
                "city": request.form.get("city"),
                "state": request.form.get("state"),
                "country": request.form.get("country"),
                "latitude": request.form.get("latitude"),
                "longitude": request.form.get("longitude"),
                "pincode": pincode,
                "service_radius_km": radius,
            })

            session["hirer_onboarding"] = data
            current_user.employer_onboarding_step = 4
            db.session.commit()


        # 🔹 STEP 4 (FINAL)
        existing = Hirer.query.filter_by(email=current_user.email).first()
        if existing:
            flash("You already completed onboarding.")
            return redirect(url_for("dashboard"))

        elif current_step == 4:
            payload = session.get("hirer_onboarding", {})
            raw_hiring_count = request.form.get("hiring_count")

            if raw_hiring_count and raw_hiring_count.isdigit():
                hiring_count = int(raw_hiring_count)
            else:
                hiring_count = None

            hirer = Hirer(
                institute_name = payload.get("institute_name"),
                contact_person_name = payload.get("contact_person_name"),
                contact_number = payload.get("contact_number"),
                alternate_number = payload.get("alternate_number"),
                business_type = payload.get("business_type"),
                gst_number = payload.get("gst_number"),
                years_active = payload.get("years_active"),
                address_full = payload.get("address_full"),
                city = payload.get("city"),
                state = payload.get("state"),
                country = payload.get("country"),
                latitude = payload.get("latitude"),
                longitude = payload.get("longitude"),
                pincode = payload.get("pincode"),
                hiring_count = hiring_count,
                registration_doc_path = payload.get("registration_doc_path"),
                owner_id_doc_path = payload.get("owner_id_doc_path"),
                gst_doc_path = payload.get("gst_doc_path"),

                hiring_mode = request.form.get("hiring_mode"),
                google_maps_link = request.form.get("google_maps_link"),
                notes = request.form.get("notes"),
                email = current_user.email,

                phone_otp_status="Verified",
                email_otp_status="Verified",
            )
            mode = request.form.get("hiring_mode")
            if not mode:
                flash("Please select hiring mode.")
                return redirect(url_for("hirer_onboarding"))


            db.session.add(hirer)
            db.session.commit()   # ✅ generate hirer.id first

            review = HirerReview(hirer_id=hirer.id)
            db.session.add(review)
            db.session.commit()

            current_user.employer_onboarding_completed = True
            current_user.employer_onboarding_step = 4
            
            db.session.commit()
            session.pop("hirer_onboarding", None)
            flash("🎉 Onboarding completed successfully!")
            return redirect(url_for("dashboard"))

        session["hirer_onboarding"] = data
        return redirect(url_for("hirer_onboarding"))

    return render_template(
        "hirer_onboarding.html",
        current_step=current_step,
        data=data
    )
@app.route('/admin/hirers', methods=['GET'])
@login_required
def admin_hirers():
    require_role('admin', 'reviewer_l1', 'reviewer_l2', 'compliance')
    hirers = Hirer.query.order_by(Hirer.created_at.desc()).all()
    reviews = {r.hirer_id: r for r in HirerReview.query.all()}
    return render_template('admin_hirer_review.html', hirers=hirers, reviews=reviews)

@app.route('/admin/hirer/<int:hirer_id>/review', methods=['POST'])
@login_required
def update_hirer_review(hirer_id):
    h = Hirer.query.get_or_404(hirer_id)
    hr = HirerReview.query.filter_by(hirer_id=hirer_id).first()
    if not hr:
        hr = HirerReview(hirer_id=hirer_id)
        db.session.add(hr)
        db.session.commit()

    action = request.form.get('action')
    status = request.form.get('status')
    note = request.form.get('note', '').strip()

    if action == 'l1':
        require_role('admin', 'reviewer_l1')
        hr.l1_status = status
        hr.l1_reviewer_id = current_user.id
        hr.l1_note = note
        hr.l1_at = datetime.utcnow()
    elif action == 'l2':
        require_role('admin', 'reviewer_l2')
        hr.l2_status = status
        hr.l2_reviewer_id = current_user.id
        hr.l2_note = note
        hr.l2_at = datetime.utcnow()
    elif action == 'compliance':
        require_role('admin', 'compliance')
        hr.compliance_status = status
        hr.compliance_reviewer_id = current_user.id
        hr.compliance_note = note
        hr.compliance_at = datetime.utcnow()
    elif action == 'docs':
        require_role('admin', 'reviewer_l1', 'reviewer_l2', 'compliance')
        hr.docs_address_proof = bool(request.form.get('docs_address_proof'))
        hr.docs_registration = bool(request.form.get('docs_registration'))
        hr.docs_website = bool(request.form.get('docs_website'))
        hr.docs_maps_link = bool(request.form.get('docs_maps_link'))
    else:
        abort(400)

    compute_final_status(hr, h)
    db.session.commit()

    try:
        append_row_to_sheet([
            hr.hirer_id, h.institute_name, hr.l1_status, hr.l1_reviewer_id or '',
            hr.l1_at.isoformat() if hr.l1_at else '',
            hr.l2_status, hr.l2_reviewer_id or '',
            hr.l2_at.isoformat() if hr.l2_at else '',
            hr.compliance_status, hr.final_status,
            'Yes' if hr.ready_to_post else 'No'
        ], sheet_range='Hirer_Review_Log!A2:K2')
    except Exception as e:
        print(f"[Sheets] Failed to append review log: {e}")

    flash("✅ Review updated.")
    return redirect(url_for('admin_hirers'))
# ================================
# EMPLOYER REGISTER
# ================================
@app.route('/employer/register', methods=['GET', 'POST'])
def employer_register():

    # If already logged in → go dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email already registered.")
            return redirect(url_for('employer_register'))

        new_user = User(
            username=request.form.get('company_name'),
            email=email,
            role='employer',   # 🔒 Force employer role
            password=generate_password_hash(request.form.get('password')),
            referral_code=generate_referral_code()
        )

        db.session.add(new_user)
        db.session.commit()

        # Optional Google Sheet logging (safe)
        try:
            append_row_to_sheet([
                str(new_user.id),
                new_user.username,
                new_user.email,
                '',
                new_user.role,
                '',
                '',
                new_user.subscription_status,
                new_user.stripe_customer_id or ''
            ], sheet_range='Users!A2:I2')
        except Exception as e:
            print(f"[Sheets] Employer append failed: {e}")

        login_user(new_user)

        # Employer always goes to onboarding
        return redirect(url_for('hirer_onboarding'))

    return render_template('employer_register.html')
# ================================
# EMPLOYER LOGIN
# ================================
@app.route('/employer/login', methods=['GET', 'POST'])
def employer_login():

    # If already logged in → go dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, role='employer').first()

        if user and user.password and check_password_hash(user.password, password):
            login_user(user)

            next_url = request.args.get("next")

            # Enforce onboarding
            if not user.employer_onboarding_completed:
                return redirect(url_for('hirer_onboarding'))

            # Redirect back if next exists
            if next_url:
                return redirect(next_url)

            return redirect(url_for('dashboard'))

        flash("Invalid employer credentials")

    return render_template('employer_login.html')

@app.route('/error')
def error_demo():
    return render_template('error.html', error_code=500), 500

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    socketio.run(app, debug=False)