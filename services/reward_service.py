from core.extensions import db
from models.rewards import RewardLedger


def award_reward(user_id, reward_type, coins=0, points=0, description=""):
    """Award coins and points to a user"""
    from models.user import User
    
    user = User.query.get(user_id)
    if not user:
        return False
    
    # Check if reward already exists for this action
    existing = RewardLedger.query.filter_by(
        user_id=user_id,
        action=reward_type
    ).first()

    if existing:
        return False

    # Create reward record
    reward = RewardLedger(
        user_id=user_id,
        action=reward_type,
        points_awarded=points,
        coins_awarded=coins
    )

    # Update user totals
    if not user.points:
        user.points = 0
    if not user.coins:
        user.coins = 0
        
    user.points += points
    user.coins += coins

    db.session.add(reward)
    db.session.commit()
    return True
