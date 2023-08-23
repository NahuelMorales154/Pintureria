#Para obtener la direccion ponemos:
#En la direccion del archivo desde el CMD:
#    1- set FLASK_APP=nombre.py
#    2- flask run
#    
#    python nombre.py            para ejecutar el servidor en modo de desarrollo (debug = on).
#                                para no estar reiniciando el servidor en cada cambio.
#                                -> Esto siempre que este el if (__name__ == '__main__'): al final del codigo

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

#Conexion a la base de datos#
app = Flask(__name__)                       #Para saber si esta siendo ejecutando desde un archivo principal o esta siendo importada.
app.config['MYSQL_HOST'] = "localhost"          #Host
app.config['MYSQL_USER'] = "root"               #Usuario de phpmyadmin
app.config['MYSQL_PASSWORD'] = ""               #Contraseña de phpmyadmin
app.config['MYSQL_DB'] = "pintureria_pehuajo"   #Base de datos (No tabla)
mysql = MySQL(app)
#Llave#
app.secret_key = "mysecretkey"

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
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos ORDER BY cantidad ASC')
    datos = cur.fetchall()
    return render_template("productos.html", datosDB = datos)

@app.route("/clientes")
def Clientes():
    return render_template("clientes.html")

@app.route("/proveedores")
def Proveedores():
    return render_template("proveedores.html")

@app.route("/reportes")
def Reportes():
    return render_template("reportes.html")

#-------------------- ABM Productos--------------------#
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
        #mensaje
        flash('Producto agregado satisfactoriamente')
    return redirect(url_for('Productos'))

@app.route("/edit_product/<string:id>")
def edit_product(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos WHERE id = %s', (id))
    datos = cur.fetchall()
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos')
    datos2 = cur.fetchall()
    return render_template('Productos.html', editDB = datos[0], datosDB = datos2)

@app.route("/update_product/<string:id>", methods=['POST'])
def update_product(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        cantidad = request.form['cantidad']
        precio = request.form['precio']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE productos 
            SET nombre = %s,
                tipo = %s,
                cantidad = %s,
                precio = %s
            Where id = %s """, (nombre, tipo, cantidad, precio, id))
        mysql.connection.commit()
        flash('Producto actualizado satisfactoriamente')
    return redirect(url_for('Productos'))

@app.route("/delete_product/<string:id>")
def delete_product(id):
    #consulta delete_product
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM productos WHERE id = {0}'.format(id))
    mysql.connection.commit()
    #mensaje
    flash('Producto eliminado satisfactoriamente')
    return redirect(url_for('Productos'))

#-------------------- Filtro--------------------#
@app.route("/filter", methods=['POST'])
def filter():
    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        tipo_orden = request.form['tipo_orden']
        orden = request.form['orden']
        #consulta filter
        cur = mysql.connection.cursor()
        cur.execute(" SELECT * FROM productos WHERE nombre LIKE '%{0}%' AND tipo LIKE '%{1}%' ORDER BY {2} {3}".format(nombre, tipo, tipo_orden, orden))
        mysql.connection.commit()
        datos = cur.fetchall()
    return render_template("productos.html", datosDB = datos, filterDB = (nombre, tipo, tipo_orden, orden))

#Modo desarrollo. (Usar solo en desarrollo, desabilitar en produccion)
if (__name__ == "__main__"):
    app.run(port = 3000, debug=True)