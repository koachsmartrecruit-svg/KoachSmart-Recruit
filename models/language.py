"""
Language preference models for multi-language onboarding system
"""

from datetime import datetime
from core.extensions import db


class LanguagePreference(db.Model):
    """Stores user language preferences and content customization"""
    
    __tablename__ = "language_preference"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Language settings
    primary_language = db.Column(db.String(50), default='english')
    secondary_language = db.Column(db.String(50))
    audio_instructions = db.Column(db.Boolean, default=True)
    
    # Content preferences
    form_language = db.Column(db.String(50))
    notification_language = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship("User", backref=db.backref("language_preference", uselist=False))
    
    def __repr__(self):
        return f'<LanguagePreference {self.user_id}: {self.primary_language}>'


class ReferralSystem(db.Model):
    """Tracks referral relationships and rewards"""
    
    __tablename__ = "referral_system"
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Referral details
    referral_code = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, orange_completed, premium_completed
    
    # Rewards tracking
    coins_awarded = db.Column(db.Integer, default=0)
    milestone_reached = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    referrer = db.relationship("User", foreign_keys=[referrer_id], backref="referrals_made")
    referred = db.relationship("User", foreign_keys=[referred_id], backref="referral_received")
    
    def __repr__(self):
        return f'<ReferralSystem {self.referral_code}: {self.status}>'


class EnhancedVerificationStage(db.Model):
    """Enhanced verification stage tracking with detailed progress"""
    
    __tablename__ = "enhanced_verification_stage"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Stage information
    stage_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4
    stage_name = db.Column(db.String(100))  # Orange, Purple, Blue, Green
    
    # Progress tracking
    stage_start_time = db.Column(db.DateTime)
    stage_completion_time = db.Column(db.DateTime)
    time_spent_minutes = db.Column(db.Integer, default=0)
    completion_percentage = db.Column(db.Float, default=0.0)
    
    # Verification details
    requirements_met = db.Column(db.JSON)  # Store which requirements are completed
    documents_uploaded = db.Column(db.JSON)  # Store document upload status
    verification_status = db.Column(db.String(50), default='pending')  # pending, verified, rejected
    
    # Rewards
    coins_earned = db.Column(db.Integer, default=0)
    badge_awarded = db.Column(db.String(50))
    
    # Referral tracking
    referral_code_generated = db.Column(db.Boolean, default=False)
    referrals_count = db.Column(db.Integer, default=0)
    referral_coins_earned = db.Column(db.Integer, default=0)
    
    # Premium features (Stage 4)
    premium_features_unlocked = db.Column(db.Boolean, default=False)
    cv_builder_completed = db.Column(db.Boolean, default=False)
    social_media_integration = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship("User", backref="enhanced_verification_stages")
    
    def __repr__(self):
        return f'<EnhancedVerificationStage {self.user_id}: Stage {self.stage_number} ({self.stage_name})>'