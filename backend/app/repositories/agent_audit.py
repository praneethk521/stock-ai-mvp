from sqlalchemy.orm import Session

from app.agents.contracts import get_tool_contract
from app.models.agent import AgentToolAuditLog


def create_agent_tool_audit_log(
    db: Session,
    tool_name: str,
    input_payload: dict,
    ok: bool,
    output_summary: dict | None = None,
    error: dict | None = None,
    duration_ms: int = 0,
) -> AgentToolAuditLog:
    contract = get_tool_contract(tool_name)
    record = AgentToolAuditLog(
        tool_name=tool_name,
        audit_event=contract.audit_event if contract else f'agent.tool.{tool_name}',
        ok=ok,
        input_payload=input_payload,
        output_summary=output_summary,
        error=error,
        duration_ms=duration_ms,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_agent_tool_audit_logs(
    db: Session,
    tool_name: str | None = None,
    limit: int = 20,
) -> list[AgentToolAuditLog]:
    query = db.query(AgentToolAuditLog)
    if tool_name:
        query = query.filter(AgentToolAuditLog.tool_name == tool_name)
    return query.order_by(AgentToolAuditLog.id.desc()).limit(limit).all()


def count_agent_tool_audit_logs(db: Session) -> int:
    return db.query(AgentToolAuditLog).count()
