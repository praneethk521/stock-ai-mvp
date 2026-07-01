from datetime import datetime
from sqlalchemy import DateTime, Float, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class RecommendationRecord(Base):
    __tablename__ = 'recommendations'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(12), index=True)
    recommendation: Mapped[str] = mapped_column(String(16))
    trade_horizon: Mapped[str] = mapped_column(String(16))
    confidence_score: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(String(2000))
    supporting_signals: Mapped[dict] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(32), default='rules-v1')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
