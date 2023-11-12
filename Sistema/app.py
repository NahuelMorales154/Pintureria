from flask import Flask, render_template, request, redirect, flash, session
from flaskext.mysql import MySQL
import json
import heapq

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

# Inicio del pedido/orden de compra
pedido = []
lista_vta = []
listaDNIs = []
listaCUITs = []

# Ruta principal
@app.route("/")
def index():
    return render_template("index.html")
contrasena_correcta = "asd123"
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        contrasena_ingresada = request.form.get("contrasena")
        if contrasena_ingresada == contrasena_correcta:
            # Contraseña correcta, redirige al usuario al índice
            return render_template("home.html")
        else:
            # Contraseña incorrecta, muestra un mensaje de error
            mensaje_error = "Contraseña incorrecta. Inténtalo de nuevo."
            return render_template("index.html", mensaje_error=mensaje_error)
    return render_template("index.html", mensaje_error=None)

@app.route("/home")
def home():
    current_page = 'home'
    return render_template("home.html", current_page=current_page)
# Ruta - Mostrar lista de productos con opciones de busqueda y filtrado
@app.route("/productos")
def products():
    current_page = 'productos'
    search = request.args.get("search")
    filterTipo = request.args.get("filterTipo")

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT tipo FROM productos;")
    tipos = [tipo[0] for tipo in cursor.fetchall()]

    cursor.execute("SELECT id, nombre, tipo, descripcion, cantidad, precio, marca, minimo, salida FROM productos;")
    productos = cursor.fetchall()

    conn.commit()

    # Orden de Venta
    total = sum(item['precio'] * item['cantidad'] for item in pedido)

    conn = mysql.connect()
    cursor = conn.cursor()

    conn.commit()
    return render_template("productos/productos.html", current_page=current_page, productos=productos, search=search, filterTipo=filterTipo, tipos=tipos, lista_pedido=pedido, total=total)

@app.route("/destroy/<int:id>")
def destroy(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id=%s", (id,))
    conn.commit()
    return redirect("/productos")

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

    return redirect("/productos")

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
    return redirect("/productos")

# Ruta para aplicar descuento/aumento a los productos
@app.route('/apply_discount', methods=['POST'])
def apply_discount():
    try:
        discount_percentage_raw = request.form['discountPercentage']
        
        try:
            discount_percentage = float(discount_percentage_raw)
        except ValueError:
            flash(f"Error: El descuento/aumento '{discount_percentage_raw}' no es un número válido.")
            return redirect("/productos")

        product_type = request.form.get('tipoFiltro')
        conn = mysql.connect()
        cursor = conn.cursor()

        if product_type:
            cursor.execute("SELECT * FROM productos WHERE tipo = %s;", (product_type,))
        else:
            cursor.execute("SELECT * FROM productos;")

        productos = cursor.fetchall()

        for producto in productos:
            precio_index = 5  # Ajusta según la estructura de tu base de datos
            precio_original = float(producto[precio_index])
            # Calcula el nuevo precio teniendo en cuenta el descuento/aumento
            new_price = precio_original * (1 + discount_percentage / 100)
            print(f"Producto: {producto[1]}, Precio Original: {precio_original}, Nuevo Precio: {new_price}")
            cursor.execute("UPDATE productos SET precio=%s WHERE id=%s;", (new_price, producto[0]))

        conn.commit()
        flash("Descuento/aumento aplicado exitosamente.")
    except Exception as e:
        print(f"Error al aplicar descuento/aumento: {str(e)}")
        flash(f"Error al aplicar descuento/aumento: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    return redirect("/productos")

# Ruta para agregar un producto al pedido
@app.route('/add_to_cart_ped/<int:id>')
def add_to_cart_ped(id):
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
    return redirect("/productos")

# Actualizar lista de pedido
@app.route('/actualizar_cantidad_pedido/<int:id>/<int:cantidad>', methods=['POST'])
def actualizar_cantidad_pedido(id, cantidad):
    for item in pedido:
        if item['id'] == id:
            # Si está en el pedido, aumenta la cantidad
            item['cantidad'] = cantidad
            break
    return

@app.route('/actualizar_precio_pedido/<int:id>/<int:precio>', methods=['POST'])
def actualizar_precio_pedido(id, precio):
    for item in pedido:
        if item['id'] == id:
            # Si está en el pedido, aumenta la cantidad
            item['precio'] = precio
            break
    return

@app.route("/actualizar_pedido")
def actualizar_pedido():
    return redirect("/pedido") 

# Ruta para mostrar la pagina del pedido
@app.route("/pedido")
def mostrar_pedido():
    total = sum(item['precio'] * item['cantidad'] for item in pedido)

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener lista de clientes / proveedores desde la base de datos
    cursor.execute("SELECT id, nombre FROM clientes_proveedores WHERE tipo = 2;")
    proveedor_data = cursor.fetchall()

    conn.commit()

    return render_template("productos/pedido.html", pedido=pedido, total=total, proveedor_data = proveedor_data)

# Ruta para mostrar la lista de clientes
@app.route('/clientes')
def clientes():
    current_page = 'clientes'
    search = request.args.get("search")

    conn = mysql.connect()
    cursor = conn.cursor()

    # SQL para filtrada clientes por nombre o DNI
    if search:
        cursor.execute("SELECT * FROM clientes_proveedores WHERE nombre LIKE %s OR dni LIKE %s;", (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM clientes_proveedores;")

    clientes_data = cursor.fetchall()

    conn.commit()

    return render_template("clientes/clientes.html", current_page=current_page, clientes_data=clientes_data)

# Ruta para mostrar el formulario de agregar nuevo cliente
@app.route("/nuevo_cliente", methods=["GET"])
def nuevo_cliente():

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener los DNIs de los clientes
    cursor.execute("SELECT dni FROM clientes_proveedores WHERE dni > 0")
    DNIs = cursor.fetchall()

    listaDNIs.clear()
    for i in DNIs:
        listaDNIs.append(i[0])

    conn.commit()

    return render_template("clientes/nuevo_cliente.html", listaDNIs=listaDNIs)

# Ruta para agregar un nuevo cliente a la base de datos
@app.route("/agregar_cliente", methods=["POST"])
def agregar_cliente():
    _nombre = request.form["nombre"]
    _dni = request.form["dni"]
    _numero = request.form["numero"]
    _direccion = request.form["direccion"]
    _tipo = 1

    # Validacion de datos
    if not _nombre or not _dni or not _numero or not _direccion:
        flash("Todos los campos son obligatorios. Por favor, completa todos los campos.")
        return redirect("/nuevo_cliente")

    if int(_dni) in listaDNIs:
        mensaje = "El DNI ya existe"
        return render_template("clientes/nuevo_cliente.html", mensaje=mensaje)
    else:
            conn = mysql.connect()
            cursor = conn.cursor()

            # Insertar el nuevo cliente en la base de datos
            sql = "INSERT INTO `clientes_proveedores` (`nombre`, `dni`, `numero`, `direccion`, `tipo`) VALUES (%s, %s, %s, %s, %s);"
            datos = (_nombre, _dni, _numero, _direccion, _tipo)

            cursor.execute(sql, datos)
            conn.commit()

    return redirect("/clientes")

# Ruta para eliminar un cliente
@app.route("/eliminar_cliente/<int:id>")
def eliminar_cliente(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Eliminar el cliente con el ID proporcionado
    cursor.execute("DELETE FROM clientes_proveedores WHERE id=%s", (id,))
    conn.commit()
    return redirect("/clientes") 
    
# Ruta para mostrar el formulario de edicion de cliente
@app.route("/editar_cliente/<int:id>", methods=["GET"])
def editar_cliente(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener los datos del cliente con el ID proporcionado para editar
    cursor.execute("SELECT * FROM clientes_proveedores WHERE id=%s", (id,))
    cliente = cursor.fetchone()

    conn.commit()

    return render_template("clientes/editar_cliente.html", cliente=cliente)

# Ruta para actualizar los datos del cliente despues de editar
@app.route('/actualizar_cliente/<int:id>', methods=['POST'])
def actualizar_cliente(id):
    _nombre = request.form["nombre"]
    _dni = request.form["dni"]
    _cuit = request.form["cuit"]
    _numero = request.form["numero"]
    _direccion = request.form["direccion"]
    _saldo = request.form["saldo"]
    _tipo = request.form["tipo"]

    # Validacion de datos

    if not _nombre or not _dni or not _numero or not _direccion or not _cuit or not _saldo:
        flash("Todos los campos son obligatorios. Por favor, completa todos los campos.")
        return redirect(f"/editar_cliente/{id}")

    conn = mysql.connect()
    cursor = conn.cursor()

    # Actualizar los datos del cliente en la base de datos
    sql = "UPDATE `clientes_proveedores` SET `nombre`=%s, `dni`=%s, `numero`=%s, `direccion`=%s, `cuit`=%s, `saldo`=%s, `tipo`=%s WHERE `id`=%s;"
    datos = (_nombre, _dni, _numero, _direccion, _cuit, _saldo, _tipo, id)

    cursor.execute(sql, datos)
    conn.commit()

    flash("Cliente actualizado exitosamente.")
    return redirect("/clientes")

################################################################
# Ruta para mostrar la lista de proveedores
@app.route('/proveedores')
def proveedores():
    current_page = 'proveedores'
    search = request.args.get("search")

    conn = mysql.connect()
    cursor = conn.cursor()

    # SQL para filtrada proveedores por nombre o DNI
    if search:
        cursor.execute("SELECT * FROM clientes_proveedores WHERE nombre LIKE %s OR cuit LIKE %s;", (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM clientes_proveedores;")

    proveedores_data = cursor.fetchall()

    conn.commit()

    return render_template("proveedores/proveedores.html", current_page=current_page, proveedores_data=proveedores_data)

# Ruta para mostrar el formulario de agregar nuevo proveedor
@app.route("/nuevo_proveedor", methods=["GET"])
def nuevo_proveedor():

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener los DNIs de los proveedores
    cursor.execute("SELECT cuit FROM clientes_proveedores WHERE cuit > 0")
    DNIs = cursor.fetchall()

    listaCUITs.clear()
    for i in DNIs:
        listaCUITs.append(i[0])

    conn.commit()

    return render_template("proveedores/nuevo_proveedor.html")

# Ruta para agregar un nuevo proveedor a la base de datos
@app.route("/agregar_proveedor", methods=["POST"])
def agregar_proveedor():
    _nombre = request.form["nombre"]
    _cuit = request.form["cuit"]
    _numero = request.form["numero"]
    _direccion = request.form["direccion"]
    _tipo = 2

    # Validacion de datos
    if not _nombre or not _cuit or not _numero or not _direccion:
        flash("Todos los campos son obligatorios. Por favor, completa todos los campos.")
        return redirect("/nuevo_proveedor")

    if int(_cuit) in listaCUITs:
        mensaje = "El CUIT ya existe"
        return render_template("proveedores/nuevo_proveedor.html", mensaje=mensaje)
    else:
            conn = mysql.connect()
            cursor = conn.cursor()

            # Insertar el nuevo proveedor en la base de datos
            sql = "INSERT INTO `clientes_proveedores` (`nombre`, `cuit`, `numero`, `direccion`, `tipo`) VALUES (%s, %s, %s, %s, %s);"
            datos = (_nombre, _cuit, _numero, _direccion, _tipo)

            cursor.execute(sql, datos)
            conn.commit()

    return redirect("/proveedores")

# Ruta para eliminar un proveedor
@app.route("/eliminar_proveedor/<int:id>")
def eliminar_proveedor(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Eliminar el proveedor con el ID proporcionado
    cursor.execute("DELETE FROM clientes_proveedores WHERE id=%s", (id,))
    conn.commit()
    return redirect("/proveedores") 
    
# Ruta para mostrar el formulario de edicion de proveedor
@app.route("/editar_proveedor/<int:id>", methods=["GET"])
def editar_proveedor(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener los datos del proveedor con el ID proporcionado para editar
    cursor.execute("SELECT * FROM clientes_proveedores WHERE id=%s", (id,))
    proveedor = cursor.fetchone()

    conn.commit()

    return render_template("proveedores/editar_proveedor.html", proveedor=proveedor)

# Ruta para actualizar los datos del proveedor despues de editar
@app.route('/actualizar_proveedor/<int:id>', methods=['POST'])
def actualizar_proveedor(id):
    _nombre = request.form["nombre"]
    _dni = request.form["dni"]
    _cuit = request.form["cuit"]
    _numero = request.form["numero"]
    _direccion = request.form["direccion"]
    _saldo = request.form["saldo"]
    _tipo = request.form["tipo"]

    # Validacion de datos

    if not _nombre or not _dni or not _numero or not _direccion or not _cuit or not _saldo:
        flash("Todos los campos son obligatorios. Por favor, completa todos los campos.")
        return redirect(f"/editar_proveedor/{id}")

    conn = mysql.connect()
    cursor = conn.cursor()

    # Actualizar los datos del proveedor en la base de datos
    sql = "UPDATE `clientes_proveedores` SET `nombre`=%s, `dni`=%s, `numero`=%s, `direccion`=%s, `cuit`=%s, `saldo`=%s, `tipo`=%s WHERE `id`=%s;"
    datos = (_nombre, _dni, _numero, _direccion, _cuit, _saldo, _tipo, id)

    cursor.execute(sql, datos)
    conn.commit()

    flash("proveedor actualizado exitosamente.")
    return redirect("/proveedores")
################################################################


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

# Función para aumentar el stock de un producto
def aumentar_stock(producto_id, cantidad_comprada):
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT cantidad FROM productos WHERE id=%s", (producto_id,))
    stock_actual = cursor.fetchone()[0]

    nuevo_stock = stock_actual + cantidad_comprada

    cursor.execute("UPDATE productos SET cantidad=%s WHERE id=%s", (nuevo_stock, producto_id))
    conn.commit()

    conn.close()

#procesar compra
@app.route("/procesar_compra", methods=["POST"])
def procesar_compra():
    current_page = 'pedido'
    # Obtener la lista de productos y cantidades del pedido
    # lista_productos = ", ".join([f"{item['nombre']} (x{item['cantidad']})" for item in pedido])
    lista_productos = json.dumps(pedido)

    # Calcular el total de la compra
    total_compra = sum(item['precio'] * item['cantidad'] for item in pedido)

    # Obtener el nombre del proveedor seleccionado
    id_proveedor = request.form.get('id_proveedor')
    
    # Verificar si id_proveedor es None y manejarlo
    if id_proveedor is None:
        flash("Error: Selecciona un cliente.")
        return redirect("/pedido")

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener el nombre del proveedor a partir de su ID
    # cursor.execute("SELECT nombre FROM clientes_proveedores WHERE id=%s", (id_proveedor,))
    # resultado_cliente = cursor.fetchone()

    # Verificar si result_cliente es None y manejarlo
    # if resultado_cliente is None:
    #     flash("Error: Cliente no encontrado.")
    #     return redirect("/pedido")

    # nombre_cliente = resultado_cliente[0]

    # Obtener el monto pagado por el usuario desde el formulario
    monto_pagado = request.form.get('pago_a_proveedor')

    # Verificar si monto_pagado es None y manejarlo
    if monto_pagado is None:
        flash("Error: Ingresa el pago.")
        return redirect("/pedido")

    # Convertir monto_pagado a float
    try:
        monto_pagado = float(monto_pagado)
    except ValueError:
        flash("Error: Ingresa un monto pagado válido.")
        return redirect("/pedido")

    # Calcular la diferencia entre el total y el pago del cliente
    diferencia = monto_pagado - total_compra

    # Obtener el saldo actual del proveedor
    cursor.execute("SELECT saldo FROM clientes_proveedores WHERE id=%s", (id_proveedor,))
    saldo_actual = cursor.fetchone()[0]

    # Calcular el nuevo saldo sumando la diferencia
    nuevo_saldo = saldo_actual + diferencia

    # Obtener la fecha y hora de la transaccion
    fecha_hora = request.form.get('fecha_hora')

    # Tipo de movimiento 1 (compra)
    tipo = 1

    # Actualizar el saldo del proveedor en la base de datos
    cursor.execute("UPDATE clientes_proveedores SET saldo=%s WHERE id=%s", (nuevo_saldo, id_proveedor))
    conn.commit()

    # Insertar los datos en la tabla "detalles_compra"
    sql = "INSERT INTO detalles_compra (productos, total, pago, diferencia_cliente, id_cliente, tipo, fecha) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    datos = (lista_productos, total_compra, monto_pagado, diferencia, id_proveedor, tipo, fecha_hora)
    cursor.execute(sql, datos)
    conn.commit()

    # Aumentar el stock de los productos comprados
    for item in pedido:
        aumentar_stock(item['id'], item['cantidad'])

    # Actualizar la salida de los productos en la base de datos
    # for item in pedido:
    #     producto_id = item['id']
    #     cantidad_vendida = item['cantidad']

        # Obtener la salida actual del producto
        # cursor.execute("SELECT salida FROM productos WHERE id=%s", (producto_id,))
        # salida_actual = cursor.fetchone()[0]

        # Calcular la nueva salida sumando la cantidad vendida // MAMAAAA
        # nueva_salida = salida_actual + cantidad_vendida

        # Actualizar la salida del producto en la base de datos // MAMAAAA
        # cursor.execute("UPDATE productos SET salida=%s WHERE id=%s", (nueva_salida, producto_id))
        # conn.commit()

    # Limpiar el pedido despues de procesar la compra
    pedido.clear()

    flash("Compra procesada exitosamente.")
    return render_template("productos/pedido.html", current_page=current_page)

# Ruta para mostrar la pagina de la venta
@app.route("/orden_venta")
def mostrar_orden_venta():
    total = sum(item['precio'] * item['cantidad'] for item in lista_vta)

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener lista de clientes / proveedores desde la base de datos
    cursor.execute("SELECT id, nombre FROM clientes_proveedores WHERE tipo = 1;")
    cliente_data = cursor.fetchall()

    conn.commit()

    return render_template("compra_venta/orden_venta.html", lista_vta=lista_vta, total=total, cliente_data = cliente_data)

#procesar venta
@app.route("/procesar_venta", methods=["POST"])
def procesar_venta():
    current_page = 'orden_venta'
    # Obtener la lista de productos y cantidades de la venta
    # lista_productos = ", ".join([f"{item['nombre']} (x{item['cantidad']})" for item in lista_vta])
    lista_productos = json.dumps(lista_vta)

    # Calcular el total de la venta
    total_venta = sum(item['precio'] * item['cantidad'] for item in lista_vta)

    # Obtener el nombre del cliente seleccionado
    id_cliente = request.form.get('id_cliente')
    
    # Verificar si id_cliente es None y manejarlo
    if id_cliente is None:
        flash("Error: Selecciona un cliente.")
        return redirect("/orden_venta")

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener el nombre del cliente a partir de su ID
    # cursor.execute("SELECT nombre FROM clientes_proveedores WHERE id=%s", (id_cliente,))
    # resultado_cliente = cursor.fetchone()

    # Verificar si result_cliente es None y manejarlo
    # if resultado_cliente is None:
    #     flash("Error: Cliente no encontrado.")
    #     return redirect("/orden_venta")

    # nombre_cliente = resultado_cliente[0]

    # Obtener el monto pagado por el cliente desde el formulario
    monto_pagado = request.form.get('pago_cliente')

    # Verificar si monto_pagado es None y manejarlo
    if monto_pagado is None:
        flash("Error: Ingresa el monto pagado por el cliente.")
        return redirect("/orden_venta")

    # Convertir monto_pagado a float
    try:
        monto_pagado = float(monto_pagado)
    except ValueError:
        flash("Error: Ingresa un monto pagado válido.")
        return redirect("/orden_venta")

    # Calcular la diferencia entre el total y el pago del cliente
    diferencia = monto_pagado - total_venta

    # Obtener el saldo actual del cliente
    cursor.execute("SELECT saldo FROM clientes_proveedores WHERE id=%s", (id_cliente,))
    saldo_actual = cursor.fetchone()[0]

    # Calcular el nuevo saldo sumando la diferencia
    nuevo_saldo = saldo_actual + diferencia

    # Obtener la fecha y hora de la transaccion
    fecha_hora = request.form.get('fecha_hora')

    # Tipo de movimiento 2 (venta)
    tipo = 2

    # Actualizar el saldo del cliente en la base de datos
    cursor.execute("UPDATE clientes_proveedores SET saldo=%s WHERE id=%s", (nuevo_saldo, id_cliente))
    conn.commit()

    # Insertar los datos en la tabla "detalles_compra"
    sql = "INSERT INTO detalles_compra (productos, total, pago, diferencia_cliente, id_cliente, tipo, fecha) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    datos = (lista_productos, total_venta, monto_pagado, diferencia, id_cliente, tipo, fecha_hora)
    cursor.execute(sql, datos)
    conn.commit()

    # Restar el stock de los productos comprados
    for item in lista_vta:
        restar_stock(item['id'], item['cantidad'])

    # Actualizar la salida de los productos en la base de datos
    for item in lista_vta:
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

    # Limpiar la lista de venta despues de procesar la compra
    lista_vta.clear()

    flash("Compra procesada exitosamente.")
    return render_template("compra_venta/orden_venta.html")

# Ruta para mostrar el ranking de productos con filtro por tipo
@app.route("/ranking")
def ranking():
    current_page = 'ranking'
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

    lista_temp = []
    suma = 0
    for i in productos_ranking:
        lista_temp.append([i[8], i[1]])
        suma = suma + i[8]

    mas_vendido = heapq.nlargest(5, lista_temp)
    mas_vendido_total = suma

    conn.commit()

    # Totales vendidos
    cursor.execute("SELECT total, pago, tipo FROM detalles_compra;")
    totales = cursor.fetchall()

    # Consulta adicional para obtener los tipos disponibles
    cursor.execute("SELECT DISTINCT tipo FROM productos;")
    tipos = [tipo[0] for tipo in cursor.fetchall()]

    return render_template("productos/ranking.html", current_page=current_page, productos_ranking=productos_ranking, tipos=tipos, tipo_filtro=tipo_filtro, mas_vendido=mas_vendido, mas_vendido_total=mas_vendido_total)

# Ruta para resetear el ranking
@app.route('/reset_ranking', methods=['POST'])
def reset_ranking():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        # Restablecer el campo de salida de todos los productos a 0
        cursor.execute("UPDATE productos SET salida = 0;")

        conn.commit()
    except Exception as e:
        # Manejar la excepción (imprimir o registrar el error)
        print(f"Error al resetear el ranking: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    return redirect("/ranking")

# VENTA
# Ruta - Mostrar lista de productos con opciones de busqueda y filtrado
@app.route("/venta")
def venta():
    current_page = 'ventas'
    search = request.args.get("search")
    filterTipo = request.args.get("filterTipo")

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT tipo FROM productos;")
    tipos = [tipo[0] for tipo in cursor.fetchall()]

    cursor.execute("SELECT id, nombre, tipo, descripcion, cantidad, precio, marca, minimo, salida FROM productos;")
    productos = cursor.fetchall()

    conn.commit()

    # Orden de Venta
    total = sum(item['precio'] * item['cantidad'] for item in lista_vta)

    conn = mysql.connect()
    cursor = conn.cursor()

    # Obtener lista de clientes desde la base de datos
    cursor.execute("SELECT id, nombre FROM clientes_proveedores WHERE tipo = 1;")
    clientes_data = cursor.fetchall()

    conn.commit()

    return render_template("compra_venta/venta.html", current_page=current_page, productos=productos, search=search, filterTipo=filterTipo, tipos=tipos, lista_vta=lista_vta, total=total, clientes_data=clientes_data)

# Ruta - Agregar producto a la lista de venta
@app.route('/add_to_cart_vta/<int:id>')
def add_to_cart_vta(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos WHERE id=%s", (id,))
    producto = cursor.fetchone()

    # Verificar si el producto ya está en la lista
    for item in lista_vta:
        if item['id'] == id:
            # Si esta en la lista, aumenta la cantidad
            item['cantidad'] += 1
            break
    else:
        # Si no esta en la lista, agrega un nuevo elemento
        lista_vta.append({
            'id': id,
            'nombre': producto[1],
            'precio': producto[5],
            'cantidad': 1
        })

    conn.commit()
    return redirect("/venta")

# Actualizar lista de venta
@app.route('/actualizar_cantidad_venta/<int:id>/<int:cantidad>', methods=['POST'])
def actualizar_cantidad_venta(id, cantidad):
    for item in lista_vta:
        if item['id'] == id:
            # Si está en la venta, aumenta la cantidad
            item['cantidad'] = cantidad
            break
    return
@app.route("/actualizar_venta")
def actualizar_venta():
    return redirect("/orden_venta")

# Ruta para cancelar la venta
@app.route("/cancelar_venta")
def cancelar_venta():
    # Vaciar el pedido al hacer clic en "Cancelar Venta"
    lista_vta.clear()
    return redirect("/orden_venta")
@app.route("/cancelar_venta_in")
def cancelar_venta_in():
    # Vaciar el pedido al hacer clic en "Cancelar Venta"
    lista_vta.clear()
    return redirect("/venta")

# Ruta para cancelar el pedido
@app.route("/cancelar_pedido")
def cancelar_pedido():
    # Vaciar el pedido al hacer clic en "Cancelar compra" // en el caso de comprar productos para el local
    pedido.clear()
    return redirect("/pedido")
@app.route("/cancelar_pedido_in")
def cancelar_pedido_in():
    # Vaciar el pedido al hacer clic en "Cancelar compra" // en el caso de comprar productos para el local
    pedido.clear()
    return redirect("/productos")

@app.route('/realizar_pago/<int:id>', methods=['GET'])
def realizar_pago(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # conseguir info del cliente a partir del ID
    cursor.execute("SELECT id, nombre, saldo FROM clientes_proveedores WHERE id=%s", (id,))
    cliente = cursor.fetchone()

    conn.commit()
    conn.close()

    return render_template("clientes/realizar_pago.html", cliente=cliente)

@app.route('/procesar_pago/<int:id>', methods=['POST'])
def procesar_pago(id):
    # if request.method == 'POST':
    #     try:
    # Conseguir monto del formulario
    monto_pagado = float(request.form.get('monto'))

    conn = mysql.connect()
    cursor = conn.cursor()

    # conseguir info del cliente antes de realizar el pago
    cursor.execute("SELECT id, saldo, tipo FROM clientes_proveedores WHERE id=%s", (id,))
    cliente_info = cursor.fetchone()

    id_cliente = cliente_info[0]
    saldo_actual = cliente_info[1]
    tipo_cliente = cliente_info[2]

    # Calcula la nueva deuda sumando el monto pagado al saldo actual
    nueva_deuda = saldo_actual + monto_pagado

    # Tipo de movimiento 3 (pago deuda)
    tipo = 3
    
    sql = "INSERT INTO detalles_compra (productos, total, pago, diferencia_cliente, id_cliente, tipo) VALUES (%s, %s, %s, %s, %s, %s);"
    datos = ('Pago de saldo', saldo_actual, monto_pagado, nueva_deuda, id_cliente, tipo)
    cursor.execute(sql, datos)
    conn.commit()

    # Actualiza el saldo del cliente en la base de datos
    cursor.execute("UPDATE clientes_proveedores SET saldo=%s WHERE id=%s", (nueva_deuda, id))
    conn.commit()

        #     flash("Pago procesado exitosamente.")
        # except Exception as e:
        #     print(f"Error al procesar pago: {str(e)}")
        #     flash("Error al procesar el pago. Por favor, inténtalo de nuevo.")

        # finally:
    conn.close()

        # Redirige a la página principal de clientes después de procesar el pago
    if tipo_cliente == 1:
        return redirect("/clientes")
    else:
        return redirect("/proveedores")

#Info Clientes
@app.route('/ver_info_cliente/<int:id>', methods=['GET'])
def ver_info_cliente(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # conseguir info del cliente a partir del ID
    cursor.execute("SELECT * FROM clientes_proveedores WHERE id=%s", (id,))
    cliente = cursor.fetchone()

    # conseguir info de los movimientos del cliente a partir del ID
    cursor.execute("SELECT id, total, pago, diferencia_cliente, tipo, fecha  FROM detalles_compra WHERE id_cliente=%s", (id,))
    movimiento = cursor.fetchall()

    movimiento_list = list(movimiento)

    movimiento_list2 = []
    for i in movimiento_list:
        movimiento_list2.append(list(i))

    movimiento = movimiento_list2

    for i in movimiento:
        formateo = f'{i[0]:07}'
        i[0] = formateo

        # Dividir la cadena en partes
        partes = f'{i[5]}'.split(' ')

        # Dividir la parte de la fecha en año, mes y día
        anio, mes, dia = partes[0].split('-')

        # Formatear la nueva cadena
        i[5] = f"{dia}/{mes}/{anio} {partes[1]}"

    # conseguir info de las compras del cliente a partir del ID
    cursor.execute("SELECT productos FROM detalles_compra WHERE id_cliente=%s", (id,))
    compras_json_rows = cursor.fetchall()
    compras = []

    for row in compras_json_rows:
        compras_json = row[0]
        if compras_json == 'Pago de saldo':
            compras.append(compras_json)
        else:
            compras.append(json.loads(compras_json))

    movimientos =  zip(movimiento, compras)

    lista_temp = []
    for i in movimientos:
        lista_temp.insert(0, i)
    
    movimientos = lista_temp

    # conseguir la suma del total
    cursor.execute("SELECT SUM(total) FROM detalles_compra WHERE id_cliente=%s AND total >= 0", (id,))
    total = cursor.fetchone()[0]

    # conseguir la suma del total
    cursor.execute("SELECT SUM(pago) FROM detalles_compra WHERE id_cliente=%s", (id,))
    pago = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return render_template("clientes/info_cliente.html", cliente=cliente, movimientos=movimientos, total=total, pago=pago)

#Info Proveedores
@app.route('/ver_info_proveedores/<int:id>', methods=['GET'])
def ver_info_proveedores(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # conseguir info del proveedor a partir del ID
    cursor.execute("SELECT * FROM clientes_proveedores WHERE id=%s", (id,))
    proveedor = cursor.fetchone()

    # conseguir info de los movimientos del proveedor a partir del ID
    cursor.execute("SELECT id, total, pago, diferencia_cliente, tipo, fecha  FROM detalles_compra WHERE id_cliente=%s", (id,))
    movimiento = cursor.fetchall()

    movimiento_list = list(movimiento)

    movimiento_list2 = []
    for i in movimiento_list:
        movimiento_list2.append(list(i))

    movimiento = movimiento_list2
    
    for i in movimiento:
        formateo = f'{i[0]:07}'
        i[0] = formateo

        # Dividir la cadena en partes
        partes = f'{i[5]}'.split(' ')

        # Dividir la parte de la fecha en año, mes y día
        anio, mes, dia = partes[0].split('-')

        # Formatear la nueva cadena
        i[5] = f"{dia}/{mes}/{anio} {partes[1]}"

    # conseguir info de las compras al proveedor a partir del ID
    cursor.execute("SELECT productos FROM detalles_compra WHERE id_cliente=%s", (id,))
    compras_json_rows = cursor.fetchall()
    compras = []

    for row in compras_json_rows:
        compras_json = row[0]
        if compras_json == 'Pago de saldo':
            compras.append(compras_json)
        else:
            compras.append(json.loads(compras_json))

    movimientos =  zip(movimiento, compras)

    lista_temp = []
    for i in movimientos:
        lista_temp.insert(0, i)
    
    movimientos = lista_temp

    # conseguir la suma del total
    cursor.execute("SELECT SUM(total) FROM detalles_compra WHERE id_cliente=%s AND total >= 0", (id,))
    total = cursor.fetchone()[0]

    # conseguir la suma del total
    cursor.execute("SELECT SUM(pago) FROM detalles_compra WHERE id_cliente=%s", (id,))
    pago = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return render_template("proveedores/info_proveedor.html", proveedor=proveedor, movimientos=movimientos, total=total, pago=pago)

#Info Proveedores
@app.route('/info_compra_venta', methods=['GET'])
def info_compra_venta():
    conn = mysql.connect()
    cursor = conn.cursor()

    # conseguir info del proveedor_cliente // No necesario por ahora
    cursor.execute("SELECT * FROM clientes_proveedores")
    proveedor_cliente = cursor.fetchone()

    # conseguir info de los movimientos del proveedor_cliente
    cursor.execute("SELECT id, total, pago, diferencia_cliente, tipo, fecha, id_cliente FROM detalles_compra")
    movimiento = cursor.fetchall()

    movimiento_list = list(movimiento)

    movimiento_list2 = []
    for i in movimiento_list:
        movimiento_list2.append(list(i))

    movimiento = movimiento_list2
    
    for i in movimiento:
        formateo = f'{i[0]:07}'
        i[0] = formateo

        # Dividir la cadena en partes
        partes = f'{i[5]}'.split(' ')

        # Dividir la parte de la fecha en año, mes y día
        anio, mes, dia = partes[0].split('-')

        # Formatear la nueva cadena
        i[5] = f"{dia}/{mes}/{anio} {partes[1]}"

    # conseguir info de las compras al proveedor_cliente a partir del ID
    cursor.execute("SELECT productos FROM detalles_compra")
    compras_json_rows = cursor.fetchall()
    compras = []

    for row in compras_json_rows:
        compras_json = row[0]
        if compras_json == 'Pago de saldo':
            compras.append(compras_json)
        else:
            compras.append(json.loads(compras_json))

    movimientos =  zip(movimiento, compras)

    lista_temp = []
    for i in movimientos:
        lista_temp.insert(0, i)
    
    movimientos = lista_temp

    # Totales compras y ventas

    # COMPRAS
    # conseguir la suma del total
    cursor.execute("SELECT SUM(total) FROM detalles_compra WHERE tipo=%s AND total >= 0", (1,))
    compra_total = cursor.fetchone()[0]

    # conseguir la suma del total
    cursor.execute("SELECT SUM(pago) FROM detalles_compra WHERE tipo=%s", (1,))
    compra_pago = cursor.fetchone()[0]

    # VENTAS
    # conseguir la suma del total
    cursor.execute("SELECT SUM(total) FROM detalles_compra WHERE tipo=%s AND total >= 0", (2,))
    venta_total = cursor.fetchone()[0]

    # conseguir la suma del total
    cursor.execute("SELECT SUM(pago) FROM detalles_compra WHERE tipo=%s", (2,))
    venta_pago = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return render_template("productos/info_compra_venta.html", proveedor_cliente=proveedor_cliente, movimientos=movimientos, compra_total=compra_total, compra_pago=compra_pago, venta_total=venta_total, venta_pago=venta_pago)

# Iniciar la aplicacion Flask
if __name__ == "__main__":
    app.run(debug=True)