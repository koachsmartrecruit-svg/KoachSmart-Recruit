import secrets
from core.extensions import db
from models.user import User


def generate_referral_code():
    return secrets.token_hex(4).upper()


def apply_referral_bonus(new_user):
    """
    Apply bonus when a user registers using a referral code.
    """
    if not new_user.referred_by:
        return

    referrer = User.query.filter_by(
        referral_code=new_user.referred_by
    ).first()

    if not referrer:
        return

    referrer.coins += 50
    new_user.referral_bonus_claimed = True

    db.session.commit()


def award_referral_bonus(user_id):
    """
    Award referral bonus after onboarding completion.
    """
    user = User.query.get(user_id)

    if not user:
        return

    if user.referral_bonus_claimed:
        return

    if not user.referred_by:
        return

    referrer = User.query.filter_by(
        referral_code=user.referred_by
    ).first()

    if not referrer:
        return

    referrer.coins += 50
    user.referral_bonus_claimed = True
    db.session.commit()
