from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import redis.asyncio as aioredis

from app.models import Base, Event, Ticket
from app.redis_client import get_redis

from app.config import settings
from app.database import engine, get_db
from app.models import Base, Event, Ticket
from app.redis_client import get_redis
from app.schemas import EventCreate, EventResponse, ReservationResponse

import json
from fastapi import status

import time
from fastapi import Request

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Crea las tablas correspondientes a Eventos y Tickets si no existen en la BD
        await conn.run_sync(Base.metadata.create_all)

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

# Middleware para Rate Limiting Avanzado por IP usando Redis
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 1. Registramos el tiempo exacto antes de que empiece la petición
    start_time = time.perf_counter()
    
    # 2. Procesamos la petición (va al endpoint, base de datos, Redis, etc.)
    response = call_next(request)
    
    # Si la respuesta es una corrutina (como en endpoints asíncronos), esperamos su resolución
    if hasattr(response, "__await__"):
        response = await response
        
    # 3. Calculamos la diferencia de tiempo
    process_time = time.perf_counter() - start_time
    
    # 4. Inyectamos la latencia en milisegundos en los headers de respuesta para análisis
    response.headers["X-Process-Time-Ms"] = f"{process_time * 1000:.2f}"
    
    return response

async def rate_limiter_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    redis: aioredis.Redis = await get_redis()
    
    # Llave identificadora por cliente
    key = f"rate_limit:{client_ip}"
    current_requests = await redis.get(key)
    
    if current_requests and int(current_requests) >= 5:
        # Se bloquea si supera las 5 peticiones por segundo
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Límite excedido.")
        
    async with redis.pipeline(transaction=True) as pipe:
        await pipe.incr(key)
        await pipe.expire(key, 1) # Reseteo cada segundo
        await pipe.execute()
        
    return await call_next(request)

# GET /events con Paginación y Caching de Alto Rendimiento
@app.get("/api/v1/events")
async def list_events(limit: int = 10, offset: int = 0, db: AsyncSession = Depends(get_db_session)):
    redis: aioredis.Redis = await get_redis()
    cache_key = f"events:list:{limit}:{offset}"
    
    # 1. Intentar obtener datos de la caché (Latencia < 10ms)
    cached_data = await redis.get(cache_key)
    if cached_data:
        import json
        return json.loads(cached_data)
        
    # 2. Si no está en caché, consultar Base de Datos mitigando N+1 con selectinload
    result = await db.execute(
        select(Event).options(selectinload(Event.tickets)).offset(offset).limit(limit)
    )
    events = result.scalars().all()
    
    # Transformar a formato JSON serializable
    response_payload = [
        {"id": e.id, "title": e.title, "tickets_left": e.tickets_left} for e in events
    ]
    
    # 3. Almacenar en caché por 60 segundos
    import json
    await redis.setex(cache_key, 60, json.dumps(response_payload))
    return response_payload

# POST /reserve implementando expiración atómica (TTL)
@app.post("/api/v1/events/{event_id}/reserve", status_code=201)
async def reserve_ticket(event_id: int, user_id: int, db: AsyncSession = Depends(get_db_session)):
    redis: aioredis.Redis = await get_redis()
    
    # Verificar disponibilidad en la base de datos transaccional
    result = await db.execute(select(Event).filter(Event.id == event_id))
    event = result.scalars().first()
    
    if not event or event.tickets_left <= 0:
        raise HTTPException(status_code=400, detail="No hay boletos disponibles para este evento.")
        
    # Bloqueo Temporal en Redis: Evita condiciones de carrera asumiendo control atómico por 10 minutos
    reserve_key = f"ticket:reserve:{event_id}:{user_id}"
    already_reserved = await redis.get(reserve_key)
    
    if already_reserved:
        raise HTTPException(status_code=400, detail="Ya cuentas con una reserva activa en progreso.")
        
    # Restar stock transaccional
    event.tickets_left -= 1
    new_ticket = Ticket(event_id=event_id, user_id=user_id, status="reserved")
    db.add(new_ticket)
    
    await db.commit()
    
    # Registramos en Redis el TTL de expiración automática de 10 minutos (600 segundos)
    await redis.setex(reserve_key, 600, "pending_payment")
    
    return {"message": "Reserva exitosa. Cuenta con 10 minutos para concretar su pago.", "ticket_id": new_ticket.id}

# Endpoint para simular la confirmación de pago y disparar el evento asíncrono
@app.post("/api/v1/booking/checkout/{ticket_id}", status_code=status.HTTP_200_OK)
async def checkout_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    # 1. Buscar el ticket reservado
    result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
    ticket = result.scalars().first()
    
    if not ticket or ticket.status != "reserved":
        raise HTTPException(status_code=404, detail="Ticket no encontrado o no está reservado.")
        
    # 2. Transaccionalidad: Cambiar estado a confirmado
    ticket.status = "confirmed"
    await db.commit()
    
    # 3. Desacoplamiento Senior: Publicar el evento en Redis Pub/Sub
    redis = await get_redis()
    event_payload = {
        "ticket_id": ticket.id,
        "event_id": ticket.event_id,
        "user_id": ticket.user_id,
        "status": ticket.status,
        "email": f"user_{ticket.user_id}@ticketflow.com"  # Simulación de correo asociado
    }
    
    # Publicamos el mensaje en el canal 'ticket_orders'
    await redis.publish("ticket_orders", json.dumps(event_payload))
    
    return {"message": "Pago procesado exitosamente. Su entrada está en camino.", "ticket_id": ticket.id}