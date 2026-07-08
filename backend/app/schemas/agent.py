from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AgentToolAuditItem(BaseModel):
    id: int
    tool_name: str
    audit_event: str
    ok: bool
    input_payload: dict[str, Any]
    output_summary: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    duration_ms: int
    created_at: datetime
