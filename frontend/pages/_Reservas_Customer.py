import streamlit as tf
import requests
from config import BOOKING_SERVICE_URL

tf.set_page_config(page_title="Reservas", page_icon="🎟️", layout="wide")

if not tf.session_state.get("token") or tf.session_state.get("role") != "Customer":
    tf.error("🚨 Acceso Restringido. Debes iniciar sesión como Customer.")
    tf.stop()

col1, col2 = tf.columns([2, 1])

with col1:
    tf.header("🗓️ Eventos Disponibles")
    if tf.button("🔄 Actualizar Catálogo"):
        try:
            res = requests.get(f"{BOOKING_SERVICE_URL}/events?limit=10&offset=0")
            if res.status_code == 200:
                for ev in res.json():
                    with tf.container(border=True):
                        tf.subheader(f"🏟️ {ev.get('title')}")
                        # Cambiado según tus especificaciones concretas
                        tf.write(f"🎟️ **Entradas Restantes:** {ev.get('tickets_left')}")
                        tf.caption(f"ID del Evento: `{ev.get('id')}`")
        except Exception as e:
            tf.error(f"Error de conexión: {e}")

with col2:
    tf.header("⚡ Nueva Reserva")
    event_id = tf.text_input("ID del Evento")
    tf.info(f"👤 Vinculado a tu **user_id: {tf.session_state.user_id}**")

    if tf.button("🔒 Bloquear Entrada (10 min)"):
        if event_id:
            try:
                headers = {"Authorization": f"Bearer {tf.session_state.token}"}
                target_url = f"{BOOKING_SERVICE_URL}/events/{event_id}/reserve?user_id={tf.session_state.user_id}"
                res = requests.post(target_url, headers=headers)
                if res.status_code == 200:
                    tf.success("🎉 ¡Reserva realizada!")
                else:
                    tf.error(f"Error: {res.json().get('detail', 'No disponible')}")
            except Exception as e:
                tf.error(f"Error en transacción: {e}")
