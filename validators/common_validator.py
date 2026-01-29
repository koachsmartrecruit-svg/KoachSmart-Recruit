import re


def is_non_empty(value) -> bool:
    return bool(value and str(value).strip())


def is_positive_number(value) -> bool:
    try:
        return float(value) > 0
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """Validate email address format"""
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))
