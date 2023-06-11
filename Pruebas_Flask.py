"""Para obtener la direccion ponemos:
En la direccion del archivo desde el CMD:
    1- set FLASK_APP=nombre.py
    2- flask run
    
    python nombre.py            para ejecutar el servidor en modo de desarrollo (debug = on).
                                para no estar reiniciando el servidor en cada cambio.
                                -> Esto siempre que este el if (__name__ == '__main__'): al final del codigo"""
from flask import Flask, render_template

app = Flask(__name__)           #Para saber si esta siendo ejecutando desde un archivo principal o esta siendo importada.

@app.route("/")                 #Decorador, ruta principal.
def Index():
    return render_template("index.html")

if (__name__ == "__main__"):    #Modo desarrollo. (Usar solo en desarrollo, desabilitar en produccion)
    app.run(debug=True)