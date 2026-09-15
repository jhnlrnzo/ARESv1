from app.db.base import Base
from app.db.session import engine

from app.models import ticket
from app.models import rescue_team
from app.models import audit_log
from app.models import vehicle
from app.models import missions

def init_db():
    Base.metadata.create_all(bind=engine)