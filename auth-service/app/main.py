import os
import datetime
import hashlib
import bcrypt
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.future import select
from passlib.context import CryptContext
from jose import jwt
import enum  # El enum nativo de Python
from sqlalchemy import Enum as SQLEnum  # El tipo Enum de SQLAlchemy

# ==========================================
# 1. CONFIGURACIÓN CENTRALIZADA
# ==========================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ticket_user:ticket_password@postgres-db:5432/ticketflow_db",
)
SECRET_KEY = os.getenv(
    "SECRET_KEY", "super-secret-key-change-in-production-1234567890!"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto criptográfico estándar de Passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==========================================
# 2. IMPLEMENTACIÓN REESCRITA CON BCRYPT NATIVO (SIN PASSLIB)
# ==========================================
def get_password_hash(password: str) -> str:
    """
    Genera un hash seguro utilizando la librería nativa bcrypt.
    Para evitar el límite de 72 bytes por diseño de bcrypt, primero aplicamos SHA-256.
    """
    # 1. Pre-hash a SHA-256 para normalizar a una longitud fija de 32 bytes
    pre_hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # 2. Generar el Salt y aplicar Bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed.encode("utf-8"), salt)

    # Decodificamos a string para poder almacenarlo limpiamente en la base de datos de texto
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


# ==========================================
# 3. MODELOS DE BASE DE DATOS (SQLAlchemy)
# ==========================================
class Base(DeclarativeBase):
    pass


# Declaramos las opciones idénticas a las que espera el tipo 'userrole' de la BD
class UserRole(str, enum.Enum):
    CUSTOMER = "Customer"
    ORGANIZER = "Organizer"
    ADMIN = "Admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)

    # Configuramos la columna para que use el Enum de SQLAlchemy mapeado al tipo nativo de Postgres
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="userrole", native_enum=True),
        default=UserRole.CUSTOMER,
        nullable=False,
    )


# Inicialización asíncrona del motor de la BD
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ==========================================
# 4. ESQUEMAS DE VALIDACIÓN (Pydantic v2)
# ==========================================
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "Customer"


class Token(BaseModel):
    access_token: str
    token_type: str


# ==========================================
# 5. INICIALIZACIÓN DE LA API FASTAPI
# ==========================================
app = FastAPI(title="TicketFlow Auth Service", version="1.0.0")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Autogeneración segura de la tabla de usuarios si no existe
        await conn.run_sync(Base.metadata.create_all)


# ==========================================
# 6. ENDPOINTS CORREGIDOS Y SEGUROS
# ==========================================


@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=400, detail="El correo ya se encuentra registrado."
        )

    secure_hash = get_password_hash(user_data.password)

    # Convertimos el string enviado por el cliente (ej. "Customer") al valor del Enum válido
    try:
        db_role = UserRole(user_data.role)
    except ValueError:
        db_role = UserRole.CUSTOMER  # Respaldo por si mandan un string inválido

    new_user = User(
        email=user_data.email,
        hashed_password=secure_hash,
        role=db_role,  # ⬅️ Asignamos el objeto Enum mapeado
    )
    db.add(new_user)
    await db.commit()
    return {"message": "Usuario registrado exitosamente."}


@app.post("/api/v1/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    # Buscar al usuario por correo
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()

    # Validar existencia y contrastar contraseña usando el verificador protegido
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso incorrectas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar el Token JWT firmado
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.datetime.utcnow() + access_token_expires

    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": encoded_jwt, "token_type": "bearer"}
