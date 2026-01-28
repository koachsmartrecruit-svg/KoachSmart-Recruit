from core.extensions import db
from datetime import datetime


class VerificationStage(db.Model):
    """Tracks verification stages and badges for coaches"""
    __tablename__ = "verification_stage"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    # Language preference
    preferred_language = db.Column(db.String(50), default="english")
    
    # Stage 1 - Orange Badge (Basic Verification)
    stage_1_completed = db.Column(db.Boolean, default=False)
    stage_1_score = db.Column(db.Integer, default=0)
    stage_1_coins = db.Column(db.Integer, default=0)
    
    # Personal details
    name_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    aadhar_verified = db.Column(db.Boolean, default=False)
    username_created = db.Column(db.Boolean, default=False)
    password_set = db.Column(db.Boolean, default=False)
    digital_id_created = db.Column(db.Boolean, default=False)
    
    # Stage 2 - Purple Badge (Location & Availability)
    stage_2_completed = db.Column(db.Boolean, default=False)
    stage_2_score = db.Column(db.Integer, default=0)
    stage_2_coins = db.Column(db.Integer, default=0)
    
    # Location details
    language_selected = db.Column(db.Boolean, default=False)
    state_selected = db.Column(db.Boolean, default=False)
    city_selected = db.Column(db.Boolean, default=False)
    location_mapped = db.Column(db.Boolean, default=False)
    serviceable_area_set = db.Column(db.Boolean, default=False)
    job_type_selected = db.Column(db.Boolean, default=False)
    specific_location_set = db.Column(db.Boolean, default=False)
    range_set = db.Column(db.Boolean, default=False)
    
    # Stage 3 - Blue Badge (Education & Experience)
    stage_3_completed = db.Column(db.Boolean, default=False)
    stage_3_score = db.Column(db.Integer, default=0)
    stage_3_coins = db.Column(db.Integer, default=0)
    
    # Education details
    education_qualification_added = db.Column(db.Boolean, default=False)
    specialization_added = db.Column(db.Boolean, default=False)
    education_document_uploaded = db.Column(db.Boolean, default=False)
    professional_certification_added = db.Column(db.Boolean, default=False)
    certification_document_uploaded = db.Column(db.Boolean, default=False)
    playing_level_added = db.Column(db.Boolean, default=False)
    playing_document_uploaded = db.Column(db.Boolean, default=False)
    experience_added = db.Column(db.Boolean, default=False)
    
    # Stage 4 - Green Badge (Certified Coach)
    stage_4_completed = db.Column(db.Boolean, default=False)
    stage_4_score = db.Column(db.Integer, default=0)
    stage_4_coins = db.Column(db.Integer, default=0)
    
    # Advanced certifications
    first_aid_certified = db.Column(db.Boolean, default=False)
    coaching_principles_certified = db.Column(db.Boolean, default=False)
    soft_skills_certified = db.Column(db.Boolean, default=False)
    cv_uploaded = db.Column(db.Boolean, default=False)
    social_media_content_uploaded = db.Column(db.Boolean, default=False)
    
    # Final verification
    aadhar_verification_complete = db.Column(db.Boolean, default=False)
    pcc_verified = db.Column(db.Boolean, default=False)
    noc_certified = db.Column(db.Boolean, default=False)
    
    # Badges earned
    orange_badge = db.Column(db.Boolean, default=False)
    purple_badge = db.Column(db.Boolean, default=False)
    blue_badge = db.Column(db.Boolean, default=False)
    green_badge = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="verification_stage")
    
    def calculate_stage_1_score(self):
        """Calculate Stage 1 completion score"""
        fields = [
            self.name_verified, self.phone_verified, self.email_verified,
            self.aadhar_verified, self.username_created, self.password_set,
            self.digital_id_created
        ]
        completed = sum(1 for field in fields if field)
        self.stage_1_score = completed
        return completed
    
    def calculate_stage_2_score(self):
        """Calculate Stage 2 completion score"""
        fields = [
            self.language_selected, self.state_selected, self.city_selected,
            self.location_mapped, self.serviceable_area_set, self.job_type_selected,
            self.specific_location_set, self.range_set
        ]
        completed = sum(1 for field in fields if field)
        self.stage_2_score = completed
        return completed
    
    def calculate_stage_3_score(self):
        """Calculate Stage 3 completion score"""
        fields = [
            self.education_qualification_added, self.specialization_added,
            self.education_document_uploaded, self.professional_certification_added,
            self.certification_document_uploaded, self.playing_level_added,
            self.playing_document_uploaded, self.experience_added
        ]
        completed = sum(1 for field in fields if field)
        self.stage_3_score = completed
        return completed
    
    def calculate_stage_4_score(self):
        """Calculate Stage 4 completion score"""
        fields = [
            self.first_aid_certified, self.coaching_principles_certified,
            self.soft_skills_certified, self.cv_uploaded,
            self.social_media_content_uploaded, self.aadhar_verification_complete,
            self.pcc_verified, self.noc_certified
        ]
        completed = sum(1 for field in fields if field)
        self.stage_4_score = completed
        return completed
    
    def get_current_stage(self):
        """Get the current verification stage"""
        if not self.stage_1_completed:
            return 1
        elif not self.stage_2_completed:
            return 2
        elif not self.stage_3_completed:
            return 3
        elif not self.stage_4_completed:
            return 4
        else:
            return 5  # All stages completed
    
    def get_badge_level(self):
        """Get the current badge level"""
        if self.green_badge:
            return "green"
        elif self.blue_badge:
            return "blue"
        elif self.purple_badge:
            return "purple"
        elif self.orange_badge:
            return "orange"
        else:
            return "none"


class VerificationDocument(db.Model):
    """Stores uploaded verification documents"""
    __tablename__ = "verification_document"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    document_type = db.Column(db.String(100), nullable=False)  # aadhar, education, certification, etc.
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    
    # Verification status
    verification_status = db.Column(db.String(50), default="pending")  # pending, verified, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    verification_notes = db.Column(db.Text)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref="verification_documents")
    verifier = db.relationship("User", foreign_keys=[verified_by])


class CoachSlugPage(db.Model):
    """Public slug pages for coaches (koachsmart.com/coach/rahul-sharma)"""
    __tablename__ = "coach_slug_page"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    
    slug = db.Column(db.String(255), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=False)  # Activated after orange badge
    
    # SEO fields
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    
    # Public profile data
    public_bio = db.Column(db.Text)
    achievements = db.Column(db.Text)
    testimonials = db.Column(db.Text)
    
    # Stats
    page_views = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="slug_page")