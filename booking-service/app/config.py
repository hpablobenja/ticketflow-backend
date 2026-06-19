import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TicketFlow Booking Service"

    # 1. Traemos las variables individuales que configuraste en tu archivo .env de la EC2
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "ticket_password")
    DB_HOST: str = os.getenv("DB_HOST", "postgres-db")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "ticketflow_db")

    # 2. Construimos el string de conexión asíncrono para PostgreSQL automáticamente
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Cambiamos también 'localhost' por 'redis-cache' para evitar el mismo error con Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis-cache:6379")

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "super-secret-key-change-in-production-1234567890!"
    )
    ALGORITHM: str = "HS256"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
