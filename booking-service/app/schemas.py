from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


# Esquemas para la gestión de Eventos
class EventBase(BaseModel):
    title: str = Field(
        ..., min_length=3, max_length=100, description="Título del evento masivo"
    )
    date: datetime = Field(..., description="Fecha y hora del evento")
    total_tickets: int = Field(
        ..., gt=0, description="Capacidad total de entradas del recinto"
    )


class EventCreate(EventBase):
    pass


class EventResponse(BaseModel):
    id: int
    title: str
    date: datetime
    total_tickets: int
    tickets_left: int

    class Config:
        from_attributes = True


# Esquemas para la gestión de Tickets / Reservas
class TicketResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReservationRequest(BaseModel):
    user_id: int  # En producción se extraerá automáticamente del JWT decodificado


class ReservationResponse(BaseModel):
    message: str
    ticket_id: int
