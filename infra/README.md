# TicketFlow API — Arquitectura Cloud & Microservicios (Free-Tier Optimized)

Este repositorio contiene la arquitectura de infraestructura como código (IaC) utilizando **AWS CDK v2** en Python para desplegar la plataforma **TicketFlow**. El diseño ha sido optimizado estratégicamente para operar al **100% dentro de la Capa Gratuita (Free Tier)** de AWS durante 12 meses, eliminando costos fijos de red, contenedores serverless o balanceadores de carga administrados, garantizando la persistencia e independencia de tus servicios.

---

## 🗺️ Arquitectura del Sistema

La infraestructura en la nube centraliza la computación en una única máquina virtual, aislando la capa de datos relacional y manteniendo una huella de memoria optimizada para ejecutar tus tres microservicios en paralelo.

```
                      [ Internet / Postman ]
                                │
                                ▼ (Puertos: 8000, 8001)
              ┌────────────────────────────────────────┐
              │          VPC (Subnet Pública)          │
              │  ┌──────────────────────────────────┐  │
              │  │       Instancia AWS EC2          │  │
              │  │          (t3.micro)              │  │
              │  │                                  │  │
              │  │  ┌────────────────────────────┐  │  │
              │  │  │     Contenedor Local       │  │  │
              │  │  │     Redis (Broker/Cache)   │  │  │
              │  │  └──────────────┬─────────────┘  │  │
              │  │                 │                │  │
              │  │  ┌──────────────▼─────────────┐  │  │
              │  │  │    notification-service    │  │  │
              │  │  │   (Consumidor Asíncrono)   │  │  │
              │  │  └────────────────────────────┘  │  │
              │  └─────────────────┬────────────────┘  │
              │                    ▼                   │
              │  ┌──────────────────────────────────┐  │
              │  │        AWS RDS Postgres          │  │
              │  │         (db.t3.micro)            │  │
              │  └──────────────────────────────────┘  │
              └────────────────────────────────────────┘

```

### Componentes de AWS Desplegados:

1. **AWS VPC (Virtual Private Cloud):** Configurada con subredes públicas directas y `nat_gateways=0`. Esto evita el cobro por procesamiento de datos o tarifas por hora de un NAT Gateway convencional.
2. **AWS EC2 Instance (`t3.micro` o `t2.micro`):** Aloja de manera centralizada el entorno de ejecución. Cuenta con un script automatizado en `UserData` que aprovisiona Docker y Docker Compose al encenderse la máquina virtual.
3. **AWS RDS PostgreSQL (`db.t3.micro`):** Instancia de base de datos relacional administrada con almacenamiento de 20 GB SSD. Garantiza copias de seguridad automáticas y aislamiento de la persistencia fuera del ciclo de vida del servidor web.
4. **AWS Security Groups:** Reglas estrictas de firewall que abren exclusivamente los puertos SSH (`22`), Auth Service (`8000`) y Booking Service (`8001`) hacia el exterior, y el puerto `5432` únicamente para la comunicación interna EC2 ➔ RDS.

---

## 🔄 Relación entre Infraestructura y Microservicios

El backend se conecta a la infraestructura mediante el mapeo dinámico de variables de entorno (utilizando `Pydantic Settings`). Al migrar desde el entorno local a AWS, la arquitectura orquesta tus servicios de la siguiente forma:

* **Base de Datos Desacoplada (RDS):** El contenedor local de PostgreSQL es eliminado del stack de Docker. En su lugar, tanto el `auth-service` como el `booking-service` apuntan al endpoint de **AWS RDS (`DB_HOST`)**. Esto reduce drásticamente el consumo de memoria RAM en la EC2.
* **Message Broker Local (Redis):** Para mitigar los altos costos fijos de un clúster de AWS ElastiCache, se mantiene una instancia de Redis como contenedor local en la EC2.
* **Flujo Asíncrono de Notificaciones (`notification-service`):** Cuando se procesa una acción en el `booking-service`, se publica un mensaje en el contenedor local de Redis. El `notification-service` actúa en segundo plano consumiendo continuamente estos eventos de Redis para disparar avisos por correo o alertas de sistema. Dado que este servicio no recibe peticiones HTTP directas desde el exterior, **no expone ningún puerto al Security Group**, protegiendo la seguridad interna del stack.

---

## 📡 Documentación de la API (Creación de Eventos)

El sistema utiliza esquemas asíncronos para procesar la información de eventos en el `booking-service`.

### Crear un Evento

* **Endpoint:** `POST http://<IP_PUBLICA_EC2>:8001/api/v1/events/`
* **Content-Type:** `application/json`

**Cuerpo de la Petición (Payload):**

```json
{
    "id": 2,
    "title": "Pequeño TicketFlow 2026",
    "tickets_left": 100
}

```

*Nota: Internamente, el modelo de persistencia mapea `tickets_left` para inicializar el inventario de boletos disponibles dentro de la base de datos de AWS RDS.*

---

## 🚀 Guía de Despliegue Completo en AWS

### 1. Desplegar la Infraestructura Cloud (CDK)

Desde tu máquina de desarrollo local, navega a la carpeta de infraestructura e instala dependencias:

```bash
cd infra/
pip install -r requirements.txt
cdk deploy

```

*Al finalizar, copia el endpoint de base de datos generado por AWS RDS y la IP Pública de la EC2.*

### 2. Configurar el Servidor de Producción (EC2)

Conéctate mediante *EC2 Instance Connect* en la consola web de AWS. Accede a la máquina virtual, clona tu repositorio y entra a la carpeta raíz:

```bash
git clone https://github.com/hpablobenja/ticketflow-backend.git
cd ticket-backend
nano .env

```

Crea el archivo `.env` compartiendo las credenciales reales de tu nube con los contenedores:

```env
# AWS RDS - Base de datos externa
DB_HOST=ticketflowvpc-xxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=ticketflow_db
DB_USER=postgres
DB_PASSWORD=tu_password_de_rds

# Broker Redis Interno (Usa el nombre del servicio asignado en el docker-compose)
REDIS_HOST=redis
REDIS_PORT=6379

# Configuraciones de negocio de los servicios
SECRET_KEY=un_secreto_super_seguro_12345

```

*(Guarda los cambios con `Ctrl + O`, presiona `Enter` y sal con `Ctrl + X`).*

### 3. Orquestar y Levantar Todos los Servicios

Compila las imágenes de tus tres microservicios de Python (`auth`, `booking`, `notifications`) e inicia todo el ecosistema de forma aislada ejecutando:

```bash
docker compose up -d --build

```

### 4. Monitoreo y Verificación

Verifica que los 4 contenedores (los 3 microservicios + el broker Redis) estén saludables y en estado `Up`:

```bash
docker compose ps

```

Si deseas examinar los logs o depurar las conexiones asíncronas entre los servicios y la base de datos cloud, ejecuta:

```bash
docker compose logs -f

```

---