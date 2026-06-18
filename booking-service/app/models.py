from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    total_tickets = Column(Integer, nullable=False)
    tickets_left = Column(Integer, nullable=False)

    tickets = relationship("Ticket", back_populates="event")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, nullable=False)  # Proveniente del token de auth-service
    status = Column(String, default="reserved")  # reserved, confirmed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="tickets")
