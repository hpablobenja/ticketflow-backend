from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.future import select
import enum
from app.database import Base
from sqlalchemy import Enum as SQLEnum  # El tipo Enum de SQLAlchemy

# MODELOS DE BASE DE DATOS (SQLAlchemy)

class Base(DeclarativeBase):
    pass

# Declaramos las opciones
class UserRole(str, enum.Enum):
    CUSTOMER = "Customer"
    ORGANIZER = "Organizer"
    ADMIN = "Admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)

    # Configuramos la columna para que use el Enum de SQLAlchemy
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="userrole", native_enum=True),
        default=UserRole.CUSTOMER,
        nullable=False,
    )