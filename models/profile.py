from core.extensions import db


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Personal
    full_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)

    # Sports
    sport = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    certifications = db.Column(db.String(500))

    # Location
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    travel_range = db.Column(db.String(100))

    # Preferences
    sport_primary = db.Column(db.String(100))
    working_type = db.Column(db.String(50))
    range_km = db.Column(db.Integer)
    notify_outside_range = db.Column(db.Boolean, default=False)
    languages = db.Column(db.Text)  # JSON string

    # Documents
    cert_proof_path = db.Column(db.String(300))
    resume_path = db.Column(db.String(300))
    experience_proof_path = db.Column(db.String(300))
    id_proof_path = db.Column(db.String(300))

    # Stats
    is_verified = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
