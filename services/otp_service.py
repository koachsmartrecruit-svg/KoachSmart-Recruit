import random
import time

# In-memory OTP store (replace with Redis later)
_otp_store = {}


def generate_otp():
    return str(random.randint(100000, 999999))


def save_otp(key, otp, ttl_seconds=300):
    _otp_store[key] = {
        "otp": otp,
        "expires_at": time.time() + ttl_seconds
    }


def verify_otp(key, user_otp):
    record = _otp_store.get(key)

    if not record:
        return False

    if time.time() > record["expires_at"]:
        _otp_store.pop(key, None)
        return False

    if record["otp"] != user_otp:
        return False

    _otp_store.pop(key, None)
    return True
