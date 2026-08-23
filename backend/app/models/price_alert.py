from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Index, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PriceAlert(Base):
    __tablename__ = 'price_alerts'
    __table_args__ = (
        CheckConstraint("condition IN ('above', 'below')", name='ck_price_alerts_condition'),
        CheckConstraint('target_price > 0 AND target_price <= 1000000000', name='ck_price_alerts_target_price'),
        Index('ix_price_alerts_user_active', 'user_id', 'is_active'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    ticker: Mapped[str] = mapped_column(String(12), index=True)
    condition: Mapped[str] = mapped_column(String(8))
    target_price: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
