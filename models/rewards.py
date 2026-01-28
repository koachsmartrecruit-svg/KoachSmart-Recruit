from datetime import datetime
from core.extensions import db


class RewardLedger(db.Model):
    __tablename__ = "reward_ledger"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(100), nullable=False)

    points_awarded = db.Column(db.Integer, default=0)
    coins_awarded = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "action", name="unique_user_action_reward"),
    )
