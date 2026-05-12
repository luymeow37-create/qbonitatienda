import os
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
import firebase_admin
from firebase_admin import credentials, firestore

# --- IMPORTACIÓN DE SEGURIDAD ---
# Se utiliza security.py según tu estructura de archivos
from security import login_required, validar_credenciales, cerrar_sesion

app = Flask(__name__)
app.secret_key = "qbonita_llave_maestra_2026"

# --- CONFIGURACIÓN DE FIREBASE ---
RUTA_JSON = os.path.join('datos', 'serviceAccountKey.json')
if not firebase_admin._apps:
    cred = credentials.Certificate(RUTA_JSON)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- UTILIDAD: EXTRACTOR DE LINKS (Múltiples fotos) ---
def extraer_lista_links(texto):
    """
    Extrae links directos (.jpg, .png, .webp) de bloques de texto.
    Si pegas 10 links de ImgBB, esta función los convierte en una lista real.
    """
    if not texto: return []
    # Buscamos patrones de URL que terminen en extensiones de imagen comunes
    return re.findall(r'https?://[^\s<> "\[\]]+\.(?:jpg|jpeg|png|gif|webp)', texto)

# --- RUTA: TIENDA PÚBLICA (INDEX / VITRINA) ---
@app.route('/')
def index():
    try:
        productos_ref = db.collection('tienda_qbonita').order_by('fecha', direction=firestore.Query.DESCENDING)
        lista_productos = []
        for doc in productos_ref.stream():
            p = doc.to_dict()
            p['id'] = doc.id
            if 'estado' not in p: p['estado'] = 'disponible'
            lista_productos.append(p)
        return render_template('index.html', productos=lista_productos)
    except Exception as e:
        return f"Error en la base de datos: {e}"

# --- RUTA: DETALLE DEL PRODUCTO (Aquí se ven y pasan las fotos) ---
@app.route('/detalle/<id>')
def detalle_producto(id):
    """Muestra la galería de fotos del producto."""
    doc_ref = db.collection('tienda_qbonita').document(id).get()
    if doc_ref.exists:
        producto = doc_ref.to_dict()
        producto['id'] = doc_ref.id
        
        # Si el producto no tiene la lista 'imagenes', usamos la principal
        if 'imagenes' not in producto or not producto['imagenes']:
            producto['imagenes'] = [producto.get('url_imagen')]
            
        return render_template('detalle.html', p=producto)
    
    flash("El producto no existe", "warning")
    return redirect(url_for('index'))

# --- RUTA: LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        clave = request.form.get('clave')
        if validar_credenciales(usuario, clave):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        flash("Usuario o clave incorrectos", "danger")
    return render_template('login.html')

# --- RUTA: PANEL ADMIN (GESTIÓN TOTAL) ---
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        id_prod = request.form.get('id_producto') 
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        
        # Recibimos el bloque de texto con uno o muchos links
        links_sucios = request.form.get('url_foto') 
        links_limpios = extraer_lista_links(links_sucios)

        if titulo and links_limpios:
            datos = {
                'titulo': titulo,
                'descripcion': descripcion,
                'precio': precio,
                'url_imagen': links_limpios[0], # La primera foto es la portada en la vitrina
                'imagenes': links_limpios,      # Todas las fotos guardadas en una lista
                'estado': request.form.get('estado', 'disponible'),
                'fecha': datetime.now()
            }
            
            if id_prod:
                db.collection('tienda_qbonita').document(id_prod).update(datos)
                flash("✅ Producto actualizado", "success")
            else:
                db.collection('tienda_qbonita').add(datos)
                flash("✨ Publicado con múltiples fotos", "success")
            
            return redirect(url_for('admin'))

    productos_ref = db.collection('tienda_qbonita').order_by('fecha', direction=firestore.Query.DESCENDING)
    mis_productos = [{**doc.to_dict(), 'id': doc.id} for doc in productos_ref.stream()]
    return render_template('admin.html', productos=mis_productos)

# --- ACCIONES DE ESTADO Y ELIMINACIÓN ---
@app.route('/estado/<id>')
@login_required
def cambiar_estado(id):
    doc_ref = db.collection('tienda_qbonita').document(id)
    doc = doc_ref.get()
    if doc.exists:
        actual = doc.to_dict().get('estado', 'disponible')
        nuevo = 'agotado' if actual == 'disponible' else 'disponible'
        doc_ref.update({'estado': nuevo})
        flash(f"Estado cambiado a {nuevo}", "info")
    return redirect(url_for('admin'))

@app.route('/eliminar/<id>')
@login_required
def eliminar(id):
    db.collection('tienda_qbonita').document(id).delete()
    flash("🗑️ Eliminado correctamente", "danger")
    return redirect(url_for('admin'))

# --- RUTA: BOTÓN DE COMPRA ---
@app.route('/comprar/<id>')
def comprar(id):
    doc = db.collection('tienda_qbonita').document(id).get()
    if doc.exists:
        p = doc.to_dict()
        telefono = "584143939483" # Reemplaza con el de Elena
        mensaje = f"¡Hola! Me encanta este accesorio de la vitrina: {p['titulo']}. ✨"
        return redirect(f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20')}")
    return redirect(url_for('index'))

# --- CIERRE DE SESIÓN ---
@app.route('/logout')
def logout():
    cerrar_sesion()
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)