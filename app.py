import os
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
import firebase_admin
from firebase_admin import credentials, firestore

# --- IMPORTACIÓN DE SEGURIDAD ---
# Se importa desde security.py (asegúrate de que el archivo esté en la raíz)
try:
    from security import login_required, validar_credenciales, cerrar_sesion
except ImportError:
    # Fallback por si el archivo tiene problemas de ruta en Render
    def login_required(f): return f
    def validar_credenciales(u, c): return False
    def cerrar_sesion(): pass

app = Flask(__name__)
# Llave para sesiones seguras
app.secret_key = os.environ.get("SECRET_KEY", "qbonita_llave_maestra_2026")

# --- CONFIGURACIÓN DE FIREBASE ---
# Buscamos el JSON en la carpeta 'datos' como indicaste en tu estructura
RUTA_JSON = os.path.join(os.path.dirname(__file__), 'datos', 'serviceAccountKey.json')

if not firebase_admin._apps:
    try:
        if os.path.exists(RUTA_JSON):
            cred = credentials.Certificate(RUTA_JSON)
            firebase_admin.initialize_app(cred)
        else:
            print("⚠️ Error: No se encontró serviceAccountKey.json en /datos")
    except Exception as e:
        print(f"❌ Error inicializando Firebase: {e}")

db = firestore.client()

# --- UTILIDAD: EXTRACTOR DE LINKS ---
def extraer_lista_links(texto):
    if not texto: return []
    # Busca URLs que terminen en extensiones de imagen
    return re.findall(r'https?://[^\s<> "\[\]]+\.(?:jpg|jpeg|png|gif|webp|JPG|PNG)', texto)

# --- RUTA: TIENDA PÚBLICA ---
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

# --- RUTA: DETALLE DEL PRODUCTO ---
@app.route('/detalle/<id>')
def detalle_producto(id):
    doc_ref = db.collection('tienda_qbonita').document(id).get()
    if doc_ref.exists:
        producto = doc_ref.to_dict()
        producto['id'] = doc_ref.id
        
        # Garantizar que siempre haya una lista de imágenes para el carrusel
        if 'imagenes' not in producto or not producto['imagenes']:
            url_principal = producto.get('url_imagen')
            producto['imagenes'] = [url_principal] if url_principal else []
            
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

# --- RUTA: PANEL ADMIN ---
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        id_prod = request.form.get('id_producto') 
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        
        links_sucios = request.form.get('url_foto') 
        links_limpios = extraer_lista_links(links_sucios)

        if titulo and links_limpios:
            datos = {
                'titulo': titulo,
                'descripcion': descripcion,
                'precio': precio,
                'url_imagen': links_limpios[0], 
                'imagenes': links_limpios,
                'estado': request.form.get('estado', 'disponible'),
                'fecha': datetime.now()
            }
            
            if id_prod:
                db.collection('tienda_qbonita').document(id_prod).update(datos)
                flash("✅ Producto actualizado", "success")
            else:
                db.collection('tienda_qbonita').add(datos)
                flash("✨ Publicado correctamente", "success")
            
            return redirect(url_for('admin'))

    productos_ref = db.collection('tienda_qbonita').order_by('fecha', direction=firestore.Query.DESCENDING)
    mis_productos = [{**doc.to_dict(), 'id': doc.id} for doc in productos_ref.stream()]
    return render_template('admin.html', productos=mis_productos)

# --- ACCIONES ---
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

@app.route('/comprar/<id>')
def comprar(id):
    doc = db.collection('tienda_qbonita').document(id).get()
    if doc.exists:
        p = doc.to_dict()
        telefono = "584143939483"
        mensaje = f"¡Hola! Me encanta este accesorio de la vitrina: {p['titulo']}. ✨"
        return redirect(f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20')}")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    cerrar_sesion()
    return redirect(url_for('index'))

# --- CONFIGURACIÓN PARA RENDER ---
if __name__ == '__main__':
    # Render usa la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)