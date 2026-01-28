import re


def is_valid_indian_phone(phone: str) -> bool:
    if not phone:
        return False
    return bool(re.fullmatch(r"[6-9]\d{9}", phone.strip()))
