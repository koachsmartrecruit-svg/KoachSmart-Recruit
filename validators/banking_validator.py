import re


def is_valid_pan(pan: str) -> bool:
    if not pan:
        return False
    return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan.strip()))


def is_valid_ifsc(ifsc: str) -> bool:
    if not ifsc:
        return False
    return bool(re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", ifsc.strip()))
