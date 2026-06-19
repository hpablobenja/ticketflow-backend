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


# Esquema simple para crear eventos desde Postman con payload reducido
class SimpleEventCreate(BaseModel):
    id: Optional[int] = None
    title: str = Field(
        ..., min_length=1, max_length=200, example="Pequeño TicketFlow 2026"
    )
    tickets_left: int = Field(..., ge=0, example=100)


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    date: Optional[datetime] = None
    total_tickets: Optional[int] = Field(None, gt=0)
    tickets_left: Optional[int] = Field(None, ge=0)


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


class TicketUpdate(BaseModel):
    status: Optional[str] = Field(
        None, description="Estado del ticket: reserved, confirmed, cancelled"
    )


class ReservationRequest(BaseModel):
    user_id: int  # En producción se extraerá automáticamente del JWT decodificado


class ReservationResponse(BaseModel):
    message: str
    ticket_id: int
