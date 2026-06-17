import os
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    PROJECT_NAME: str = "TicketFlow Auth Service"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://ticket_user:ticket_password@localhost:5432/ticketflow_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-1234567890!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()