import streamlit as tf
import requests
from config import BOOKING_SERVICE_URL

tf.set_page_config(page_title="Logística de Reservas", page_icon="📊")

if not tf.session_state.get("token") or tf.session_state.get("role") != "Organizer":
    tf.error("🚨 Panel exclusivo para Organizadores.")
    tf.stop()

headers = {"Authorization": f"Bearer {tf.session_state.token}"}
tf.header("📊 Registro Maestro de Reservaciones Globales")

try:
    res = requests.get(f"{BOOKING_SERVICE_URL}/bookings", headers=headers)
    if res.status_code == 200:
        reservas = res.json()
        if not reservas:
            tf.info("No existen reservaciones activas en el clúster.")

        for r in reservas:
            with tf.container(border=True):
                tf.write(
                    f"🎫 **Reserva ID:** `{r.get('id')}` | Asiento del Evento: `{r.get('event_id')}`"
                )
                tf.write(
                    f"👤 Reservado por User ID: `{r.get('user_id')}` | Estado: **{r.get('status').upper()}**"
                )

                # UPDATE/DELETE: Liberar o forzar expiración del bloqueo en Redis
                if tf.button(
                    "🔓 Forzar Liberación de Asiento", key=f"cancel_{r.get('id')}"
                ):
                    c_res = requests.delete(
                        f"{BOOKING_SERVICE_URL}/reservations/{r.get('id')}",
                        headers=headers,
                    )
                    if c_res.status_code == 200:
                        tf.success("Bloqueo removido.")
                        tf.rerun()
except Exception as e:
    tf.error(f"Error de enlace con el microservicio de logs: {e}")
