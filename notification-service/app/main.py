import asyncio
import json
import logging
import sys
from config import settings
import redis.asyncio as aioredis

# Configuración de Logs Estructurados en JSON para Producción (AWS CloudWatch)
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

logger = logging.getLogger("NotificationWorker")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

async def process_notification(message_data: str):
    """Simulación del procesamiento pesado del código QR y envío de correo"""
    try:
        order = json.loads(message_data)
        ticket_id = order.get("ticket_id")
        email = order.get("email")
        
        logger.info(f"Iniciando generación de código QR para Ticket ID: {ticket_id}")
        
        # Simulación de delay por generación de PDF/QR o consumo de API externa (SendGrid/SES)
        await asyncio.sleep(2) 
        
        # Log estructurado final que leería CloudWatch
        logger.info(f"Notificación de entrada enviada exitosamente a {email} para Ticket #{ticket_id}")
    except Exception as e:
        logger.error(f"Error procesando la notificación: {str(e)}")

async def main():
    logger.info("Iniciando Worker de Notificaciones. Conectando a Redis Pub/Sub...")
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    
    # Suscribirse al canal de órdenes de tickets
    await pubsub.subscribe("ticket_orders")
    
    logger.info("Worker listo y escuchando el canal 'ticket_orders'.")
    
    try:
        while True:
            # Escucha mensajes de manera no bloqueante
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                data = message.get("data")
                if data:
                    # Ejecutar la tarea pesada sin bloquear el bucle de escucha del pub-sub
                    asyncio.create_task(process_notification(data))
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logger.info("Worker detenido por el sistema.")
    finally:
        await pubsub.unsubscribe("ticket_orders")
        await redis.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Proceso terminado por el usuario.")