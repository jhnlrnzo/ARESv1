from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from app.models.ticket import Ticket
from app.models.rescue_team import RescueTeam
from app.models.audit_log import AuditLog
from app.models.vehicle import Vehicle
from app.models.missions import Mission
