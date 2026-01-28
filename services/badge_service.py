from core.extensions import db
from models.user import User


def assign_badge(user_id, badge_field):
    """
    Sets a boolean badge flag on User model.
    Example:
        assign_badge(1, "phone_verified")
    """

    user = User.query.get(user_id)

    if not user:
        return False

    if not hasattr(user, badge_field):
        return False

    setattr(user, badge_field, True)
    db.session.commit()
    return True
