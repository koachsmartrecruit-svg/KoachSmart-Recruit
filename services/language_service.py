"""
Language Engine and Localization Service
Handles multi-language support and content localization for the enhanced onboarding system
"""

import json
import os
from typing import Dict, Optional, Any
from flask import current_app
from core.extensions import db
from models.language import LanguagePreference
from models.user import User


class LanguageEngine:
    """Handles multi-language support and content localization"""
    
    SUPPORTED_LANGUAGES = {
        'english': {
            'code': 'en',
            'name': 'English',
            'native_name': 'English',
            'flag': '🇺🇸'
        },
        'hindi': {
            'code': 'hi',
            'name': 'Hindi',
            'native_name': 'हिंदी',
            'flag': '🇮🇳'
        },
        'tamil': {
            'code': 'ta',
            'name': 'Tamil',
            'native_name': 'தமிழ்',
            'flag': '🇮🇳'
        },
        'telugu': {
            'code': 'te',
            'name': 'Telugu',
            'native_name': 'తెలుగు',
            'flag': '🇮🇳'
        },
        'bengali': {
            'code': 'bn',
            'name': 'Bengali',
            'native_name': 'বাংলা',
            'flag': '🇮🇳'
        }
    }
    
    # Default content translations
    DEFAULT_CONTENT = {
        'english': {
            # Onboarding stages
            'stage_1_title': 'Personal Information',
            'stage_1_subtitle': 'Let\'s start with your basic details and verify your contact information.',
            'stage_2_title': 'Location & Sport',
            'stage_2_subtitle': 'Tell us about your location and coaching expertise.',
            'stage_3_title': 'Education Certificate',
            'stage_3_subtitle': 'Upload your education certificate and set your preferences.',
            'stage_4_title': 'Premium Certification',
            'stage_4_subtitle': 'Complete advanced certifications for premium features.',
            
            # Form labels
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'phone_number': 'Phone Number',
            'email_address': 'Email Address',
            'aadhar_number': 'Aadhar Number',
            'username': 'Username',
            'state': 'State',
            'city': 'City',
            'sport': 'Primary Sport',
            'experience': 'Coaching Experience',
            'certificate': 'Education Certificate',
            'working_type': 'Preferred Working Type',
            
            # Buttons
            'send_otp': 'Send OTP',
            'verify_continue': 'Verify & Continue',
            'continue': 'Continue',
            'complete_onboarding': 'Complete Onboarding',
            'skip_step': 'Skip This Step',
            
            # Messages
            'otp_sent_phone': 'OTP sent to your phone!',
            'otp_sent_email': 'OTP sent to your email!',
            'step_completed': 'Step completed successfully!',
            'onboarding_completed': 'Congratulations! Onboarding completed successfully!',
            'coins_earned': 'You earned {coins} coins and the {badge}!',
            'features_unlocked': 'You can now apply for jobs and access all features!',
            
            # Validation messages
            'required_field': 'This field is required',
            'invalid_phone': 'Please enter a valid phone number',
            'invalid_email': 'Please enter a valid email address',
            'invalid_otp': 'Invalid OTP. Please try again.',
            'username_taken': 'Username is already taken',
            'file_too_large': 'File size must be less than 5MB',
            'invalid_file_type': 'Please upload a valid file (PDF, JPG, PNG)',
            
            # Audio instructions
            'audio_stage_1': 'Welcome to KoachSmart onboarding. Please enter your personal details and verify your phone and email.',
            'audio_stage_2': 'Now, let\'s set up your location and coaching preferences.',
            'audio_stage_3': 'Please upload your education certificate to complete verification.',
            'audio_stage_4': 'Complete advanced certifications to unlock premium features.'
        },
        
        'hindi': {
            # Onboarding stages
            'stage_1_title': 'व्यक्तिगत जानकारी',
            'stage_1_subtitle': 'आइए आपकी बुनियादी जानकारी से शुरुआत करते हैं और आपकी संपर्क जानकारी सत्यापित करते हैं।',
            'stage_2_title': 'स्थान और खेल',
            'stage_2_subtitle': 'हमें अपने स्थान और कोचिंग विशेषज्ञता के बारे में बताएं।',
            'stage_3_title': 'शिक्षा प्रमाणपत्र',
            'stage_3_subtitle': 'अपना शिक्षा प्रमाणपत्र अपलोड करें और अपनी प्राथमिकताएं सेट करें।',
            'stage_4_title': 'प्रीमियम प्रमाणन',
            'stage_4_subtitle': 'प्रीमियम सुविधाओं के लिए उन्नत प्रमाणन पूरा करें।',
            
            # Form labels
            'first_name': 'पहला नाम',
            'last_name': 'अंतिम नाम',
            'phone_number': 'फोन नंबर',
            'email_address': 'ईमेल पता',
            'aadhar_number': 'आधार नंबर',
            'username': 'उपयोगकर्ता नाम',
            'state': 'राज्य',
            'city': 'शहर',
            'sport': 'मुख्य खेल',
            'experience': 'कोचिंग अनुभव',
            'certificate': 'शिक्षा प्रमाणपत्र',
            'working_type': 'पसंदीदा कार्य प्रकार',
            
            # Buttons
            'send_otp': 'OTP भेजें',
            'verify_continue': 'सत्यापित करें और जारी रखें',
            'continue': 'जारी रखें',
            'complete_onboarding': 'ऑनबोर्डिंग पूरा करें',
            'skip_step': 'यह चरण छोड़ें',
            
            # Messages
            'otp_sent_phone': 'आपके फोन पर OTP भेजा गया!',
            'otp_sent_email': 'आपके ईमेल पर OTP भेजा गया!',
            'step_completed': 'चरण सफलतापूर्वक पूरा हुआ!',
            'onboarding_completed': 'बधाई हो! ऑनबोर्डिंग सफलतापूर्वक पूरा हुआ!',
            'coins_earned': 'आपने {coins} सिक्के और {badge} अर्जित किए!',
            'features_unlocked': 'अब आप नौकरियों के लिए आवेदन कर सकते हैं और सभी सुविधाओं का उपयोग कर सकते हैं!',
            
            # Validation messages
            'required_field': 'यह फील्ड आवश्यक है',
            'invalid_phone': 'कृपया एक वैध फोन नंबर दर्ज करें',
            'invalid_email': 'कृपया एक वैध ईमेल पता दर्ज करें',
            'invalid_otp': 'अमान्य OTP। कृपया पुनः प्रयास करें।',
            'username_taken': 'उपयोगकर्ता नाम पहले से लिया गया है',
            'file_too_large': 'फाइल का आकार 5MB से कम होना चाहिए',
            'invalid_file_type': 'कृपया एक वैध फाइल अपलोड करें (PDF, JPG, PNG)',
            
            # Audio instructions
            'audio_stage_1': 'KoachSmart ऑनबोर्डिंग में आपका स्वागत है। कृपया अपनी व्यक्तिगत जानकारी दर्ज करें और अपने फोन और ईमेल को सत्यापित करें।',
            'audio_stage_2': 'अब, आइए अपना स्थान और कोचिंग प्राथमिकताएं सेट करें।',
            'audio_stage_3': 'सत्यापन पूरा करने के लिए कृपया अपना शिक्षा प्रमाणपत्र अपलोड करें।',
            'audio_stage_4': 'प्रीमियम सुविधाओं को अनलॉक करने के लिए उन्नत प्रमाणन पूरा करें।'
        },
        
        'tamil': {
            # Onboarding stages
            'stage_1_title': 'தனிப்பட்ட தகவல்',
            'stage_1_subtitle': 'உங்கள் அடிப்படை விவரங்களுடன் தொடங்கி உங்கள் தொடர்பு தகவலை சரிபார்ப்போம்.',
            'stage_2_title': 'இடம் மற்றும் விளையாட்டு',
            'stage_2_subtitle': 'உங்கள் இடம் மற்றும் பயிற்சி நிபுணத்துவத்தைப் பற்றி எங்களிடம் கூறுங்கள்.',
            'stage_3_title': 'கல்வி சான்றிதழ்',
            'stage_3_subtitle': 'உங்கள் கல்வி சான்றிதழை பதிவேற்றி உங்கள் விருப்பங்களை அமைக்கவும்.',
            'stage_4_title': 'பிரீமியம் சான்றிதழ்',
            'stage_4_subtitle': 'பிரீமியம் அம்சங்களுக்கு மேம்பட்ட சான்றிதழ்களை முடிக்கவும்.',
            
            # Form labels
            'first_name': 'முதல் பெயர்',
            'last_name': 'கடைசி பெயர்',
            'phone_number': 'தொலைபேசி எண்',
            'email_address': 'மின்னஞ்சல் முகவரி',
            'aadhar_number': 'ஆதார் எண்',
            'username': 'பயனர் பெயர்',
            'state': 'மாநிலம்',
            'city': 'நகரம்',
            'sport': 'முதன்மை விளையாட்டு',
            'experience': 'பயிற்சி அனுபவம்',
            'certificate': 'கல்வி சான்றிதழ்',
            'working_type': 'விருப்பமான வேலை வகை',
            
            # Buttons
            'send_otp': 'OTP அனுப்பு',
            'verify_continue': 'சரிபார்த்து தொடரவும்',
            'continue': 'தொடரவும்',
            'complete_onboarding': 'ஆன்போர்டிங் முடிக்கவும்',
            'skip_step': 'இந்த படியை தவிர்க்கவும்',
            
            # Messages
            'otp_sent_phone': 'உங்கள் தொலைபேசிக்கு OTP அனுப்பப்பட்டது!',
            'otp_sent_email': 'உங்கள் மின்னஞ்சலுக்கு OTP அனுப்பப்பட்டது!',
            'step_completed': 'படி வெற்றிகரமாக முடிந்தது!',
            'onboarding_completed': 'வாழ்த்துக்கள்! ஆன்போர்டிங் வெற்றிகரமாக முடிந்தது!',
            'coins_earned': 'நீங்கள் {coins} நாணயங்கள் மற்றும் {badge} பெற்றுள்ளீர்கள்!',
            'features_unlocked': 'இப்போது நீங்கள் வேலைகளுக்கு விண்ணப்பிக்கலாம் மற்றும் அனைத்து அம்சங்களையும் அணுகலாம்!',
            
            # Validation messages
            'required_field': 'இந்த புலம் தேவை',
            'invalid_phone': 'தயவுசெய்து சரியான தொலைபேசி எண்ணை உள்ளிடவும்',
            'invalid_email': 'தயவுசெய்து சரியான மின்னஞ்சல் முகவரியை உள்ளிடவும்',
            'invalid_otp': 'தவறான OTP. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.',
            'username_taken': 'பயனர் பெயர் ஏற்கனவே எடுக்கப்பட்டுள்ளது',
            'file_too_large': 'கோப்பு அளவு 5MB க்கும் குறைவாக இருக்க வேண்டும்',
            'invalid_file_type': 'தயவுசெய்து சரியான கோப்பை பதிவேற்றவும் (PDF, JPG, PNG)',
            
            # Audio instructions
            'audio_stage_1': 'KoachSmart ஆன்போர்டிங்கிற்கு வரவேற்கிறோம். தயவுசெய்து உங்கள் தனிப்பட்ட விவரங்களை உள்ளிட்டு உங்கள் தொலைபேசி மற்றும் மின்னஞ்சலை சரிபார்க்கவும்.',
            'audio_stage_2': 'இப்போது, உங்கள் இடம் மற்றும் பயிற்சி விருப்பங்களை அமைப்போம்.',
            'audio_stage_3': 'சரிபார்ப்பை முடிக்க தயவுசெய்து உங்கள் கல்வி சான்றிதழை பதிவேற்றவும்.',
            'audio_stage_4': 'பிரீமியம் அம்சங்களை திறக்க மேம்பட்ட சான்றிதழ்களை முடிக்கவும்.'
        }
    }
    
    def __init__(self):
        self._content_cache = {}
    
    def get_supported_languages(self) -> Dict[str, Dict[str, str]]:
        """Get list of supported languages with metadata"""
        return self.SUPPORTED_LANGUAGES
    
    def get_localized_content(self, language_code: str, content_key: str, **kwargs) -> str:
        """
        Get localized content for a specific key
        
        Args:
            language_code: Language code (e.g., 'english', 'hindi')
            content_key: Content key to retrieve
            **kwargs: Format parameters for string formatting
            
        Returns:
            Localized content string
        """
        # Default to English if language not supported
        if language_code not in self.SUPPORTED_LANGUAGES:
            language_code = 'english'
        
        # Get content from cache or default
        content = self.DEFAULT_CONTENT.get(language_code, {})
        
        # Get the specific content or fallback to English
        text = content.get(content_key)
        if not text and language_code != 'english':
            text = self.DEFAULT_CONTENT.get('english', {}).get(content_key, content_key)
        
        # Format with provided parameters
        if text and kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass  # Return unformatted text if formatting fails
        
        return text or content_key
    
    def set_user_language_preference(self, user_id: int, language: str) -> bool:
        """
        Set language preference for a user
        
        Args:
            user_id: User ID
            language: Language code
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate language
            if language not in self.SUPPORTED_LANGUAGES:
                return False
            
            # Get or create language preference
            preference = LanguagePreference.query.filter_by(user_id=user_id).first()
            
            if not preference:
                preference = LanguagePreference(
                    user_id=user_id,
                    primary_language=language,
                    form_language=language,
                    notification_language=language
                )
                db.session.add(preference)
            else:
                preference.primary_language = language
                preference.form_language = language
                preference.notification_language = language
            
            # Also update user's preferred_language field
            user = User.query.get(user_id)
            if user:
                user.preferred_language = language
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error setting language preference: {str(e)}")
            return False
    
    def get_user_language_preference(self, user_id: int) -> str:
        """
        Get user's language preference
        
        Args:
            user_id: User ID
            
        Returns:
            Language code (defaults to 'english')
        """
        try:
            preference = LanguagePreference.query.filter_by(user_id=user_id).first()
            if preference:
                return preference.primary_language
            
            # Fallback to user table
            user = User.query.get(user_id)
            if user and user.preferred_language:
                return user.preferred_language
            
            return 'english'
            
        except Exception:
            return 'english'
    
    def get_audio_instructions(self, language_code: str, stage: int) -> str:
        """
        Get audio instructions for a specific stage
        
        Args:
            language_code: Language code
            stage: Onboarding stage number (1-4)
            
        Returns:
            Audio instruction text
        """
        audio_key = f'audio_stage_{stage}'
        return self.get_localized_content(language_code, audio_key)
    
    def translate_form_labels(self, language_code: str, form_data: dict) -> dict:
        """
        Translate form labels to specified language
        
        Args:
            language_code: Target language code
            form_data: Dictionary of form field names and values
            
        Returns:
            Dictionary with translated labels
        """
        translated = {}
        
        for field_name, value in form_data.items():
            # Get translated label
            translated_label = self.get_localized_content(language_code, field_name)
            translated[field_name] = {
                'label': translated_label,
                'value': value
            }
        
        return translated
    
    def get_validation_message(self, language_code: str, validation_type: str, **kwargs) -> str:
        """
        Get localized validation message
        
        Args:
            language_code: Language code
            validation_type: Type of validation error
            **kwargs: Format parameters
            
        Returns:
            Localized validation message
        """
        return self.get_localized_content(language_code, validation_type, **kwargs)
    
    def get_stage_content(self, language_code: str, stage: int) -> dict:
        """
        Get all content for a specific onboarding stage
        
        Args:
            language_code: Language code
            stage: Stage number (1-4)
            
        Returns:
            Dictionary with stage title, subtitle, and audio instructions
        """
        return {
            'title': self.get_localized_content(language_code, f'stage_{stage}_title'),
            'subtitle': self.get_localized_content(language_code, f'stage_{stage}_subtitle'),
            'audio': self.get_audio_instructions(language_code, stage)
        }


# Global language engine instance
language_engine = LanguageEngine()


def get_user_language(user_id: int) -> str:
    """Helper function to get user's language preference"""
    return language_engine.get_user_language_preference(user_id)


def localize(user_id: int, content_key: str, **kwargs) -> str:
    """Helper function to get localized content for a user"""
    language = get_user_language(user_id)
    return language_engine.get_localized_content(language, content_key, **kwargs)


def set_language(user_id: int, language: str) -> bool:
    """Helper function to set user's language preference"""
    return language_engine.set_user_language_preference(user_id, language)