import re


def is_valid_indian_phone(phone: str) -> bool:
    if not phone:
        return False
    return bool(re.fullmatch(r"[6-9]\d{9}", phone.strip()))


def is_valid_phone(phone: str) -> bool:
    """Validate phone number (supports Indian and international formats)"""
    if not phone:
        return False
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone.strip())
    
    # Indian phone number patterns
    indian_patterns = [
        r'^[6-9]\d{9}$',           # 10 digits starting with 6-9
        r'^\+91[6-9]\d{9}$',       # +91 followed by 10 digits
        r'^91[6-9]\d{9}$',         # 91 followed by 10 digits
    ]
    
    # Check Indian patterns
    for pattern in indian_patterns:
        if re.match(pattern, cleaned):
            return True
    
    # International format (basic validation)
    if re.match(r'^\+\d{10,15}$', cleaned):
        return True
    
    return False
