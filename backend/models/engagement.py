"""
EngagementStat model
Per-child record of how engaging each kind of reply choice has been
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from database.database import Base


class EngagementStat(Base):
    """
    EngagementStat model - accumulated engagement scores for one reply choice

    A reply choice is a (feature, arm) pair, for example ("follow_up", "yes"),
    ("humor", "pun") or ("template:like_thing", "<template id>"). Each time a reply
    with that choice gets a response from the child, the response's engagement
    score (0.0-1.0) is added to score_sum and count is incremented.

    Relationships:
        - Many-to-one with User
    """

    __tablename__ = "engagement_stats"
    __table_args__ = (UniqueConstraint("user_id", "feature", "arm", name="uq_engagement_choice"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    feature = Column(String, nullable=False)
    arm = Column(String, nullable=False)
    score_sum = Column(Float, default=0.0, nullable=False)
    count = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    user = relationship("User", back_populates="engagement_stats")

    def __init__(self, **kwargs):
        # Column defaults only apply on INSERT; set them so new rows can be updated before flushing
        kwargs.setdefault("score_sum", 0.0)
        kwargs.setdefault("count", 0)
        super().__init__(**kwargs)

    @property
    def mean(self) -> float:
        return self.score_sum / self.count if self.count else 0.0

    def to_dict(self):
        return {
            "feature": self.feature,
            "arm": self.arm,
            "count": self.count,
            "mean_score": round(self.mean, 3),
        }

    def __repr__(self):
        return f"<EngagementStat(user_id={self.user_id}, {self.feature}={self.arm}, n={self.count}, mean={self.mean:.2f})>"
