#Para obtener la direccion ponemos:
#En la direccion del archivo desde el CMD:
#    1- set FLASK_APP=nombre.py
#    2- flask run
#    
#    python nombre.py            para ejecutar el servidor en modo de desarrollo (debug = on).
#                                para no estar reiniciando el servidor en cada cambio.
#                                -> Esto siempre que este el if (__name__ == '__main__'): al final del codigo

from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)                       #Para saber si esta siendo ejecutando desde un archivo principal o esta siendo importada.
app.config['MYSQL_HOST'] = "localhost"          #Host
app.config['MYSQL_USER'] = "root"               #Usuario de phpmyadmin
app.config['MYSQL_PASSWORD'] = ""               #Contraseña de phpmyadmin
app.config['MYSQL_DB'] = "pintureria_pehuajo"   #Base de datos (No tabla)
mysql = MySQL(app)

#Rutas#
@app.route("/")                             #Decorador, ruta principal.
def Index():
    return render_template("index.html")

@app.route("/carga-de-Productos")
def CargaProducto():
    return render_template("carga-productos.html")

@app.route("/venta")
def Venta():
    return render_template("venta.html")

@app.route("/Empresa")
def Empresa():
    return render_template("empresa.html")

@app.route("/productos")
def Productos():
    return render_template("productos.html")

@app.route("/clientes")
def Clientes():
    return render_template("clientes.html")

@app.route("/proveedores")
def Proveedores():
    return render_template("proveedores.html")

@app.route("/reportes")
def Reportes():
    return render_template("reportes.html")

#-------------------- ABM --------------------#
@app.route("/add_product", methods=['POST'])
def add_product():
    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        cantidad = request.form['cantidad']
        precio = request.form['precio']
        #consulta add_product
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO productos (nombre, tipo, cantidad, precio) VALUES (%s, %s ,%s ,%s)', (nombre, tipo, cantidad, precio))
        mysql.connection.commit()
        
        print(f"nombre: {nombre}\nTipo: {tipo}\nCantidad: {cantidad},\nPrecio: ${precio}")
    return redirect(url_for('Productos'))

@app.route("/edit_product")
def edit_product():
    return "edit product"

@app.route("/delete_product")
def delete_product():
    return "delete_product"

#Modo desarrollo. (Usar solo en desarrollo, desabilitar en produccion)
if (__name__ == "__main__"):
    app.run(port = 3000, debug=True)