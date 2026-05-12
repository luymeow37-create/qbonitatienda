import os
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
import firebase_admin
from firebase_admin import credentials, firestore

# --- IMPORTACIÓN DE SEGURIDAD ---
try:
    from security import login_required, validar_credenciales, cerrar_sesion
except ImportError:
    def login_required(f): return f
    def validar_credenciales(u, c): return False
    def cerrar_sesion(): pass

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "qbonita_llave_maestra_2026")

# --- CONFIGURACIÓN DE FIREBASE (DIRECTA EN EL CÓDIGO) ---
firebase_config = {
    "type": "service_account",
    "project_id": "brawl-67616",
    "private_key_id": "724abc063e6f08ffac06a9383ad1bc4b176a5362",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDcXb+h+ym3ES24\nDwX2JQseeUrLJlYHgGswpxdJPoAS2eeoQ9Aab2X6D2Q4NzX2a8o1qgWlTUlO5Zne\nxq466Vs6K0huQEygFV8azp48wGxC1WEpgRgv3l+NC1kUU9PXQUKQOy8WTQikYmoA\nyVoC+Pl4pbrFO3IbDvLIOwaC2EtJQFc3PgQnCgC2wmcokTqAZ3eSYWk9GuygYtSq\nm51azLTPoJgwn8FgPXdsbLaeMIqKa6VDniZrM8lAIlg/Ag1maTsh9PI1W6RlGSTu\nG3OIGzV/Lg3hs/Z4MF+Gh3/tqV6uweK+Io6agbzTt0nrySBcqqiMT0ninEU0a+NT\nmKsFshdNAgMBAAECggEANlE9XRXlsGQhms7JL2TuGrLXBsAKUIsM4M8u5DTtqLfh\nbA5bC0kOH9cPYvPo7zaefx/LiHVGbpYVmV3rsEW44NuuXM6olITwDlGDm4HqrYaf\nDnXtmk77ym5TpLkM7G//kkGkV6DhUnOXoV4AO99WzrA7G0aN17GVkllKP5JE7Gbk\neFV++A3Y6y/1JfyfzY43S0vFYtPPkqo8CT1Mi30ZyGXf9oAORRKUsE7gRu0EPe6p\nHHXS9lxUmBXuxy1dy/kDMswOPqMcI2JXA1B2/+wIm3grqhuMwatdK/pe3yKa19JQ\nDcVKDIcQjooAcx245Lh5X/P1j+AMZZZAu5oaEg66WQKBgQDzZ7clUqwwsQB9yCRH\nPuHXVpim8b4z/mnrQ1iwqOXN6idmfyl7aKq3xseUXF+AgleWbiI0jYnsQPLESlRE\nDjfxiOg1UL/b8xmR9/kyna5Uo3zQHpOD88FJoXjjmHo2rLH+IHZB1kNSDtF35k/w\nbMAIkUFnAwwqebLecICs3qLfAwKBgQDnxNifakVD6hsIT9Iv6s3omc5jzWM2W+Xa\nGmFKsItxID3CqO+OwKHnD7wik8JYjnt2RLfz0/nguvA0wh+GMYMKt9ZdUmDZjYCA\nte2acqI+hks6nrjCbsCvyLqjJ6226eyGAVUUCRlpcbirz68x/YYOLV1aZcPz+OXc\nw3sLbiN3bwKBgQDoISBr6sUmhpeGXWojvBebyw04IVIYuef/ozGhAOJwl3/N4zYH\naJFvRJavqcy2fRfU8eGTJuzDMEmV46Erajf2FHAH8KOYuuXG7KtulyxbsbLltFNQ\nwxWyB9mHjLH5FIeHaSP+s71uM42XAEF6c+xL/2NVP3XJyFhKhRZiRs0jSwKBgGia\n3JZetXJol9jRhfEgjdy8hn1e9rdTFNOyclTuh5EAVz+jVbPdV3VdEbGddOrZK/n+\nG/RNqQr39HAraWT8tcNBo9us0Y9/IQ92jQ3XTUjg/dUwS/1dVVRBSZNX1jynKZx1\nv3tye+iubgYFj3IFldqSOP8SzTUxEjXoeIF5LUK7AoGBAKznKfhEDYR9Ifj/N0Rf\n1Av7oQU8RoR3FTxJu00LwQJXuYqkcQUjGujRtUoEVOZAPPgkXo86lhgkeyTfzusz\naLDmUzR3MMCDMTB1/Hxce/aZXYCj50PZ1PU08INdn+J7yjdxiv8MhM2lFtcCcmoi\nbOsmBRM3M6bwmXFjJfGZU9ib\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@brawl-67616.iam.gserviceaccount.com",
    "client_id": "108365518647957298239",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40brawl-67616.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase inicializado correctamente (desde código)")
    except Exception as e:
        print(f"❌ Error inicializando Firebase: {e}")

db = firestore.client()

# --- UTILIDAD: EXTRACTOR DE LINKS ---
def extraer_lista_links(texto):
    if not texto: return []
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
        print(f"Error al cargar productos: {e}")
        return render_template('index.html', productos=[])

# --- RUTA: DETALLE DEL PRODUCTO ---
@app.route('/detalle/<id>')
def detalle_producto(id):
    doc_ref = db.collection('tienda_qbonita').document(id).get()
    if doc_ref.exists:
        producto = doc_ref.to_dict()
        producto['id'] = doc_ref.id
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)