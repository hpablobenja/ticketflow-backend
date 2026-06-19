from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.models import UserRole

# ESQUEMAS DE VALIDACIÓN (Pydantic v2)

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.CUSTOMER


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: UserRole

    class Config:
        from_attributes = True