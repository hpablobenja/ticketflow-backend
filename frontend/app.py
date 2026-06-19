import streamlit as tf
import requests
from config import AUTH_SERVICE_URL

tf.set_page_config(page_title="TicketFlow - Autenticación", page_icon="🎫", layout="centered")

# Inicialización de estados de sesión comunes
if "token" not in tf.session_state: tf.session_state.token = None
if "user_id" not in tf.session_state: tf.session_state.user_id = None
if "user_email" not in tf.session_state: tf.session_state.user_email = None
if "role" not in tf.session_state: tf.session_state.role = None

tf.title("🎫 TicketFlow System")
tf.subheader("Portal de Acceso Unificado")

if not tf.session_state.token:
    tab1, tab2 = tf.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
    
    with tab1:
        email = tf.text_input("Correo electrónico", key="login_email")
        password = tf.text_input("Contraseña", type="password", key="login_pass")
        if tf.button("Ingresar Sistema", use_container_width=True):
            try:
                res = requests.post(f"{AUTH_SERVICE_URL}/token", data={"username": email, "password": password})
                if res.status_code == 200:
                    data = res.json()
                    tf.session_state.token = data.get("access_token")
                    tf.session_state.user_id = data.get("user_id")
                    tf.session_state.role = data.get("role")# Captura el Rol expuesto
                    tf.session_state.user_email = email
                    tf.success(f"¡Bienvenido! Rol: {tf.session_state.role}")
                    tf.rerun()
                else:
                    tf.error("Credenciales inválidas o datos erróneos.")
            except Exception as e:
                tf.error(f"Fallo de conexión con auth-service: {e}")
                
    with tab2:
        email_reg = tf.text_input("Nuevo Correo")
        pass_reg = tf.text_input("Nueva Contraseña", type="password")
        role_reg = tf.selectbox("Selecciona tu Rol", ["Customer", "Organizer"])
        if tf.button("Crear Cuenta", use_container_width=True):
            try:
                payload = {"email": email_reg, "password": pass_reg, "role": role_reg}
                res = requests.post(f"{AUTH_SERVICE_URL}/register", json=payload)
                if res.status_code == 201: tf.success("¡Usuario creado con éxito! Inicia sesión.")
                else: tf.error("No se pudo completar el registro.")
            except Exception as e:
                tf.error(f"Error de red: {e}")
else:
    tf.success(f"Sesión activa como **{tf.session_state.user_email}** ({tf.session_state.role})")
    tf.info("👈 Utiliza la barra lateral para navegar a tus paneles autorizados.")
    if tf.button("🔒 Cerrar Sesión", use_container_width=True):
        tf.session_state.clear()
        tf.rerun()