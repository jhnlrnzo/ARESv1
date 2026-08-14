from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

def create_audit_log(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    old_value: str | None = None,
    new_value: str | None = None,
    performed_by: str | None = None
):
    audit_log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        performed_by=performed_by
    )

    db.add(audit_log)

    return audit_log