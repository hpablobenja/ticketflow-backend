import streamlit as tf
import requests
from config import BOOKING_SERVICE_URL

tf.set_page_config(page_title="Panel Organizador", page_icon="🏟️", layout="wide")

if not tf.session_state.get("token") or tf.session_state.get("role") != "Organizer":
    tf.error("🚨 Panel exclusivo para Organizadores autorizados.")
    tf.stop()

headers = {"Authorization": f"Bearer {tf.session_state.token}"}

tf.header("⚙️ Operaciones CRUD sobre Eventos")

# Formulario CREATE
with tf.expander("➕ Crear Nuevo Evento"):
    title = tf.text_input("Título del Evento")
    tickets = tf.number_input(
        "Inventario Inicial (tickets_left)", min_value=1, value=100
    )
    if tf.button("Publicar Evento"):
        payload = {"title": title, "tickets_left": tickets}
        res = requests.post(
            f"{BOOKING_SERVICE_URL}/events/", json=payload, headers=headers
        )
        if res.status_code == 201:
            tf.success("Evento creado con éxito.")

# READ, UPDATE & DELETE
tf.subheader("📋 Inventario Actual")
try:
    res = requests.get(f"{BOOKING_SERVICE_URL}/events?limit=50&offset=0")
    if res.status_code == 200:
        for ev in res.json():
            with tf.container(border=True):
                c1, c2 = tf.columns([3, 1])
                with c1:
                    tf.write(
                        f"**[{ev.get('id')}] {ev.get('title')}** - Disponibles: {ev.get('tickets_left')}"
                    )
                with c2:
                    if tf.button("❌ Eliminar", key=f"del_{ev.get('id')}"):
                        d_res = requests.delete(
                            f"{BOOKING_SERVICE_URL}/events/{ev.get('id')}",
                            headers=headers,
                        )
                        if d_res.status_code == 200:
                            tf.rerun()
except Exception as e:
    tf.error(f"Error: {e}")
