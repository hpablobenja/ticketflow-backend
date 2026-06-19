import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt
from app.models import Base, User, UserRole
from app.schemas import UserRegister, UserUpdate, UserResponse, Token
from app.security import get_password_hash, verify_password
from app.database import get_db, engine
from app.config import settings
from typing import List

# INICIALIZACIÓN DE LA API FASTAPI

app = FastAPI(title="TicketFlow Auth Service", version="1.0.0")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Autogeneración segura de la tabla de usuarios si no existe
        await conn.run_sync(Base.metadata.create_all)


# 6. ENDPOINTS CORREGIDOS Y SEGUROS


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
        print("Role recibido:", user_data.role)
        db_role = UserRole(user_data.role)
    except ValueError:
        db_role = UserRole.CUSTOMER

    new_user = User(
        email=user_data.email,
        hashed_password=secure_hash,
        role=db_role,
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
    access_token_expires = datetime.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = datetime.datetime.utcnow() + access_token_expires

    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role.value,
    }


@app.get("/api/v1/users", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return user


@app.put("/api/v1/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if user_update.email:
        user.email = user_update.email

    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)

    if user_update.role:
        try:
            user.role = UserRole(user_update.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Rol de usuario inválido.")

    await db.commit()
    await db.refresh(user)
    return user


@app.delete("/api/v1/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    await db.delete(user)
    await db.commit()
    return None
