import asyncio
import httpx
import time

# Configuramos el endpoint que queremos estresar (el GET de eventos o el POST de reserva)
TARGET_URL = "http://localhost:8001/api/v1/events"
TOTAL_REQUESTS = 50

async def send_single_request(client: httpx.AsyncClient, request_id: int):
    try:
        start = time.perf_counter()
        response = await client.get(TARGET_URL)
        latency = (time.perf_counter() - start) * 1000
        
        # Leemos el header de latencia interna que creamos en el Paso 1 (si existe)
        internal_latency = response.headers.get("X-Process-Time-Ms", "N/A")
        
        return {
            "id": request_id,
            "status_code": response.status_code,
            "total_latency_ms": latency,
            "internal_latency_ms": internal_latency
        }
    except Exception as e:
        return {"id": request_id, "status_code": "ERROR", "error": str(e)}

async def main():
    print(f"Iniciando Profiling Analítico: Enviando {TOTAL_REQUESTS} peticiones en ráfaga a {TARGET_URL}...")
    
    # Usamos un cliente asíncronos optimizado para simular concurrencia masiva
    async with httpx.AsyncClient(timeout=10.0) as client:
        start_test = time.perf_counter()
        
        # Creamos una lista de tareas concurrentes
        tasks = [send_single_request(client, i) for i in range(TOTAL_REQUESTS)]
        
        # Ejecutamos todas las peticiones en paralelo (Simulando Bots)
        results = await asyncio.gather(*tasks)
        
        total_test_time = time.perf_counter() - start_test
        
    # --- PROCESAMIENTO ANALÍTICO DE RESULTADOS ---
    success_count = 0
    rate_limited_count = 0
    errors_count = 0
    latencies = []

    for r in results:
        status = r.get("status_code")
        if status == 200:
            success_count += 1
            latencies.append(r["total_latency_ms"])
        elif status == 429:
            rate_limited_count += 1
        else:
            errors_count += 1

    print("\n" + "="*45)
    print("RESULTADOS DEL PROFILING ANALÍTICO")
    print("="*45)
    print(f"Tiempo total del test: {total_test_time:.2f} segundos")
    print(f"Peticiones Exitosas (HTTP 200): {success_count}")
    print(f"Bloqueadas por Rate Limiter (HTTP 429): {rate_limited_count}")
    print(f"Errores de Conexión/Otros: {errors_count}")
    
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        print(f"Latencia Promedio (Peticiones Exitosas): {avg_latency:.2f} ms")
        print(f"Petición más rápida: {min(latencies):.2f} ms")
        print(f"Petición más lenta: {max(latencies):.2f} ms")
    print("="*45)

if __name__ == "__main__":
    # Necesitas tener instalado httpx localmente: pip install httpx
    asyncio.run(main())