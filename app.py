import os
from flask import Flask, render_template

app = Flask(__name__)

# PRODUCTOS DE PRUEBA (sin Firebase)
productos_falsos = [
    {'id': '1', 'titulo': 'Collar de Girasol', 'descripcion': 'Hermoso collar con girasol', 'precio': '12.50', 'url_imagen': '/static/recursos/tu_cabecera.png'},
    {'id': '2', 'titulo': 'Pulsera de Amistad', 'descripcion': 'Pulsera tejida a mano', 'precio': '8.00', 'url_imagen': '/static/recursos/tu_cabecera.png'},
]

@app.route('/')
def index():
    return render_template('index.html', productos=productos_falsos)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)