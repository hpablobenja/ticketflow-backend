import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Aplica un pre-hash SHA-256 a la contraseña antes de pasarla a Bcrypt.
    Esto resuelve de raíz el bug de passlib con las versiones nuevas de bcrypt,
    y garantiza que las contraseñas largas nunca rompan el límite de 72 bytes.
    """
    # 1. Convertimos la contraseña en un hash SHA-256 de longitud fija (32 bytes / 64 caracteres hexadecimales)
    pre_hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # 2. Le aplicamos el Bcrypt con sal (Salt) para máxima seguridad de almacenamiento
    return pwd_context.hash(pre_hashed)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica la contraseña aplicando el mismo pre-hash SHA-256.
    """
    pre_hashed = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return pwd_context.verify(pre_hashed, hashed_password)


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
