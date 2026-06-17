# --- Stage 1: Compilación de dependencias (Builder) ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Evita que Python escriba archivos .pyc en el disco y asegura que los logs fluyan de inmediato
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala gcc y herramientas necesarias para compilar librerías criptográficas de python-jose/passlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia los requerimientos instalando los paquetes en el directorio local del usuario
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# --- Stage 2: Imagen Final Ejecutable (Runner) ---
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copia únicamente las librerías ya compiladas e instaladas del stage anterior (reduce drásticamente el tamaño)
COPY --from=builder /root/.local /root/.local
COPY ./app ./app

# Añade los ejecutables de las librerías (como uvicorn) al PATH del contenedor
ENV PATH=/root/.local/bin:$PATH

# Exponer el puerto asignado para el servicio de autenticación
EXPOSE 8000

# Comando para ejecutar el servicio en producción de manera asíncrona
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]