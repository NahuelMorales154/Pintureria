from flask import Flask, render_template, request, redirect, flash
from flask_mysqldb import MySQL
import os

# Crear la aplicación Flask
app = Flask(__name__, static_url_path='/static')
app.secret_key = "Develoteca"

# Configuración de la base de datos MySQL
mysql = MySQL()
app.config["MYSQL_DATABASE_HOST"] = "localhost"
app.config["MYSQL_DATABASE_USER"] = "root"
app.config["MYSQL_DATABASE_PASSWORD"] = ""
app.config["MYSQL_DATABASE_DB"] = "sistema"
mysql.init_app(app)

#inicio del carrito
carrito = []

# Ruta principal - Mostrar lista de productos con opciones de búsqueda y filtrado
@app.route("/")
def index():
    search = request.args.get("search")
    filterTipo = request.args.get("filterTipo")

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener tipos únicos de productos para opciones de filtrado
    cursor.execute("SELECT DISTINCT tipo FROM productos;")
    tipos = [tipo[0] for tipo in cursor.fetchall()]

    # Obtener lista de productos con filtros aplicados
    cursor.execute("SELECT * FROM productos;")
    productos = cursor.fetchall()

    conn.commit()
    return render_template("productos/index.html", productos=productos, search=search, filterTipo=filterTipo, tipos=tipos)

# Ruta para eliminar un producto
@app.route("/destroy/<int:id>")
def destroy(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Eliminar el producto con el ID proporcionado
    cursor.execute("DELETE FROM productos WHERE id=%s",(id))
    conn.commit()
    return redirect("/")

# Ruta para editar un producto
@app.route("/edit/<int:id>")
def edit(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener los datos del producto con el ID proporcionado para editar
    cursor.execute("SELECT * FROM `productos` WHERE id=%s", (id))
    productos = cursor.fetchall()

    return render_template("productos/edit.html", productos=productos)

# Ruta para actualizar los datos de un producto después de editar
@app.route('/update', methods=['POST'])
def update():
    # Obtener datos del formulario
    _nombre = request.form["txtNombre"]
    _tipo = request.form["txtTipo"]
    _descripcion = request.form["txtDescripcion"]
    _cantidad = request.form["txtCantidad"]
    _precio = request.form["txtPrecio"]
    _marca = request.form["txtMarca"]
    id = request.form["txtID"]

    sql = "UPDATE productos SET nombre=%s, tipo=%s, descripcion=%s, cantidad=%s, precio=%s, marca=%s WHERE id=%s ;"
    datos = (_nombre, _tipo, _descripcion, _cantidad, _precio, _marca, id)

    conn = mysql.connect()
    cursor = conn.cursor()

    # Actualizar los datos del producto en la base de datos
    cursor.execute(sql, datos)
    conn.commit()

    return redirect("/")

# Ruta para mostrar el formulario de ingreso de nuevo producto
@app.route('/create')
def create():
    return render_template("productos/create.html")

# Ruta para almacenar un nuevo producto en la base de datos
@app.route('/store', methods=['POST'])
def storage():
    _nombre = request.form["txtNombre"]
    _tipo = request.form["txtTipo"]
    _descripcion = request.form["txtDescripcion"]
    _cantidad = request.form["txtCantidad"]
    _precio = request.form["txtPrecio"]
    _marca = request.form["txtMarca"]

    if _nombre == "" or _tipo == "" or _descripcion == "" or _cantidad == "" or _precio == "" or _marca == "":
        flash("Recuerda llenar los datos de los campos")
        return redirect('create')

    sql = "INSERT INTO `productos` (`id`, `nombre`, `tipo`, `descripcion`, `cantidad`, `precio`, `marca`) VALUES (NULL,%s,%s,%s,%s,%s,%s);"
    datos = (_nombre, _tipo, _descripcion, _cantidad, _precio, _marca)

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql, datos)
    conn.commit()
    return redirect("/") 

# Ruta para aplicar descuento a los productos
@app.route('/apply_discount', methods=['POST'])
def apply_discount():
    discount_percentage = float(request.form['discountPercentage']) / 100

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener lista de productos
    cursor.execute("SELECT * FROM productos;")
    productos = cursor.fetchall()

    # Aplicar descuento a los precios de los productos
    for producto in productos:
        new_price = float(producto[5]) * (1 + discount_percentage)
        cursor.execute("UPDATE productos SET precio=%s WHERE id=%s;", (new_price, producto[0]))

    conn.commit()
    return redirect("/")

# Ruta para agregar un producto al carrito
@app.route("/add_to_cart/<int:id>")
def add_to_cart(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener el producto con el ID proporcionado
    cursor.execute("SELECT * FROM productos WHERE id=%s", (id))
    producto = cursor.fetchone()

    carrito.append({
        'nombre': producto[1],
        'precio': producto[5]
    })

    conn.commit()
    return redirect("/")

# Ruta para mostrar el carrito
@app.route("/carrito")
def mostrar_carrito():
    total = sum(item['precio'] for item in carrito)
    return render_template("productos/carrito.html", carrito=carrito, total=total)

# Otras rutas...
@app.route('/clientes')
def clientes():
    return render_template("productos/clientes.html")

# Iniciar la aplicación Flask
if __name__ == "__main__":
    app.run(debug=True)