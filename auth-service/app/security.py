import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.config import settings
import bcrypt

# IMPLEMENTACIÓN REESCRITA CON BCRYPT NATIVO (SIN PASSLIB)

# Contexto criptográfico estándar de Passlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Genera un hash seguro utilizando la librería nativa bcrypt.
    Para evitar el límite de 72 bytes por diseño de bcrypt, primero aplicamos SHA-256.
    """
    # Pre-hash a SHA-256 para normalizar a una longitud fija de 32 bytes
    pre_hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # Generar el Salt y aplicar Bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed.encode("utf-8"), salt)

    # Decodificamos a string para poder almacenarlo
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica de forma segura si la contraseña coincide usando bcrypt nativo.
    """
    try:
        pre_hashed = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        # Contrasta los bytes de la contraseña ingresada contra los bytes almacenados
        return bcrypt.checkpw(
            pre_hashed.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Asignación de scopes granulares dependiendo del rol del usuario
    role = data.get("role")
    scopes = ["tickets:read"]
    if role == "Customer":
        scopes.append("tickets:buy")
    elif role in ["Organizer", "Admin"]:
        scopes.extend(["tickets:buy", "events:create", "events:delete"])

    to_encode.update({"exp": expire, "scopes": scopes})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
