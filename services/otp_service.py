import random
import time
from flask import current_app
from services.email_service import send_otp_email

# In-memory OTP store (replace with Redis later)
_otp_store = {}


def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def generate_demo_mobile_otp():
    """Generate demo OTP for mobile (always 123456 for demo)"""
    return "123456"


def save_otp(key, otp, ttl_seconds=300):
    """Save OTP with expiration time"""
    _otp_store[key] = {
        "otp": otp,
        "expires_at": time.time() + ttl_seconds,
        "attempts": 0
    }
    current_app.logger.info(f"OTP saved for {key}: {otp} (expires in {ttl_seconds}s)")


def verify_otp(key, user_otp):
    """Verify OTP with attempt limiting"""
    record = _otp_store.get(key)

    if not record:
        current_app.logger.warning(f"OTP verification failed for {key}: No OTP found")
        return False

    # Check expiration
    if time.time() > record["expires_at"]:
        _otp_store.pop(key, None)
        current_app.logger.warning(f"OTP verification failed for {key}: OTP expired")
        return False

    # Increment attempts
    record["attempts"] += 1

    # Check attempt limit (max 3 attempts)
    if record["attempts"] > 3:
        _otp_store.pop(key, None)
        current_app.logger.warning(f"OTP verification failed for {key}: Too many attempts")
        return False

    # Verify OTP
    if record["otp"] != user_otp:
        current_app.logger.warning(f"OTP verification failed for {key}: Invalid OTP")
        return False

    # Success - remove OTP
    _otp_store.pop(key, None)
    current_app.logger.info(f"OTP verification successful for {key}")
    return True


def send_mobile_otp(phone_number):
    """
    Send OTP to mobile number
    For demo purposes, always use 123456
    In production, integrate with SMS service like Twilio, MSG91, etc.
    """
    try:
        # For demo - always use 123456
        demo_otp = generate_demo_mobile_otp()
        save_otp(phone_number, demo_otp)
        
        current_app.logger.info(f"Demo mobile OTP sent to {phone_number}: {demo_otp}")
        
        # In production, replace this with actual SMS service
        # Example with Twilio:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     body=f"Your KoachSmart verification code is: {demo_otp}",
        #     from_='+1234567890',
        #     to=phone_number
        # )
        
        return {
            'success': True,
            'message': f'Demo OTP sent to {phone_number}. Use 123456 for verification.',
            'otp': demo_otp  # Remove this in production
        }
        
    except Exception as e:
        current_app.logger.error(f"Error sending mobile OTP to {phone_number}: {str(e)}")
        return {
            'success': False,
            'message': 'Failed to send OTP. Please try again.',
            'error': str(e)
        }


def send_email_otp_service(email):
    """
    Send OTP to email address
    For demo purposes, always use 123456 (same as mobile)
    In production, integrate with email service
    """
    try:
        # For demo - always use 123456 (same as mobile for consistency)
        demo_otp = generate_demo_mobile_otp()  # This returns "123456"
        save_otp(email, demo_otp)
        
        current_app.logger.info(f"Demo email OTP sent to {email}: {demo_otp}")
        
        # In production, uncomment this to send actual emails:
        # email_sent = send_otp_email(email, demo_otp)
        # if not email_sent:
        #     current_app.logger.warning(f"Email sending failed for {email}")
        
        return {
            'success': True,
            'message': f'Demo OTP sent to {email}. Use 123456 for verification.',
            'otp': demo_otp,  # Remove this in production
            'demo_mode': True
        }
        
    except Exception as e:
        current_app.logger.error(f"Error in email OTP service for {email}: {str(e)}")
        return {
            'success': False,
            'message': 'Failed to generate OTP. Please try again.',
            'error': str(e)
        }


def get_otp_status(key):
    """Get OTP status for debugging"""
    record = _otp_store.get(key)
    if not record:
        return {'exists': False}
    
    return {
        'exists': True,
        'otp': record['otp'],
        'expires_at': record['expires_at'],
        'attempts': record['attempts'],
        'time_remaining': max(0, record['expires_at'] - time.time())
    }


def clear_otp(key):
    """Clear OTP for a specific key"""
    if key in _otp_store:
        _otp_store.pop(key)
        current_app.logger.info(f"OTP cleared for {key}")
        return True
    return False


def clear_all_otps():
    """Clear all OTPs (for testing/debugging)"""
    global _otp_store
    count = len(_otp_store)
    _otp_store.clear()
    current_app.logger.info(f"Cleared {count} OTPs")
    return count
