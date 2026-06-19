import streamlit as tf
import requests
from config import USER_SERVICE_URL 

tf.set_page_config(page_title="Mi Perfil", page_icon="👤")

if not tf.session_state.get("token"):
    tf.error("🚨 Acceso Restringido. Debes iniciar sesión como Customer.")
    tf.stop()

tf.header("👤 Gestión de Mi Cuenta (CRUD)")
headers = {"Authorization": f"Bearer {tf.session_state.token}"}

# READ: Obtener datos actuales
try:
    user_id = tf.session_state.user_id 
    res = requests.get(f"{USER_SERVICE_URL}/users/{user_id}", headers=headers)
    if res.status_code == 200:
        user_data = res.json()
        tf.write(f"**ID de Usuario:** `{tf.session_state.user_id}`")
        tf.write(f"**Email Actual:** {user_data.get('email')}")
        
        # UPDATE: Formulario para modificar datos
        with tf.form("update_profile"):
            tf.subheader("Actualizar Información")
            new_email = tf.text_input("Cambiar Correo", value=user_data.get('email'))
            new_password = tf.text_input("Nueva Contraseña (Dejar vacío para no cambiar)", type="password")
            if tf.form_submit_button("Guardar Cambios"):
                payload = {"email": new_email}
                if new_password: payload["password"] = new_password
                
                up_res = requests.put(f"{USER_SERVICE_URL}/users/{user_id}", json=payload, headers=headers)
                if up_res.status_code == 200:
                    tf.success("¡Datos actualizados correctamente!")
                    tf.session_state.user_email = new_email
                else: tf.error("Error al actualizar datos.")
                
        # DELETE: Darse de baja
        tf.divider()
        tf.subheader("⚠️ Zona de Peligro")
        if tf.button("❌ Eliminar mi cuenta permanentemente"):
            del_res = requests.delete(f"{USER_SERVICE_URL}/users/{user_id}", headers=headers)
            if del_res.status_code == 200:
                tf.warning("Cuenta eliminada.")
                tf.session_state.clear()
                tf.rerun()
            else: tf.error("No se pudo procesar la baja.")
except Exception as e:
    tf.error(f"Error cargando el perfil: {e}")