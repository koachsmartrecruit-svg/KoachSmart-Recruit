from core.extensions import db
from models.rewards import RewardLedger


def award_reward(user, action, points=0, coins=0):
    existing = RewardLedger.query.filter_by(
        user_id=user.id,
        action=action
    ).first()

    if existing:
        return False

    reward = RewardLedger(
        user_id=user.id,
        action=action,
        points_awarded=points,
        coins_awarded=coins
    )

    user.points += points
    user.coins += coins

    db.session.add(reward)
    db.session.commit()
    return True
