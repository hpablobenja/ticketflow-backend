# TicketFlow 🎫 - Plataforma Distribuida de Compra de Entradas

TicketFlow es una solución de backend diseñada bajo una **arquitectura orientada a microservicios** de alta disponibilidad para mitigar los problemas clásicos de alta concurrencia, reventa masiva (bots) y consistencia de datos durante la venta de entradas para eventos masivos.

El ecosistema aprovecha el rendimiento de **FastAPI**, la robustez transaccional de **PostgreSQL**, bloqueos en memoria optimizados con **Redis**, y un desacoplamiento asíncrono mediante el patrón **Pub/Sub** para el procesamiento de pagos y notificaciones.

---

## 🏗️ Arquitectura del Sistema

El sistema se compone de los siguientes elementos que interactúan de forma aislada y escalable:

```text
[ Cliente (Postman/Web) ]
           │
           ├──► [ auth-service:8000 ] ──► (PostgreSQL: userrole Enum)
           │
           └──► [ booking-service:8001 ] 
                     │
                     ├──► (PostgreSQL: Eventos y Transacciones)
                     ├──► (Redis: Rate Limiting & TTL Candados de 10 min)
                     │
                     └──► [ Redis Pub/Sub Channel ]
                                │
                                └──► [ ticketflow_notifications ] (Worker Asíncrono)
                                          │
                                          └──► Generación de QR & PDF / Email

```

### Componentes Clave:

1. **`auth-service` (Puerto 8000):** Se encarga del registro, hashing seguro de contraseñas mediante `bcrypt` nativo y la emisión de credenciales criptográficas basadas en **JWT (OAuth2)**. Maneja roles estrictos (`Customer`, `Organizer`, `Admin`) mapeados directamente a enums nativos de PostgreSQL (`userrole`).
2. **`booking-service` (Puerto 8001):** El núcleo transaccional. Permite consultar eventos y gestionar el flujo de reservas y checkout de boletos.
3. **`ticketflow_notifications` (Worker):** Servicio en segundo plano desacoplado. Escucha eventos de pago confirmados para realizar tareas pesadas (renderizado de PDFs, inyección de códigos QR y simulación de envío de correos) sin bloquear el hilo principal de la experiencia del usuario.
4. **Capa de Datos y Caching:**
* **PostgreSQL:** Fuente de verdad para datos relacionales estrictos.
* **Redis:** Actúa como caché de alto rendimiento, manejador de *Rate Limiting* por IP/Usuario, y almacén de llaves temporales (TTL) para expirar reservas no pagadas a los 10 minutos.



---

## 🛠️ Tecnologías y Herramientas

* **Lenguaje:** Python 3.11+
* **Framework:** FastAPI (Uvicorn / ASGI)
* **ORM & Driver:** SQLAlchemy 2.0 (Asyncio) + `asyncpg`
* **Base de Datos:** PostgreSQL 15+ & Redis 7+
* **Seguridad:** JWT, PyJWT, Bcrypt nativo
* **Validación:** Pydantic v2
* **Despliegue:** Docker & Docker Compose

---

## 🚀 Requisitos Previos e Instalación

Asegúrate de tener instalados **Docker** y **Docker Compose** en tu máquina de desarrollo.

1. Clona este repositorio:
```bash
git clone https://github.com/hpablobenja/ticketflow-backend.git
cd ticketflow-backend

```


2. Construye y levanta el entorno completo en un solo comando:
```bash
docker-compose up --build

```


*Esto descargará las imágenes correspondientes, creará la red interna, inicializará PostgreSQL/Redis y encenderá los microservicios de manera coordinada.*

---

## 🚦 Guía de Pruebas de Extremo a Extremo (E2E)

Sigue estos pasos en **Postman** o la interfaz integrada de Swagger para verificar el flujo transaccional distribuido:

### Paso 1: Autenticación (`auth-service`)

* **Registro de Usuario:** Envía una petición `POST` a `http://localhost:8000/api/v1/auth/register` con el rol deseado (`Customer`, `Organizer` o `Admin`).
* **Obtención del Token:** Envía las credenciales vía formulario `POST` a `http://localhost:8000/api/v1/auth/token` para recibir tu `access_token` JWT.

### Paso 2: Preparar el Evento

Si la base de datos se encuentra vacía, inyecta un evento de prueba directamente ejecutando en tu terminal:

```bash
docker exec -it postgres-db psql -U ticket_user -d ticketflow_db -c "INSERT INTO events (title, date, total_tickets, tickets_left) VALUES ('Gran Concierto TicketFlow 2026', '2026-12-31 20:00:00', 100, 100);"

```

### Paso 3: Bloqueo de Entrada de Alta Concurrencia (`booking-service`)

* Envía un `POST` a `http://localhost:8001/api/v1/events/1/reserve?user_id=1`.
* **Comportamiento esperado:** Redis registrará un candado temporal por 10 minutos. Si intentas mandar la misma petición de inmediato, el sistema bloqueará el intento para evitar el acaparamiento o duplicidad de compras concurrentes.

### Paso 4: Desacoplamiento de Checkout

* Procesa el pago simulado enviando un `POST` a `http://localhost:8001/api/v1/booking/checkout/1` (cambia el `1` por el `ticket_id` obtenido).
* **Comportamiento esperado:** La API responderá de inmediato con un código `200 OK`. Paralelamente, en los logs de Docker verás cómo el contenedor `ticketflow_notifications` reacciona instantáneamente al evento asíncrono imprimiendo la generación del código QR y PDF.

### Paso 5: Protección contra Bots (Rate Limiter)

* Haz solicitudes repetidas y muy rápidas (más de 5 por segundo) a cualquier endpoint de consulta como `GET http://localhost:8001/api/v1/events`.
* **Comportamiento esperado:** La API mitigará el comportamiento devolviendo un estado HTTP **`429 Too Many Requests`**.

---

## 🔒 Buenas Prácticas de Ingeniería Aplicadas

* **Manejo Estricto de Tipos en DB:** Solución de colisiones de tipos complejos mediante el mapeo explícito de tipos enumerados (`SQLEnum`) en SQLAlchemy sincronizados con PostgreSQL.
* **Seguridad Criptográfica:** Migración del ecosistema hacia librerías de `bcrypt` nativas compiladas en C en entornos Linux/Docker, evitando errores de tipado en payloads de strings/bytes.
* **Manejo de Errores Semántico:** Respuestas claras basadas en los estándares de FastAPI y validaciones nativas en Query Params con Pydantic.
* **Arquitectura de Alta Disponibilidad:** Separación estricta de responsabilidades donde las tareas de E/S intensivas (I/O Bound) se delegan a workers asíncronos para mantener una API con latencias mínimas.