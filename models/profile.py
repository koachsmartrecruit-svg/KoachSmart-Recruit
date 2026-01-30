from core.extensions import db


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Personal
    full_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    aadhar_number = db.Column(db.String(20))

    # Sports
    sport = db.Column(db.String(100))
    sport2 = db.Column(db.String(100))  # Secondary sport
    experience_years = db.Column(db.String(50))
    certifications = db.Column(db.String(500))
    playing_level = db.Column(db.String(100))

    # Location
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    location = db.Column(db.String(200))  # Specific location like "South Delhi"
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    serviceable_area = db.Column(db.String(50))  # 5km, 10km, etc.
    range_km = db.Column(db.Integer, default=5)
    specific_locations = db.Column(db.Text)  # Comma-separated specific areas

    # Coaching Preferences
    working_type = db.Column(db.String(50))  # full_time / part_time / session
    job_types = db.Column(db.Text)  # Comma-separated: full_time, part_time, session
    service_radius_km = db.Column(db.Integer, nullable=True)

    # Education & Professional
    education = db.Column(db.String(100))
    specialization = db.Column(db.String(200))
    has_professional_cert = db.Column(db.Boolean, default=False)
    cert_name = db.Column(db.String(200))

    # Optional Preferences
    sport_primary = db.Column(db.String(100))
    notify_outside_range = db.Column(db.Boolean, default=False)
    languages = db.Column(db.Text)  # Comma-separated languages

    # Documents
    cert_proof_path = db.Column(db.String(300))
    resume_path = db.Column(db.String(300))
    experience_proof_path = db.Column(db.String(300))
    id_proof_path = db.Column(db.String(300))
    education_doc_path = db.Column(db.String(300))
    cert_doc_path = db.Column(db.String(300))
    playing_doc_path = db.Column(db.String(300))

    # Public Profile
    public_slug = db.Column(db.String(200), unique=True)  # For koachsmart.com/coach/username

    # Stats
    is_verified = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
