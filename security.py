from flask import session, redirect, url_for, flash
from functools import wraps

# --- CONFIGURACIÓN DE CREDENCIALES ---
# Puedes cambiar estos valores por los que tú quieras
USUARIO_ADMIN = "admin"
CLAVE_ADMIN = "qbonita2026"

def validar_credenciales(usuario, clave):
    """
    Comprueba si el usuario y la contraseña son correctos.
    Esta función se usa en la ruta /login de tu app.py.
    """
    if usuario == USUARIO_ADMIN and clave == CLAVE_ADMIN:
        return True
    return False

def login_required(f):
    """
    Este es un 'decorador'. Se pone encima de las funciones 
    que quieres proteger (como el /admin) para que solo entren
    quienes hayan iniciado sesión.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Si la marca de 'admin_logged_in' no está en la sesión, lo mandamos al login
        if 'admin_logged_in' not in session:
            flash("⚠️ Por favor, inicia sesión para acceder al panel.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def cerrar_sesion():
    """
    Limpia los datos de la sesión actual.
    """
    session.pop('admin_logged_in', None)
    return True