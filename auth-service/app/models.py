from sqlalchemy import Column, Integer, String, Enum
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    ORGANIZER = "Organizer"
    CUSTOMER = "Customer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
