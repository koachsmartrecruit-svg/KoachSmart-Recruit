from datetime import datetime
from core.extensions import db


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    employer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Job basics
    title = db.Column(db.String(150), nullable=False)
    sport = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Location
    location = db.Column(db.String(150), nullable=False)
    venue = db.Column(db.String(150))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    # Hiring
    requirements = db.Column(db.Text)
    screening_questions = db.Column(db.Text)
    required_skills = db.Column(db.String(300))
    salary_range = db.Column(db.String(100))
    job_type = db.Column(db.String(50), default="Full Time")
    working_hours = db.Column(db.String(100))

    # Status
    is_active = db.Column(db.Boolean, default=True)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
