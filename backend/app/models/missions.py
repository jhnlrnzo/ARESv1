from uuid import uuid4

from sqlalchemy import String, DateTime, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base

class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    ticket_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tickets.id"),
        nullable=False
    )

    team_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("rescue_teams.id"),
        nullable=False
    )

    vehicle_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("vehicles.id"),
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="LOW"
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="ASSIGNED"
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    personnel_required: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    medical_personnel: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    vehicle_required: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    en_route_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    arrived_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    cancelled_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )