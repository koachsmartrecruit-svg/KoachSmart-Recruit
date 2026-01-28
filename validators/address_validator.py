import re


def is_valid_pincode(pincode: str) -> bool:
    if not pincode:
        return False
    return bool(re.fullmatch(r"\d{6}", pincode.strip()))
