from flask import session, redirect, url_for, flash
from functools import wraps

# --- CONFIGURACIÓN DE CREDENCIALES ---
# Estos son los datos de acceso para el panel de administración
USUARIO_ADMIN = "admin"
CLAVE_ADMIN = "qbonita2026"

def validar_credenciales(usuario, clave):
    """
    Comprueba si el usuario y la contraseña coinciden con los definidos.
    """
    return usuario == USUARIO_ADMIN and clave == CLAVE_ADMIN

def login_required(f):
    """
    Decorador para proteger rutas. 
    Si no hay sesión activa, redirige al usuario a la página de login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificamos si la llave de sesión existe y es verdadera
        if not session.get('admin_logged_in'):
            flash("⚠️ Acceso restringido. Por favor, inicia sesión.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def cerrar_sesion():
    """
    Limpia la sesión de administración de forma segura.
    """
    session.pop('admin_logged_in', None)
    # También es recomendable limpiar cualquier mensaje flash pendiente
    session.pop('_flashes', None)
    return True