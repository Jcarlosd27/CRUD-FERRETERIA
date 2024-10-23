# BIENVENIDOS A MI PRIMER PROYECTO CON PYTHON, ESPECIALIZADO EN LA GESTION LOGISTICA DE INVENTARIOS PARA EL AREA AGROINDUSTRIAL

Este proyecto es una aplicación POS (Punto de Venta) para una ferretería. Está desarrollada en Python con Flask y SQL, y cuenta con un sistema de administración de productos, clientes y ventas.

## Pasos para ejecutar el programa

Para ejecutar este programa, sigue los siguientes pasos:

1. Abre la consola de comandos (CMD) presionando `Windows + R` y escribiendo `cmd`.

2. Dentro del CMD, navega hasta la carpeta donde se encuentra el proyecto **WULLKAN**. En este ejemplo, se encuentra en la carpeta de descargas.

   ```bash
   # Cambiar al directorio de Descargas
   cd Downloads

   # Cambiar al directorio del proyecto
   cd wullkan

   # Activar el entorno virtual
   pos_ferreteria_env\Scripts\activate

   # Cambiar al directorio principal del proyecto
   cd pos_ferreteria

   # Ejecutar la aplicación con Flask
   flask run
### ------------------------------ SECCIONES ---------------------------------------
## Estructura del Proyecto y Funcionalidades

### 1. Sección de Clientes

**Funcionalidades:**
- Permite registrar nuevos clientes desde la plantilla `new_client.html`.
- Permite editar y listar clientes existentes con la vista `clients.html`.
- Incluye campos como nombre de la empresa, RUT, dirección, contactos, y más.

**Archivos Relacionados:**
- `clients.html`: Página para listar y editar los clientes.
- `new_client.html`: Formulario para registrar un nuevo cliente.

### 2. Sección de Productos

**Funcionalidades:**
- Permite agregar, editar y listar productos con detalles como nombre, SKU, precio, stock, e imagen.
- Incluye la funcionalidad de editar productos desde la plantilla `edit_product.html`.

**Archivos Relacionados:**
- `products.html`: Página para listar todos los productos.
- `new_product.html`: Formulario para agregar un nuevo producto.
- `edit_product.html`: Formulario para editar un producto existente.

### 3. Sección de Ventas

**Funcionalidades:**
- Registro de nuevas ventas con detalles de los productos seleccionados.
- Generación de reportes de ventas.

**Archivos Relacionados:**
- `sales.html`: Página para listar las ventas.
- `new_sale.html`: Formulario para registrar una nueva venta.
- `report_sales.html`: Vista para generar y visualizar reportes de ventas.

### 4. Gestión de Usuarios

**Funcionalidades:**
- Registro de nuevos usuarios desde la plantilla `register.html`.
- Iniciar sesión y gestionar perfiles de usuario.

**Archivos Relacionados:**
- `login.html`: Formulario de inicio de sesión.
- `register.html`: Formulario de registro de nuevos usuarios.
- `profile.html`: Página para ver y editar el perfil del usuario.

### 5. Dashboard

**Funcionalidades:**
- Proporciona una visión general del sistema, mostrando información resumida de productos, ventas, y clientes.

**Archivos Relacionados:**
- `dashboard.html`: Página principal que muestra el resumen de las operaciones.

### 6. Archivos y Directorios Clave

- **`app/`**: Contiene la lógica principal de la aplicación.
- **`static/`**: Carpeta para archivos estáticos (imágenes, estilos).
- **`templates/`**: Carpeta con todos los archivos HTML para las vistas (clientes, productos, ventas, etc.).
- **`config.py`**: Archivo de configuración de la aplicación.
- **`forms.py`**: Definición de formularios para productos, clientes y usuarios.
- **`models.py`**: Definición de los modelos de la base de datos.
- **`routes.py`**: Rutas y lógica para las diferentes vistas y operaciones del sistema.
- **`run.py`**: Archivo principal para ejecutar la aplicación Flask.
