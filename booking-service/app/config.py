import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TicketFlow Booking Service"
    # Cambiamos 'localhost' por 'postgres-db' que es el nombre asignado en docker-compose
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://ticket_user:ticket_password@postgres-db:5432/ticketflow_db"
    )
    # Cambiamos también 'localhost' por 'redis-cache' para evitar el mismo error con Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis-cache:6379")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-1234567890!")
    ALGORITHM: str = "HS256"

settings = Settings()