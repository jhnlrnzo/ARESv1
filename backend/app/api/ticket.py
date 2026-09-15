from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone

from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketUpdate,
    TicketCancel
)
from app.models.ticket import Ticket
from app.db.dependencies import get_db
from app.services.audit_service import create_audit_log 

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

@router.post("/")
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    new_ticket = Ticket(
        caller_name=ticket.caller_name,
        caller_phone=ticket.caller_phone,
        incident_type=ticket.incident_type,
        status="PENDING",
        latitude=ticket.latitude,
        longitude=ticket.longitude,
        notes=ticket.notes
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return {
        "message": "Ticket created successfully",
        "ticket": new_ticket
    }

@router.get("/", response_model=list[TicketResponse])
def get_tickets(db: Session = Depends(get_db)):
    
    tickets = db.execute(select(Ticket)).scalars().all()
    return tickets

@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.scalars(
    select(Ticket).where(Ticket.id == ticket_id)).first()
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    return {
        "ticket": ticket
    }

@router.patch("/{ticket_id}")
def update_ticket(ticket_id: str, ticket_data: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.scalars(select(Ticket).where(Ticket.id == ticket_id)).first()
    
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    update_data = ticket_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.patch("/{ticket_id}/cancel")
def cancel_ticket(
    ticket_id: str,
    cancel_data: TicketCancel,
    db: Session = Depends(get_db)
):
    ticket = db.scalars(select(Ticket).where(Ticket.id == ticket_id)).first()
    
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    
    if ticket.status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Ticket is already cancelled"
        )

    old_status = ticket.status

    ticket.status = "CANCELLED"
    ticket.cancelled_at = datetime.now(timezone.utc)
    ticket.cancellation_reason = cancel_data.reason

    create_audit_log(
        db=db,
        entity_type="TICKET",
        entity_id=ticket.id,
        action="STATUS_CHANGED",
        old_value=old_status,
        new_value="CANCELLED",
        performed_by=None
    )

    db.commit()
    db.refresh(ticket)

    return ticket

@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    db.delete(ticket)
    db.commit()
    return {
        "message": "Ticket deleted successfully",
        "ticket": {
            "id": ticket_id
        }
    }