from flask import Flask, render_template, request, redirect, flash
from flaskext.mysql import MySQL

# Crear la aplicacion Flask
app = Flask(__name__, static_url_path='/static')
app.secret_key = "Develoteca"

# Configuracion de la base de datos MySQL
mysql = MySQL()
app.config["MYSQL_DATABASE_HOST"] = "localhost"
app.config["MYSQL_DATABASE_USER"] = "root"
app.config["MYSQL_DATABASE_PASSWORD"] = ""
app.config["MYSQL_DATABASE_DB"] = "sistema"
mysql.init_app(app)

# Inicio del pedido
pedido = []

# Ruta principal - Mostrar lista de productos con opciones de busqueda y filtrado
@app.route("/")
def index():
    search = request.args.get("search")
    filterTipo = request.args.get("filterTipo")

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT tipo FROM productos;")
    tipos = [tipo[0] for tipo in cursor.fetchall()]

    cursor.execute("SELECT id, nombre, tipo, descripcion, cantidad, precio, marca, minimo, salida FROM productos;")
    productos = cursor.fetchall()

    conn.commit()
    return render_template("productos/index.html", productos=productos, search=search, filterTipo=filterTipo, tipos=tipos)

@app.route("/destroy/<int:id>")
def destroy(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id=%s", (id,))
    conn.commit()
    return redirect("/")

@app.route("/edit/<int:id>")
def edit(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id=%s", (id,))
    producto = cursor.fetchone()
    return render_template("productos/edit.html", producto=producto)

@app.route('/update', methods=['POST'])
def update():
    _nombre = request.form["txtNombre"]
    _tipo = request.form["txtTipo"]
    _descripcion = request.form["txtDescripcion"]
    _cantidad = request.form["txtCantidad"]
    _precio = request.form["txtPrecio"]
    _marca = request.form["txtMarca"]
    _minimo = request.form["txtMinimo"]  
    _salida = request.form["txtSalida"] 
    id = request.form["txtID"]

    sql = "UPDATE productos SET nombre=%s, tipo=%s, descripcion=%s, cantidad=%s, precio=%s, marca=%s, minimo=%s, salida=%s WHERE id=%s ;"
    datos = (_nombre, _tipo, _descripcion, _cantidad, _precio, _marca, _minimo, _salida, id)

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql, datos)
    conn.commit()

    return redirect("/")

@app.route('/create')
def create():
    return render_template("productos/create.html")

@app.route('/store', methods=['POST'])
def storage():
    _nombre = request.form["txtNombre"]
    _tipo = request.form["txtTipo"]
    _descripcion = request.form["txtDescripcion"]
    _cantidad = request.form["txtCantidad"]
    _precio = request.form["txtPrecio"]
    _marca = request.form["txtMarca"]
    _minimo = request.form["txtMinimo"]  
    _salida = request.form["txtSalida"]  

    if _nombre == "" or _tipo == "" or _descripcion == "" or _cantidad == "" or _precio == "" or _marca == "":
        flash("Recuerda llenar los datos de los campos")
        return redirect('create')

    sql = "INSERT INTO `productos` (`id`, `nombre`, `tipo`, `descripcion`, `cantidad`, `precio`, `marca`, `minimo`, `salida`) VALUES (NULL,%s,%s,%s,%s,%s,%s,%s,%s);"
    datos = (_nombre, _tipo, _descripcion, _cantidad, _precio, _marca, _minimo, _salida)

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

# Ruta para agregar un producto al pedido
@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos WHERE id=%s", (id,))
    producto = cursor.fetchone()

    # Verificar si el producto ya está en el pedido
    for item in pedido:
        if item['id'] == id:
            # Si esta en el pedido, aumenta la cantidad
            item['cantidad'] += 1
            break
    else:
        # Si no esta en el pedido, agrega un nuevo elemento
        pedido.append({
            'id': id,
            'nombre': producto[1],
            'precio': producto[5],
            'cantidad': 1
        })

    conn.commit()
    return redirect("/")

# Ruta para mostrar la pagina del pedido
@app.route("/pedido")
def mostrar_pedido():
    total = sum(item['precio'] * item['cantidad'] for item in pedido)

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener lista de clientes desde la base de datos
    cursor.execute("SELECT id, nombre FROM clientes;")
    clientes_data = cursor.fetchall()

    conn.commit()

    return render_template("productos/pedido.html", pedido=pedido, total=total, clientes_data=clientes_data)

# Ruta para mostrar la lista de clientes
@app.route('/clientes')
def clientes():
    search = request.args.get("search")

    conn = mysql.connect()
    cursor = conn.cursor()

    # SQL para filtrada clientes por nombre o DNI
    if search:
        cursor.execute("SELECT * FROM clientes WHERE nombre LIKE %s OR dni LIKE %s;", (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM clientes;")

    clientes_data = cursor.fetchall()

    conn.commit()

    return render_template("clientes/clientes.html", clientes_data=clientes_data)

# Ruta para mostrar el formulario de agregar nuevo cliente
@app.route("/nuevo_cliente", methods=["GET"])
def nuevo_cliente():
    return render_template("clientes/nuevo_cliente.html")

# Ruta para agregar un nuevo cliente a la base de datos
@app.route("/agregar_cliente", methods=["POST"])
def agregar_cliente():
    _nombre = request.form["nombre"]
    _dni = request.form["dni"]
    _numero = request.form["numero"]
    _direccion = request.form["direccion"]
    _cuit = request.form["cuit"]

    # Validacion de datos

    if not _nombre or not _dni or not _numero or not _direccion or not _cuit:
        flash("Todos los campos son obligatorios. Por favor, completa todos los campos.")
        return redirect("/nuevo_cliente")

    conn = mysql.connect()
    cursor = conn.cursor()

    # Insertar el nuevo cliente en la base de datos
    sql = "INSERT INTO `clientes` (`nombre`, `dni`, `numero`, `direccion`, `cuit`) VALUES (%s, %s, %s, %s, %s);"
    datos = (_nombre, _dni, _numero, _direccion, _cuit)

    cursor.execute(sql, datos)
    conn.commit()

    flash("Cliente agregado exitosamente.")
    return redirect("/clientes")

# Ruta para eliminar un cliente
@app.route("/eliminar_cliente/<int:id>")
def eliminar_cliente(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Eliminar el cliente con el ID proporcionado
    cursor.execute("DELETE FROM clientes WHERE id=%s", (id,))
    conn.commit()
    return redirect("/clientes") 
    
# Ruta para mostrar el formulario de edicion de cliente
@app.route("/editar_cliente/<int:id>", methods=["GET"])
def editar_cliente(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener los datos del cliente con el ID proporcionado para editar
    cursor.execute("SELECT * FROM clientes WHERE id=%s", (id,))
    cliente = cursor.fetchone()

    conn.commit()

    return render_template("clientes/editar_cliente.html", cliente=cliente)

# Ruta para actualizar los datos del cliente despues de editar
@app.route('/actualizar_cliente/<int:id>', methods=['POST'])
def actualizar_cliente(id):
    _nombre = request.form["nombre"]
    _dni = request.form["dni"]
    _numero = request.form["numero"]
    _direccion = request.form["direccion"]
    _cuit = request.form["cuit"]
    _saldo = request.form["saldo"]

    # Validacion de datos

    if not _nombre or not _dni or not _numero or not _direccion or not _cuit or not _saldo:
        flash("Todos los campos son obligatorios. Por favor, completa todos los campos.")
        return redirect(f"/editar_cliente/{id}")

    conn = mysql.connect()
    cursor = conn.cursor()

    # Actualizar los datos del cliente en la base de datos
    sql = "UPDATE `clientes` SET `nombre`=%s, `dni`=%s, `numero`=%s, `direccion`=%s, `cuit`=%s, `saldo`=%s WHERE `id`=%s;"
    datos = (_nombre, _dni, _numero, _direccion, _cuit, _saldo, id)

    cursor.execute(sql, datos)
    conn.commit()

    flash("Cliente actualizado exitosamente.")
    return redirect("/clientes")


# Función para restar el stock de un producto
def restar_stock(producto_id, cantidad_comprada):
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT cantidad FROM productos WHERE id=%s", (producto_id,))
    stock_actual = cursor.fetchone()[0]

    if stock_actual < cantidad_comprada:
        raise Exception("No hay suficiente stock para este producto.")

    nuevo_stock = stock_actual - cantidad_comprada

    cursor.execute("UPDATE productos SET cantidad=%s WHERE id=%s", (nuevo_stock, producto_id))
    conn.commit()

    conn.close()


def restar_stock(producto_id, cantidad_comprada):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener la cantidad actual en stock del producto
    cursor.execute("SELECT cantidad FROM productos WHERE id=%s", (producto_id,))
    stock_actual = cursor.fetchone()[0]

    # Calcular la nueva cantidad en stock después de la compra
    nuevo_stock = stock_actual - cantidad_comprada

    # Actualizar el stock en la tabla de productos
    cursor.execute("UPDATE productos SET cantidad=%s WHERE id=%s", (nuevo_stock, producto_id))

    conn.commit()



#procesar compra

@app.route("/procesar_compra", methods=["POST"])
def procesar_compra():
    # Obtener la lista de productos y cantidades del pedido
    lista_productos = ", ".join([f"{item['nombre']} (x{item['cantidad']})" for item in pedido])

    # Calcular el total de la compra
    total_compra = sum(item['precio'] * item['cantidad'] for item in pedido)

    # Obtener el nombre del cliente seleccionado
    id_cliente = request.form.get('nombre_cliente')
    
    # Verificar si id_cliente es None y manejarlo
    if id_cliente is None:
        flash("Error: Selecciona un cliente.")
        return redirect("/pedido")

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener el nombre del cliente a partir de su ID
    cursor.execute("SELECT nombre FROM clientes WHERE id=%s", (id_cliente,))
    resultado_cliente = cursor.fetchone()

    # Verificar si result_cliente es None y manejarlo
    if resultado_cliente is None:
        flash("Error: Cliente no encontrado.")
        return redirect("/pedido")

    nombre_cliente = resultado_cliente[0]

    # Obtener el monto pagado por el cliente desde el formulario
    monto_pagado = request.form.get('pago_cliente')

    # Verificar si monto_pagado es None y manejarlo
    if monto_pagado is None:
        flash("Error: Ingresa el monto pagado por el cliente.")
        return redirect("/pedido")

    # Convertir monto_pagado a float
    try:
        monto_pagado = float(monto_pagado)
    except ValueError:
        flash("Error: Ingresa un monto pagado válido.")
        return redirect("/pedido")

    # Calcular la diferencia entre el total y el pago del cliente
    diferencia = monto_pagado - total_compra

    # Obtener el saldo actual del cliente
    cursor.execute("SELECT saldo FROM clientes WHERE id=%s", (id_cliente,))
    saldo_actual = cursor.fetchone()[0]

    # Calcular el nuevo saldo sumando la diferencia
    nuevo_saldo = saldo_actual + diferencia

    # Actualizar el saldo del cliente en la base de datos
    cursor.execute("UPDATE clientes SET saldo=%s WHERE id=%s", (nuevo_saldo, id_cliente))
    conn.commit()

    # Insertar los datos en la tabla "detalles_compra"
    sql = "INSERT INTO detalles_compra (productos, total, pago, diferencia_cliente, nombre_cliente) VALUES (%s, %s, %s, %s, %s);"
    datos = (lista_productos, total_compra, monto_pagado, diferencia, nombre_cliente)
    cursor.execute(sql, datos)
    conn.commit()

    # Restar el stock de los productos comprados
    for item in pedido:
        restar_stock(item['id'], item['cantidad'])

      # Actualizar la salida de los productos en la base de datos
    for item in pedido:
        producto_id = item['id']
        cantidad_vendida = item['cantidad']

        # Obtener la salida actual del producto
        cursor.execute("SELECT salida FROM productos WHERE id=%s", (producto_id,))
        salida_actual = cursor.fetchone()[0]

        # Calcular la nueva salida sumando la cantidad vendida
        nueva_salida = salida_actual + cantidad_vendida

        # Actualizar la salida del producto en la base de datos
        cursor.execute("UPDATE productos SET salida=%s WHERE id=%s", (nueva_salida, producto_id))
        conn.commit()

    # Limpiar el pedido despues de procesar la compra
    pedido.clear()

    flash("Compra procesada exitosamente.")
    return redirect("/pedido")


# Ruta para mostrar el ranking de productos con filtro por tipo
@app.route("/ranking")
def ranking():
    # Obtener el valor del filtro de tipo desde los parametros de la URL
    tipo_filtro = request.args.get("tipo")

    conn = mysql.connect()
    cursor = conn.cursor()

    # Consulta SQL para obtener productos ordenados por salida
    # filtrados por tipo 
    if tipo_filtro:
        cursor.execute("SELECT * FROM productos WHERE tipo=%s ORDER BY salida DESC;", (tipo_filtro,))
    else:
        cursor.execute("SELECT * FROM productos ORDER BY salida DESC;")

    productos_ranking = cursor.fetchall()

    conn.commit()

    # Consulta adicional para obtener los tipos disponibles
    cursor.execute("SELECT DISTINCT tipo FROM productos;")
    tipos = [tipo[0] for tipo in cursor.fetchall()]

    return render_template("productos/ranking.html", productos_ranking=productos_ranking, tipos=tipos, tipo_filtro=tipo_filtro)

# Iniciar la aplicacion Flask
if __name__ == "__main__":
    app.run(debug=True)