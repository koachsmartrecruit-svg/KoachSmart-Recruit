from core.extensions import db
from models.verification import VerificationStage, VerificationDocument, CoachSlugPage
from models.user import User
from services.reward_service import award_reward
import re
import secrets
import string


class VerificationService:
    """Service for handling multi-stage verification system"""
    
    # Stage completion rewards (coins)
    STAGE_REWARDS = {
        1: 100,  # Orange Badge
        2: 500,  # Purple Badge  
        3: 1000, # Blue Badge
        4: 2000  # Green Badge
    }
    
    # Individual action rewards
    ACTION_REWARDS = {
        'phone_verified': 50,
        'email_verified': 50,
        'aadhar_verified': 50,
        'location_mapped': 100,
        'education_uploaded': 200,
        'certification_uploaded': 500,
        'first_aid_certified': 550,
        'coaching_principles_certified': 500,
        'soft_skills_certified': 500
    }
    
    @staticmethod
    def get_or_create_verification_stage(user_id):
        """Get or create verification stage for user"""
        stage = VerificationStage.query.filter_by(user_id=user_id).first()
        if not stage:
            stage = VerificationStage(user_id=user_id)
            db.session.add(stage)
            db.session.commit()
        return stage
    
    @staticmethod
    def set_language_preference(user_id, language):
        """Set user's preferred language"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        stage.preferred_language = language.lower()
        db.session.commit()
        return stage
    
    @staticmethod
    def verify_phone(user_id, phone_number):
        """Mark phone as verified and award coins"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        if not stage.phone_verified:
            stage.phone_verified = True
            stage.stage_1_coins += VerificationService.ACTION_REWARDS['phone_verified']
            
            user = User.query.get(user_id)
            user.coins += VerificationService.ACTION_REWARDS['phone_verified']
            
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def verify_email(user_id):
        """Mark email as verified and award coins"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        if not stage.email_verified:
            stage.email_verified = True
            stage.stage_1_coins += VerificationService.ACTION_REWARDS['email_verified']
            
            user = User.query.get(user_id)
            user.coins += VerificationService.ACTION_REWARDS['email_verified']
            
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def verify_aadhar(user_id, aadhar_number):
        """Mark Aadhar as verified and award coins"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        if not stage.aadhar_verified:
            stage.aadhar_verified = True
            stage.stage_1_coins += VerificationService.ACTION_REWARDS['aadhar_verified']
            
            user = User.query.get(user_id)
            user.coins += VerificationService.ACTION_REWARDS['aadhar_verified']
            
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def create_username_and_digital_id(user_id, username):
        """Create username and digital ID"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        user = User.query.get(user_id)
        
        # Create slug from username
        slug = VerificationService.create_slug(username)
        
        # Create slug page
        slug_page = CoachSlugPage(
            user_id=user_id,
            slug=slug,
            is_active=False,  # Will be activated after orange badge
            meta_title=f"{user.profile.full_name if user.profile else username} - KoachSmart Coach",
            meta_description=f"Professional sports coach {username} on KoachSmart platform"
        )
        
        stage.username_created = True
        stage.digital_id_created = True
        
        db.session.add(slug_page)
        db.session.commit()
        
        return slug
    
    @staticmethod
    def create_slug(username):
        """Create URL-friendly slug from username"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', username.lower())
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while CoachSlugPage.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    @staticmethod
    def complete_stage_1(user_id):
        """Complete Stage 1 and award Orange Badge"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        
        # Check if all Stage 1 requirements are met
        stage.calculate_stage_1_score()
        
        if (stage.name_verified and stage.phone_verified and stage.email_verified and 
            stage.aadhar_verified and stage.username_created):
            
            stage.stage_1_completed = True
            stage.orange_badge = True
            stage.stage_1_coins += VerificationService.STAGE_REWARDS[1]
            
            user = User.query.get(user_id)
            user.coins += VerificationService.STAGE_REWARDS[1]
            
            # Activate slug page
            slug_page = CoachSlugPage.query.filter_by(user_id=user_id).first()
            if slug_page:
                slug_page.is_active = True
            
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def complete_stage_2(user_id):
        """Complete Stage 2 and award Purple Badge"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        
        stage.calculate_stage_2_score()
        
        if (stage.state_selected and stage.city_selected and stage.location_mapped and 
            stage.serviceable_area_set and stage.job_type_selected):
            
            stage.stage_2_completed = True
            stage.purple_badge = True
            stage.stage_2_coins += VerificationService.STAGE_REWARDS[2]
            
            user = User.query.get(user_id)
            user.coins += VerificationService.STAGE_REWARDS[2]
            
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def complete_stage_3(user_id):
        """Complete Stage 3 and award Blue Badge"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        
        stage.calculate_stage_3_score()
        
        if (stage.education_qualification_added and stage.education_document_uploaded and 
            stage.experience_added):
            
            stage.stage_3_completed = True
            stage.blue_badge = True
            stage.stage_3_coins += VerificationService.STAGE_REWARDS[3]
            
            user = User.query.get(user_id)
            user.coins += VerificationService.STAGE_REWARDS[3]
            
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def complete_stage_4(user_id):
        """Complete Stage 4 and award Green Badge"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        
        stage.calculate_stage_4_score()
        
        if (stage.first_aid_certified and stage.coaching_principles_certified and 
            stage.cv_uploaded):
            
            stage.stage_4_completed = True
            stage.green_badge = True
            stage.stage_4_coins += VerificationService.STAGE_REWARDS[4]
            
            user = User.query.get(user_id)
            user.coins += VerificationService.STAGE_REWARDS[4]
            
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def upload_verification_document(user_id, document_type, file_path, original_filename, file_size):
        """Upload and store verification document"""
        doc = VerificationDocument(
            user_id=user_id,
            document_type=document_type,
            file_path=file_path,
            original_filename=original_filename,
            file_size=file_size
        )
        
        db.session.add(doc)
        
        # Update verification stage based on document type
        stage = VerificationService.get_or_create_verification_stage(user_id)
        
        if document_type == 'education':
            stage.education_document_uploaded = True
            user = User.query.get(user_id)
            user.coins += VerificationService.ACTION_REWARDS['education_uploaded']
            
        elif document_type == 'certification':
            stage.certification_document_uploaded = True
            user = User.query.get(user_id)
            user.coins += VerificationService.ACTION_REWARDS['certification_uploaded']
        
        db.session.commit()
        return doc
    
    @staticmethod
    def get_verification_progress(user_id):
        """Get complete verification progress for user"""
        stage = VerificationService.get_or_create_verification_stage(user_id)
        
        return {
            'current_stage': stage.get_current_stage(),
            'badge_level': stage.get_badge_level(),
            'total_coins': stage.stage_1_coins + stage.stage_2_coins + stage.stage_3_coins + stage.stage_4_coins,
            'stage_1': {
                'completed': stage.stage_1_completed,
                'score': stage.calculate_stage_1_score(),
                'max_score': 7,
                'coins': stage.stage_1_coins,
                'badge': 'orange' if stage.orange_badge else None
            },
            'stage_2': {
                'completed': stage.stage_2_completed,
                'score': stage.calculate_stage_2_score(),
                'max_score': 8,
                'coins': stage.stage_2_coins,
                'badge': 'purple' if stage.purple_badge else None
            },
            'stage_3': {
                'completed': stage.stage_3_completed,
                'score': stage.calculate_stage_3_score(),
                'max_score': 8,
                'coins': stage.stage_3_coins,
                'badge': 'blue' if stage.blue_badge else None
            },
            'stage_4': {
                'completed': stage.stage_4_completed,
                'score': stage.calculate_stage_4_score(),
                'max_score': 8,
                'coins': stage.stage_4_coins,
                'badge': 'green' if stage.green_badge else None
            }
        }
    
    @staticmethod
    def generate_referral_code(username):
        """Generate unique referral code"""
        # Use first part of username + random string
        base = re.sub(r'[^a-zA-Z0-9]', '', username.upper())[:4]
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f"{base}{random_part}"