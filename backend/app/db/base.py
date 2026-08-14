from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from app.models.ticket import Ticket
from app.models.audit_log import AuditLog