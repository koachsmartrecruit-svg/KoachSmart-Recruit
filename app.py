import os
import math
import random # For simulating AI processing time/score
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-key') 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///khelo_coach.db'

# --- FOLDERS ---
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['VIDEO_FOLDER'] = 'static/videos'
app.config['CERT_FOLDER'] = 'static/certs' 
app.config['RESUME_FOLDER'] = 'static/resumes'
app.config['PROFILE_PIC_FOLDER'] = 'static/profile_pics'
app.config['EXP_PROOF_FOLDER'] = 'static/experience_proofs'
app.config['ID_PROOF_FOLDER'] = 'static/id_proofs' # NEW FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 

folders = [
    app.config['UPLOAD_FOLDER'], app.config['VIDEO_FOLDER'], 
    app.config['CERT_FOLDER'], app.config['RESUME_FOLDER'],
    app.config['PROFILE_PIC_FOLDER'], app.config['EXP_PROOF_FOLDER'],
    app.config['ID_PROOF_FOLDER']
]
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# ... [Keep Email & Google Config same as before] ...
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

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

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=True)
    role = db.Column(db.String(50), default='coach') 
    google_id = db.Column(db.String(200), unique=True)
    profile_pic = db.Column(db.String(300))
    
    profile = db.relationship('Profile', backref='user', uselist=False)
    jobs = db.relationship('Job', backref='employer', lazy=True)
    applications = db.relationship('Application', backref='applicant', lazy=True)
    reviews_given = db.relationship('Review', backref='reviewer', lazy=True)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # IDENTITY
    full_name = db.Column(db.String(150)) # User MUST enter this
    phone = db.Column(db.String(20))
    
    # PROFESSIONAL
    sport = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    certifications = db.Column(db.String(500)) 
    bio = db.Column(db.Text)
    
    # STATUS
    is_verified = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    
    # FILES
    video_resume_path = db.Column(db.String(300)) 
    cert_proof_path = db.Column(db.String(300)) 
    resume_path = db.Column(db.String(300))
    experience_proof_path = db.Column(db.String(300))
    
    # NEW: ID Proof for Verification Basis
    id_proof_path = db.Column(db.String(300)) 
    
    reviews = db.relationship('Review', backref='profile', lazy=True)

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
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    screening_questions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    salary_range = db.Column(db.String(100))
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    required_skills = db.Column(db.String(300)) 

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Applied') 
    match_score = db.Column(db.Integer) 
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    custom_resume_path = db.Column(db.String(300))
    screening_answers = db.Column(db.Text)
    job = db.relationship('Job', backref='applications')

# --- HELPERS ---
@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

def get_profile_completion(profile):
    if not profile: return 0
    score = 0
    if profile.full_name: score += 10
    if profile.user.profile_pic: score += 10
    if profile.sport: score += 10
    if profile.experience_years: score += 10
    if profile.experience_proof_path: score += 10
    if profile.bio: score += 10
    if profile.phone: score += 10
    if profile.certifications: score += 10
    if profile.id_proof_path: score += 10 # Added ID proof weight
    if profile.resume_path: score += 10
    return min(score, 100)

@app.context_processor
def inject_globals():
    completion = 0
    if current_user.is_authenticated and current_user.role == 'coach':
        completion = get_profile_completion(current_user.profile)
    return dict(profile_completion=completion)

def send_notification_email(recipient_email, subject, body):
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']: return
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient_email])
        msg.body = body
        mail.send(msg)
    except Exception as e: print(f"Email failed: {e}")

def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2-lon1)/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    return c * 6371 

def calculate_ai_score(job, profile):
    score = 0
    if not profile: return 0
    if job.sport.lower() in profile.sport.lower(): score += 40
    if profile.experience_years and profile.experience_years >= 2: score += 30
    if profile.is_verified: score += 20
    if job.requirements and profile.certifications:
        if any(word in profile.certifications.lower() for word in job.requirements.lower().split()):
            score += 10
    return min(score, 100)

def predict_salary_ai(sport, location, description):
    base = 15000
    reason = "Base entry level for general coaching."
    if sport.lower() == 'cricket': base += 10000; reason = "Cricket has high market demand."
    elif sport.lower() == 'football': base += 5000; reason = "Growing demand for football academies."
    desc_lower = description.lower()
    if 'head coach' in desc_lower or 'senior' in desc_lower: base += 20000; reason += " + Head Coach role."
    if 'mumbai' in location.lower() or 'delhi' in location.lower() or 'bangalore' in location.lower(): base += 10000; reason += " + Metro City adjustment."
    return (f"{base} - {base + 10000}", reason)

def generate_ai_resume_content(profile):
    """Mocks an AI Text Generation for a Resume Summary"""
    if not profile: return "No profile data."
    
    # In a real app, this would be a prompt to OpenAI/Gemini
    # Prompt: "Write a professional summary for a {sport} coach with {exp} years experience."
    
    summary = f"Passionate and results-driven {profile.sport} Coach with over {profile.experience_years} years of experience in player development. "
    summary += f"Expert in {profile.sport} techniques, strategy, and athlete fitness. "
    if profile.certifications:
        summary += f"Certified in {profile.certifications}, committed to fostering sportsmanship and competitive excellence. "
    summary += "Proven track record of improving team performance and individual skill levels."
    
    return summary

# --- ROUTES ---

@app.route('/tools/resume-builder')
@login_required
def resume_builder():
    if current_user.role != 'coach': return redirect(url_for('dashboard'))
    # Use our AI Helper to generate content
    ai_summary = generate_ai_resume_content(current_user.profile)
    return render_template('resume_builder.html', profile=current_user.profile, ai_summary=ai_summary)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'coach': return redirect(url_for('dashboard'))
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        # Enforce Full Name
        full_name = request.form.get('full_name')
        if not full_name or len(full_name.split()) < 2:
            flash("Please enter your FULL Name (First & Last) for verification.")
            return redirect(url_for('edit_profile'))
            
        profile.full_name = full_name
        profile.phone = request.form.get('phone')
        profile.sport = request.form.get('sport')
        profile.experience_years = int(request.form.get('experience_years') or 0)
        profile.certifications = request.form.get('certifications')
        profile.bio = request.form.get('bio')
        
        # Files handling
        files_map = {
            'profile_image': (app.config['PROFILE_PIC_FOLDER'], 'pic_', 'current_user'),
            'video_resume': (app.config['VIDEO_FOLDER'], 'vid_', 'profile'),
            'cert_proof': (app.config['CERT_FOLDER'], 'cert_', 'profile'),
            'resume_pdf': (app.config['RESUME_FOLDER'], 'resume_', 'profile'),
            'experience_proof': (app.config['EXP_PROOF_FOLDER'], 'exp_', 'profile'),
            'id_proof': (app.config['ID_PROOF_FOLDER'], 'id_', 'profile') # NEW
        }
        
        for key, (folder, prefix, target) in files_map.items():
            f = request.files.get(key)
            if f and f.filename != '':
                filename = secure_filename(f"{prefix}{current_user.id}_{f.filename}")
                f.save(os.path.join(folder, filename))
                
                # Logic to update correct object
                if key == 'profile_image': current_user.profile_pic = url_for('static', filename=f'profile_pics/{filename}')
                elif key == 'id_proof': profile.id_proof_path = filename
                elif key == 'video_resume': profile.video_resume_path = filename
                elif key == 'cert_proof': profile.cert_proof_path = filename
                elif key == 'resume_pdf': profile.resume_path = filename
                elif key == 'experience_proof': profile.experience_proof_path = filename

        db.session.commit()
        flash('Profile Updated Successfully!')
        return redirect(url_for('dashboard'))
        
    return render_template('coach_profile.html', profile=profile)

# ... [Keep Login/Register/Google/Dashboard/Job Routes] ...
# For brevity, insert existing auth/dashboard/job routes here.
# (Copy from previous Complete Backend response)

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
            return redirect(url_for('dashboard'))
        else:
            session['google_user'] = user_info
            return redirect(url_for('select_role'))
    except Exception as e:
        flash(f"Google Login Failed: {str(e)}")
        return redirect(url_for('login'))

@app.route('/select-role', methods=['GET', 'POST'])
def select_role():
    if 'google_user' not in session: return redirect(url_for('login'))
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
        return redirect(url_for('dashboard'))
    return render_template('select_role.html')

@app.route('/')
def home(): return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form.get('email')).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        new_user = User(username=request.form.get('username'), email=request.form.get('email'), role=request.form.get('role'), password=generate_password_hash(request.form.get('password')))
        db.session.add(new_user)
        db.session.commit()
        if new_user.role == 'coach':
            db.session.add(Profile(user_id=new_user.id))
            db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            if user.role == 'admin': return redirect(url_for('super_admin'))
            return redirect(url_for('dashboard'))
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
    if current_user.role == 'admin': return redirect(url_for('super_admin'))
    if current_user.role == 'employer':
        my_jobs = Job.query.filter_by(employer_id=current_user.id).order_by(Job.is_active.desc(), Job.posted_date.desc()).all()
        applications = []
        for job in my_jobs: applications.extend(job.applications)
        return render_template('admin_dashboard.html', jobs=my_jobs, applications=applications, total_applicants=len(applications))
    else: 
        views = current_user.profile.views
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
        if current_user.profile.reviews:
            total = sum([r.rating for r in current_user.profile.reviews])
            avg_rating = round(total / len(current_user.profile.reviews), 1)
        return render_template('coach_listing.html', jobs=filtered_jobs, my_apps=my_apps, views=views, avg_rating=avg_rating)

@app.route('/job/new', methods=['GET', 'POST'])
@login_required
def new_job():
    if current_user.role != 'employer': return redirect(url_for('dashboard'))
    predicted_salary = None
    ai_reason = None
    form_data = {}
    if request.method == 'POST':
        if 'predict' in request.form:
            sport = request.form.get('sport')
            location = request.form.get('location')
            description = request.form.get('description')
            predicted_salary, ai_reason = predict_salary_ai(sport, location, description)
            flash(f"AI Suggested Salary: ₹{predicted_salary}/month")
            form_data = {
                'title': request.form.get('title'),
                'sport': request.form.get('sport'),
                'location': request.form.get('location'),
                'description': request.form.get('description'),
                'requirements': request.form.get('requirements'),
                'screening_questions': request.form.get('screening_questions'),
                'lat': request.form.get('lat'),
                'lng': request.form.get('lng')
            }
            return render_template('job_new.html', predicted_salary=predicted_salary, ai_reason=ai_reason, form_data=form_data)
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        new_job = Job(
            employer_id=current_user.id,
            title=request.form.get('title'),
            sport=request.form.get('sport'),
            location=request.form.get('location'),
            lat=float(lat) if lat and lat.strip() != '' else None,
            lng=float(lng) if lng and lng.strip() != '' else None,
            description=request.form.get('description'),
            requirements=request.form.get('requirements'),
            screening_questions=request.form.get('screening_questions'),
            salary_range=request.form.get('salary'),
            is_active=True
        )
        db.session.add(new_job)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('job_new.html')

@app.route('/job/toggle-status/<int:job_id>')
@login_required
def toggle_job_status(job_id):
    if current_user.role != 'employer': return redirect(url_for('dashboard'))
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
    if current_user.role != 'coach': return redirect(url_for('dashboard'))
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
    score = calculate_ai_score(job, profile)
    new_app = Application(
        job_id=job_id, 
        user_id=current_user.id, 
        match_score=score, 
        custom_resume_path=resume_path,
        screening_answers=final_answers_str
    )
    db.session.add(new_app)
    db.session.commit()
    flash(f"Applied! Match: {score}%")
    return redirect(url_for('dashboard'))

@app.route('/application/status/<int:app_id>/<string:new_status>', methods=['GET', 'POST'])
@login_required
def update_status(app_id, new_status):
    if current_user.role != 'employer': return redirect(url_for('dashboard'))
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
    if meeting_link: body += f"\nLink: {meeting_link}"
    send_notification_email(app_obj.applicant.email, subject, body)
    flash(f"Status updated to {new_status}")
    return redirect(url_for('dashboard'))

@app.route('/submit-review/<int:profile_id>', methods=['POST'])
@login_required
def submit_review(profile_id):
    if current_user.role != 'employer': return redirect(url_for('dashboard'))
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')
    new_review = Review(profile_id=profile_id, reviewer_id=current_user.id, rating=rating, comment=comment)
    db.session.add(new_review)
    db.session.commit()
    flash("Review submitted!")
    return redirect(url_for('dashboard'))

@app.route('/super-admin')
@login_required
def super_admin():
    if current_user.role != 'admin':
        flash("Unauthorized")
        return redirect(url_for('dashboard'))
    coaches = Profile.query.filter(Profile.cert_proof_path != None, Profile.is_verified == False).all()
    return render_template('super_admin.html', coaches=coaches)

@app.route('/verify-coach/<int:profile_id>')
@login_required
def verify_coach(profile_id):
    if current_user.role != 'admin': return redirect(url_for('dashboard'))
    profile = Profile.query.get_or_404(profile_id)
    profile.is_verified = True
    db.session.commit()
    return redirect(url_for('super_admin'))

@app.route('/reject-coach/<int:profile_id>')
@login_required
def reject_coach(profile_id):
    if current_user.role != 'admin': return redirect(url_for('dashboard'))
    profile = Profile.query.get_or_404(profile_id)
    profile.cert_proof_path = None
    db.session.commit()
    return redirect(url_for('super_admin'))

@app.route('/coach/resume/<int:user_id>')
@login_required
def view_resume(user_id):
    if current_user.role != 'employer': return redirect(url_for('dashboard'))
    profile = Profile.query.filter_by(user_id=user_id).first_or_404()
    return render_template('resume_print.html', profile=profile)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)