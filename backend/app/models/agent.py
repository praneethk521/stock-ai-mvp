from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AgentToolAuditLog(Base):
    __tablename__ = 'agent_tool_audit_logs'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tool_name: Mapped[str] = mapped_column(String(120), index=True)
    audit_event: Mapped[str] = mapped_column(String(160), index=True)
    ok: Mapped[bool] = mapped_column(Boolean)
    input_payload: Mapped[dict] = mapped_column(JSON)
    output_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
