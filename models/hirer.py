from datetime import datetime
from core.extensions import db
from core.constants import ReviewStatus


class Hirer(db.Model):
    __tablename__ = "hirer"

    id = db.Column(db.Integer, primary_key=True)

    institute_name = db.Column(db.String(150), nullable=False)
    contact_person_name = db.Column(db.String(150))
    email = db.Column(db.String(150), nullable=False)

    contact_number = db.Column(db.String(15), nullable=False)
    alternate_number = db.Column(db.String(15))

    business_type = db.Column(db.String(100))
    gst_number = db.Column(db.String(50))
    years_active = db.Column(db.Integer)

    address_full = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), default="India")

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    pincode = db.Column(db.String(10))

    hiring_mode = db.Column(db.String(20))
    hiring_count = db.Column(db.Integer)
    budget_range = db.Column(db.String(100))
    sports_categories = db.Column(db.Text)
    working_type = db.Column(db.String(50))

    google_maps_link = db.Column(db.Text)
    notes = db.Column(db.Text)

    # Verification
    phone_otp_status = db.Column(db.String(20), default="Pending")
    email_otp_status = db.Column(db.String(20), default="Pending")
    payment_verified = db.Column(db.Boolean, default=False)

    # Documents
    gst_doc_path = db.Column(db.String(300))
    registration_doc_path = db.Column(db.String(300))
    owner_id_doc_path = db.Column(db.String(300))

    # Risk flags
    duplicate_flag = db.Column(db.Boolean, default=False)
    risk_flag = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HirerReview(db.Model):
    __tablename__ = "hirer_review"

    id = db.Column(db.Integer, primary_key=True)

    hirer_id = db.Column(db.Integer, db.ForeignKey("hirer.id"), nullable=False)
    hirer = db.relationship("Hirer", backref=db.backref("review", uselist=False))

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
