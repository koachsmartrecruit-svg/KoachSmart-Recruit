from datetime import datetime
from core.extensions import db


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    status = db.Column(db.String(50), default="Applied")
    match_score = db.Column(db.Integer)
    match_reasons = db.Column(db.Text)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Add for consistency

    custom_resume_path = db.Column(db.String(300))
    screening_answers = db.Column(db.Text)

    job = db.relationship("Job", backref="applications")
