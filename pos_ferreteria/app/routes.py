import base64
from cgi import FieldStorage
import csv
import io
import os
import re
from datetime import datetime, timezone
from decimal import Decimal
from functools import wraps
from io import BytesIO
from sqlite3 import IntegrityError
import pandas as pd
import pdfkit
import qrcode
from flask import (
    Blueprint, abort, current_app, flash, json, jsonify, make_response, redirect, render_template,
    request, send_file, send_from_directory, url_for
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from .datos_comunas import obtener_comunas_por_region
from . import bcrypt, db
from .forms import (
    ClientForm, ClientImportForm, DeleteForm, DeleteRoleForm, LoginForm, ProductForm, RegistrationForm, 
    SaleForm, UpdateProfileForm, WorkerForm, UserForm, RoleForm, DeleteRoleForm
)
from .models import Client, Product, Transaction, User, Worker, Role  # Asegúrate de tener los modelos correctos
from app.creditos_dias import CREDITOS_APROBADOS_DIAS
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from .phone_format import format_chilean_phone_number,  format_chilean_telephone_number  # Importa la función

main = Blueprint('main', __name__)

#--------------------------------------------- ROLES -----------------------------------------

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role is None:
                flash('No tienes rol asignado.', 'danger')
                return redirect(url_for('main.home'))
            
            permissions_list = [p.strip() for p in current_user.role.permissions.split(',')]
            if permission not in permissions_list:
                flash('No tienes permiso para acceder a esta página.', 'danger')
                return redirect(url_for('main.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator



# Asegúrate de instanciar este formulario en tu ruta
@main.route('/roles', methods=['GET'])
@login_required
@permission_required('view_roles')
def list_roles():
    roles = Role.query.all()
    form = DeleteRoleForm()  # Crea una instancia del formulario
    return render_template('roles.html', roles=roles, form=form)

# Ruta para crear un nuevo rol
@main.route('/role/new', methods=['GET', 'POST'])
@login_required
@permission_required('create_role')
def new_role():
    form = RoleForm()  # Usamos el mismo formulario de RoleForm para mantener la consistencia

    # Definimos las opciones de permisos disponibles
    form.permissions.choices = [
        ('view_roles', 'Ver Roles'),
        ('create_role', 'Crear Rol'),
        ('edit_role', 'Editar Rol'),
        ('delete_role', 'Eliminar Rol'),
        ('view_users', 'Ver Usuarios'),
        ('view_users2', 'Ver Usuarios Alternativos'),
        ('create_user', 'Crear Usuario'),
        ('edit_user', 'Editar Usuario'),
        ('delete_user', 'Eliminar Usuario'),
        ('view_workers', 'Ver Trabajadores'),
        ('create_worker', 'Crear Trabajador'),
        ('edit_worker', 'Editar Trabajador'),
        ('delete_worker', 'Eliminar Trabajador'),
        ('import_worker', 'Importar Trabajador'),
        ('view_products', 'Ver Productos'),
        ('create_product', 'Crear Producto'),
        ('edit_product', 'Editar Producto'),
        ('delete_product', 'Eliminar Producto'),
        ('download_pdf_product', 'Descargar PDF de Producto'),
        ('import_product', 'Importar Producto'),
        ('view_clients', 'Ver Clientes'),
        ('create_client', 'Crear Cliente'),
        ('edit_client', 'Editar Cliente'),
        ('delete_client', 'Eliminar Cliente'),
        ('import_client', 'Importar Cliente'),
        ('view_sales', 'Ver Ventas'),
        ('create_sale', 'Crear Venta'),
        ('edit_profile', 'Editar Perfil')
    ]

    if form.validate_on_submit():
        # Crear el nuevo rol con los permisos seleccionados
        role_name = form.name.data
        permissions = ','.join(form.permissions.data)

        role = Role(name=role_name, permissions=permissions)
        db.session.add(role)
        db.session.commit()

        flash('Rol creado con éxito.', 'success')
        return redirect(url_for('main.list_roles'))

    return render_template('new_role.html', form=form)


# Ruta para EDITAR un rol vigente
@main.route('/role/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit_role')
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)  # Obtener el rol por ID
    form = RoleForm(obj=role)  # Cargar los datos del rol en el formulario

    # Asignar las opciones al campo de permisos
    form.permissions.choices = [
    ('view_roles', 'Ver Roles'),
    ('create_role', 'Crear Rol'),
    ('edit_role', 'Editar Rol'),
    ('delete_role', 'Eliminar Rol'),
    ('view_users', 'Ver Usuarios'),
    ('view_users2', 'Ver Usuarios Alternativos'),
    ('create_user', 'Crear Usuario'),
    ('edit_user', 'Editar Usuario'),
    ('delete_user', 'Eliminar Usuario'),
    ('view_workers', 'Ver Trabajadores'),
    ('create_worker', 'Crear Trabajador'),
    ('edit_worker', 'Editar Trabajador'),
    ('delete_worker', 'Eliminar Trabajador'),
    ('import_worker', 'Importar Trabajador'),
    ('view_products', 'Ver Productos'),
    ('create_product', 'Crear Producto'),
    ('edit_product', 'Editar Producto'),
    ('delete_product', 'Eliminar Producto'),
    ('download_pdf_product', 'Descargar PDF de Producto'),
    ('import_product', 'Importar Producto'),
    ('view_clients', 'Ver Clientes'),
    ('create_client', 'Crear Cliente'),
    ('edit_client', 'Editar Cliente'),
    ('delete_client', 'Eliminar Cliente'),
    ('import_client', 'Importar Cliente'),
    ('view_sales', 'Ver Ventas'),
    ('create_sale', 'Crear Venta'),
    ('edit_profile', 'Editar Perfil')
]

    # Preseleccionar los permisos asignados al rol actual
    if request.method == 'GET':
        form.permissions.data = role.permissions.split(',')

    if form.validate_on_submit():
        role.name = form.name.data
        role.permissions = ','.join(form.permissions.data)  # Guardar los permisos como cadena separada por comas
        db.session.commit()
        flash('Rol actualizado con éxito.', 'success')
        return redirect(url_for('main.list_roles'))

    return render_template('edit_role.html', form=form, role=role)


# Ruta para eliminar un rol
@main.route('/role/delete/<int:role_id>', methods=['POST'])
@login_required
@permission_required('delete_role')
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)  # Buscar el rol por ID

    form = DeleteRoleForm()

    if form.validate_on_submit():  # Verificar token CSRF
        db.session.delete(role)
        db.session.commit()
        flash('Rol eliminado con éxito.', 'success')
        return redirect(url_for('main.list_roles'))

    flash('Error al intentar eliminar el rol.', 'danger')
    return redirect(url_for('main.list_roles'))



#################################################################################################
#################################################################################################
#################################################################################################

#--------------------------------------------- USUARIOS -----------------------------------------


# Ruta para registrar un nuevo usuario
@main.route("/register", methods=['GET', 'POST'])
@login_required
@permission_required('view_users2')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    roles = Role.query.all()  # Obtener todos los roles disponibles
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user_role = Role.query.filter_by(name='client').first()  # Asignar rol predeterminado (client)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=user_role)
        db.session.add(user)
        db.session.commit()
        flash('Cuenta creada con éxito. ¡Ya puedes iniciar sesión!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form, roles=roles)

# Ruta para iniciar sesión
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Has iniciado sesión con éxito', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Inicio de sesión fallido. Verifica tu correo y contraseña.', 'danger')
    return render_template('login.html', form=form)

# Ruta para cerrar sesión
@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# Ruta principal
@main.route("/home")
@login_required
def home():
    sales_data = {}  # Tu lógica para obtener los datos de ventas
    credit_data = {
        'total_credit': 5000000,  # Ejemplo de valor
        'used_credit': 800000      # Ejemplo de valor
    }
    return render_template('home.html', sales_data=sales_data, credit_data=credit_data)


#------------------------------------- GESTIÓN DE USUARIOS --------------------------------------

# Ruta para listar usuarios
@main.route('/users', methods=['GET'])
@login_required
@permission_required('view_users')
def list_users():
    users = User.query.all()
    delete_form = DeleteForm()  # Asegúrate de tener este formulario aquí
    return render_template('users.html', users=users, form=delete_form)  # Pasa el formulario a la plantilla

# Ruta para registrar un nuevo usuario
@main.route("/user/new", methods=['GET', 'POST'])
@login_required
@permission_required('create_user')
def new_user():
    form = RegistrationForm()
    form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]  # Cargar roles

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role_id=form.role_id.data)
        db.session.add(user)
        db.session.commit()
        flash('Usuario creado con éxito.', 'success')
        return redirect(url_for('main.list_users'))  # Redirigir a la lista de usuarios

    return render_template('new_user.html', form=form)  # Renderizar el formulario

# Ruta para editar un usuario
@main.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit_user')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    roles = Role.query.all()  # Obtener todos los roles disponibles

    # Rellenar el campo de selección de roles
    form.role_id.choices = [(role.id, role.name) for role in roles]  # Asegúrate de que choices no sea None

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
        user.role = Role.query.get(form.role_id.data)  # Actualizar rol dinámicamente
        db.session.commit()
        flash('Usuario actualizado con éxito.', 'success')
        return redirect(url_for('main.list_users'))

    return render_template('edit_user.html', form=form, user=user, roles=roles)

# Ruta para eliminar un usuario
@main.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
@permission_required('delete_user')

def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado con éxito.', 'success')
    return redirect(url_for('main.list_users'))


# ------------------------------------ FIN DEL CÓDIGO -------------------------------------------
#################################################################################################
#################################################################################################
#################################################################################################
#-------------------------- SECCION DE LOGICA PARA LOS TRABAJADORES --------------------------------
# Función para validar archivos de trabajadores
def allowed_worker_file(filename):
    allowed_extensions = ['jpg', 'jpeg', 'png']  # Extensiones permitidas para trabajadores
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Función para limpiar nombres de archivos (solo para trabajadores)
def clean_worker_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

# Ruta para listar trabajadores
@main.route("/workers")
@login_required
@permission_required('view_workers')
def workers():
    workers = Worker.query.all()
    delete_form = DeleteForm()  # Instancia del formulario de eliminación
    return render_template('workers.html', workers=workers, form=delete_form)

# Ruta para añadir un nuevo trabajador
@main.route("/worker/new", methods=['GET', 'POST'])
@login_required
@permission_required('create_worker')
def new_worker():
    form = WorkerForm()
    if form.validate_on_submit():
        try:
            photo_filename = None
            upload_folder = os.path.join(current_app.root_path, 'static/uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            if form.photo.data:
                if not allowed_worker_file(form.photo.data.filename):
                    flash('Formato de imagen no permitido. Solo se permiten archivos jpg, jpeg y png.', 'danger')
                    return redirect(url_for('main.new_worker'))

                # Limpiar el nombre del archivo de la foto
                photo_filename = f"worker_{clean_worker_filename(form.name.data)}.jpg"
                form.photo.data.save(os.path.join(upload_folder, photo_filename))

            # Formatear el número de teléfono antes de guardarlo
            formatted_phone = format_chilean_phone_number(form.phone.data)

            # Verificar si el número de teléfono es válido
            if "Número inválido" in formatted_phone:
                flash(formatted_phone, 'danger')
                return redirect(url_for('main.new_worker'))

            worker = Worker(
                name=form.name.data,
                position=form.position.data,
                phone=formatted_phone,  # Usar el número formateado
                email=form.email.data,
                photo=photo_filename
            )
            db.session.add(worker)
            db.session.commit()
            flash('Trabajador añadido con éxito', 'success')
            return redirect(url_for('main.workers'))
        except Exception as e:
            flash(f'Ocurrió un error al añadir el trabajador: {e}', 'danger')
    return render_template('new_worker.html', form=form)


@main.route("/worker/edit/<int:worker_id>", methods=['GET', 'POST'])
@login_required
@permission_required('edit_worker')
def edit_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    form = WorkerForm(obj=worker)

    if form.validate_on_submit():
        try:
            # Asignar los datos del formulario a los atributos del trabajador
            worker.name = form.name.data
            worker.position = form.position.data
            # Formatear el número de teléfono antes de asignarlo
            formatted_phone = format_chilean_phone_number(form.phone.data)

            # Verificar si el número de teléfono es válido
            if "Número inválido" in formatted_phone:
                flash(formatted_phone, 'danger')
                return redirect(url_for('main.edit_worker', worker_id=worker_id))
            
            worker.phone = formatted_phone  # Usar el número formateado
            worker.email = form.email.data

            upload_folder = os.path.join(current_app.root_path, 'static/uploads')
            # Verificar si se ha subido una nueva foto
            if form.photo.data:
                if isinstance(form.photo.data, FileStorage):  # Verifica que sea un FileStorage
                    if allowed_worker_file(form.photo.data.filename):  # Usa la función de validación
                        # Eliminar la foto anterior si existe
                        if worker.photo:
                            old_photo_path = os.path.join(upload_folder, worker.photo)
                            if os.path.exists(old_photo_path):
                                os.remove(old_photo_path)

                        # Limpiar y guardar el nuevo nombre de archivo
                        photo_filename = f"worker_{clean_worker_filename(form.name.data)}.jpg"
                        form.photo.data.save(os.path.join(upload_folder, photo_filename))
                        worker.photo = photo_filename  # Asignar el nuevo nombre de foto
                    else:
                        flash('Formato de imagen no permitido. Solo se permiten archivos jpg, jpeg y png.', 'danger')
                        return redirect(url_for('main.edit_worker', worker_id=worker_id))
                else:
                    flash('No se ha seleccionado un archivo válido.', 'danger')

            db.session.commit()  # Guardar los cambios en la base de datos
            flash('Trabajador actualizado con éxito', 'success')
            return redirect(url_for('main.workers'))  # Redirigir a la lista de trabajadores
        except Exception as e:
            db.session.rollback()  # Revertir cambios en caso de error
            flash(f'Ocurrió un error al actualizar el trabajador: {e}', 'danger')

    return render_template('edit_worker.html', form=form, worker=worker)  # Renderizar la plantilla para editar

# Ruta para eliminar un trabajador
@main.route("/worker/delete/<int:worker_id>", methods=['POST'])
@login_required
@permission_required('delete_worker')
def delete_worker(worker_id):
    try:
        worker = Worker.query.get_or_404(worker_id)

        # Eliminar la foto asociada al trabajador, si existe
        if worker.photo:
            photo_path = os.path.join(current_app.root_path, 'static/uploads', worker.photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)

        # Eliminar el trabajador de la base de datos
        db.session.delete(worker)
        db.session.commit()
        flash('Trabajador eliminado con éxito.', 'success')
    except Exception as e:
        flash(f'Ocurrió un error al eliminar el trabajador: {e}', 'danger')

    return redirect(url_for('main.workers'))

# Ruta para importar trabajadores desde un archivo Excel o CSV
@main.route('/import_workers', methods=['POST'])
@login_required
@permission_required('import_worker')
def import_workers():
    if 'excel_file' not in request.files:
        flash('No se ha seleccionado ningún archivo.', 'danger')
        return redirect(url_for('main.workers'))

    file = request.files['excel_file']

    if file.filename == '':
        flash('No se ha seleccionado ningún archivo.', 'danger')
        return redirect(url_for('main.workers'))

    if file and allowed_file(file.filename, ['xlsx', 'xls', 'csv']):
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)  # Leer archivo CSV
            else:
                df = pd.read_excel(file)  # Leer archivo Excel

            for index, row in df.iterrows():
                worker = Worker(
                    name=row['Nombre'],
                    position=row['Cargo'],
                    phone=row.get('Teléfono', None),
                    email=row['Correo'],
                    photo=row.get('Foto', None)  # Suponiendo que hay una columna de foto
                )
                db.session.add(worker)

            db.session.commit()
            flash('Trabajadores importados con éxito.', 'success')

        except Exception as e:
            flash(f'Error al importar los trabajadores: {e}', 'danger')
            db.session.rollback()
    else:
        flash('Formato de archivo no permitido. Solo se permiten archivos Excel o CSV.', 'danger')

    return redirect(url_for('main.workers'))

# ------------------------------------ FIN DEL CÓDIGO -------------------------------------------
#################################################################################################
#################################################################################################
#################################################################################################
#-------------------------- SECCION DE LOGICA PARA LOS PRODUCTOS --------------------------------
# Función para validar archivos
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Función para limpiar nombres de archivos
def clean_filename(name, sku):
    product_name_cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
    sku_cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '_', sku)
    return product_name_cleaned, sku_cleaned

# Ruta para productos
@main.route("/products", methods=['GET'])
@login_required
@permission_required('view_products')
def products():
    products = Product.query.all()
    delete_form = DeleteForm()  # Instancia del formulario de eliminación
    return render_template('products.html', products=products, form=delete_form)

@main.route("/product/new", methods=['GET', 'POST'])
@login_required
@permission_required('create_product')
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        try:
            image_filename = None
            pdf_filename = None

            # Asegurar que el directorio de uploads existe
            upload_folder = os.path.join(current_app.root_path, 'static/uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Limpiar nombres de archivos
            product_name_cleaned, sku_cleaned = clean_filename(form.name.data, form.sku.data)

            # Manejo de la imagen
            if form.image.data:
                if not allowed_file(form.image.data.filename, ['jpg', 'jpeg', 'png']):
                    flash('Formato de imagen no permitido. Solo jpg, jpeg y png.', 'danger')
                    return redirect(url_for('main.new_product'))

                image_filename = f"img_{sku_cleaned}_{product_name_cleaned}.jpg"
                form.image.data.save(os.path.join(upload_folder, image_filename))

            # Manejo del PDF
            if form.pdf.data:
                if not allowed_file(form.pdf.data.filename, ['pdf']):
                    flash('Formato no permitido. Solo PDF.', 'danger')
                    return redirect(url_for('main.new_product'))

                pdf_filename = f"doc_{sku_cleaned}_{product_name_cleaned}.pdf"
                form.pdf.data.save(os.path.join(upload_folder, pdf_filename))

            # Crear el producto con la cantidad mínima para precio por mayor
            product = Product(
                name=form.name.data,
                sku=form.sku.data,
                image=image_filename,
                stock=form.stock.data,
                min_stock=form.min_stock.data,
                sale_price=form.sale_price.data,
                bulk_price=form.bulk_price.data,
                bulk_quantity=form.bulk_quantity.data,  # Nuevo campo
                pdf=pdf_filename
            )
            db.session.add(product)
            db.session.commit()
            flash('Producto añadido con éxito', 'success')
            return redirect(url_for('main.products'))
        except Exception as e:
            flash(f'Ocurrió un error al añadir el producto: {e}', 'danger')

    return render_template('new_product.html', form=form)


@main.route("/product/edit/<int:product_id>", methods=['GET', 'POST'])
@login_required
@permission_required('edit_product')
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        try:
            # Asignar valores del formulario al producto
            product.name = form.name.data
            product.sku = form.sku.data
            product.stock = form.stock.data
            product.min_stock = form.min_stock.data
            product.sale_price = form.sale_price.data
            product.bulk_price = form.bulk_price.data
            product.bulk_quantity = form.bulk_quantity.data

            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Manejo de la imagen
            if form.image.data and hasattr(form.image.data, 'filename'):
                if allowed_file(form.image.data.filename, ['jpg', 'jpeg', 'png']):
                    # Eliminar imagen anterior si existe
                    if product.image:
                        old_image_path = os.path.join(upload_folder, product.image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)

                    # Guardar nueva imagen
                    image_filename = f"img_{product.sku}_{product.name}.jpg"
                    form.image.data.save(os.path.join(upload_folder, image_filename))
                    product.image = image_filename

            # Manejo del PDF
            if form.pdf.data and hasattr(form.pdf.data, 'filename'):
                if allowed_file(form.pdf.data.filename, ['pdf']):
                    # Eliminar PDF anterior si existe
                    if product.pdf:
                        old_pdf_path = os.path.join(upload_folder, product.pdf)
                        if os.path.exists(old_pdf_path):
                            os.remove(old_pdf_path)

                    # Guardar nuevo PDF
                    pdf_filename = f"doc_{product.sku}_{product.name}.pdf"
                    form.pdf.data.save(os.path.join(upload_folder, pdf_filename))
                    product.pdf = pdf_filename

            # Guardar cambios en la base de datos
            db.session.commit()
            flash('Producto actualizado con éxito', 'success')
            return redirect(url_for('main.products'))

        except Exception as e:
            flash(f'Ocurrió un error al actualizar el producto: {e}', 'danger')

    return render_template('edit_product.html', form=form, product=product)


@main.route("/product/delete/<int:product_id>", methods=['POST'])
@login_required
@permission_required('delete_product')
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        # Eliminar la imagen asociada al producto, si existe
        if product.image:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], product.image)
            if os.path.exists(image_path):
                os.remove(image_path)

        # Eliminar el archivo PDF asociado al producto, si existe
        if product.pdf:
            pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], product.pdf)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        # Eliminar el producto de la base de datos
        db.session.delete(product)
        db.session.commit()
        flash('Producto eliminado con éxito.', 'success')
    except Exception as e:
        flash(f'Ocurrió un error al eliminar el producto: {e}', 'danger')
    
    return redirect(url_for('main.products'))


@main.route("/product/download_pdf/<int:product_id>")
@login_required
@permission_required('download_pdf_product')
def download_pdf(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        # Verificar si el producto tiene un PDF asociado
        if not product.pdf:
            flash('No hay PDF adjunto para este producto.', 'warning')
            return redirect(url_for('main.products'))

        # Ruta al archivo PDF
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], product.pdf)
        
        # Verificar si el archivo existe
        if os.path.exists(pdf_path):
            return send_from_directory(current_app.config['UPLOAD_FOLDER'], product.pdf, as_attachment=True)
        else:
            flash('El archivo PDF no existe en el servidor.', 'danger')
            return redirect(url_for('main.products'))
    except Exception as e:
        flash(f'Ocurrió un error al descargar el archivo: {e}', 'danger')
        return redirect(url_for('main.products'))

# -------------- Importación de productos desde un archivo Excel -------------------------
@main.route("/product/import", methods=['POST'])
@login_required
@permission_required('import_product')
def import_products():
    if 'excel_file' not in request.files:
        flash('No se ha seleccionado ningún archivo.', 'danger')
        return redirect(url_for('main.products'))

    file = request.files['excel_file']

    if file.filename == '':
        flash('No se ha seleccionado ningún archivo.', 'danger')
        return redirect(url_for('main.products'))

    if file and allowed_file(file.filename, ['xlsx', 'xls']):
        try:
            # Leer el archivo Excel
            df = pd.read_excel(file)

            # Validar si las columnas necesarias existen
            required_columns = {'Nombre', 'SKU', 'Stock', 'Precio de Venta', 'Precio por Mayor'}
            missing_columns = required_columns - set(df.columns)
            if missing_columns:
                flash(f'El archivo Excel no contiene las siguientes columnas requeridas: {", ".join(missing_columns)}.', 'danger')
                return redirect(url_for('main.products'))

            # Recorrer las filas y añadir los productos a la base de datos
            for index, row in df.iterrows():
                product = Product(
                    name=row['Nombre'],
                    sku=row['SKU'],
                    stock=row['Stock'],
                    min_stock=row.get('Stock Mínimo', 0),  # Valor predeterminado 0 si no se proporciona
                    sale_price=row['Precio de Venta'],
                    bulk_price=row['Precio por Mayor'],
                    bulk_quantity=row.get('Cantidad Mínima para Precio por Mayor', 1)  # Valor predeterminado 1 si no existe la columna
                )
                db.session.add(product)

            db.session.commit()
            flash('Productos importados con éxito.', 'success')

        except IntegrityError as e:
            db.session.rollback()
            if "UNIQUE constraint failed" in str(e.orig):
                flash(f'Error: El SKU "{row["SKU"]}" ya existe en la base de datos.', 'danger')
            else:
                flash(f'Error de integridad al importar productos: {e}', 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al importar los productos: {e}', 'danger')

    else:
        flash('Formato de archivo no permitido. Solo se permiten archivos Excel (.xlsx, .xls).', 'danger')

    return redirect(url_for('main.products'))


# ------------------------------------ FIN DEL CÓDIGO -------------------------------------------
#################################################################################################
#################################################################################################
#################################################################################################
# ----------------------------------- SECCIÓN DE LÓGICA PARA CLIENTES ---------------------------

# Ruta para la lista de clientes
@main.route("/clients")
@login_required
@permission_required('view_clients')
def clients():
    clients = Client.query.all()  # Obtener todos los clientes
    delete_form = DeleteForm()  # Instancia del formulario de eliminación
    import_form = ClientImportForm()  # Instancia del formulario de importación
    return render_template('clients.html', clients=clients, delete_form=delete_form, import_form=import_form)

# Ruta para agregar un nuevo cliente
@main.route("/client/new", methods=['GET', 'POST'])
@login_required
@permission_required('create_client')
def new_client():
    form = ClientForm()  # Instancia del formulario para agregar cliente
    
    # Actualizar las comunas según la región seleccionada
    if form.region.data:
        form.actualizar_comunas(form.region.data)
    
    if form.validate_on_submit():
        try:
            # Formatear los números de contacto
            formatted_mobile_number = format_chilean_phone_number(form.contact_number.data)
            formatted_landline_number = format_chilean_telephone_number(form.landline.data)

            # Crear una nueva instancia de cliente
            client = Client(
                company_name=form.company_name.data,
                rut=form.rut.data,
                legal_representative=form.legal_representative.data,
                address=form.address.data,
                commune=form.commune.data,
                region=form.region.data,
                contact_number=formatted_mobile_number,  # Usa el número de contacto formateado
                landline=formatted_landline_number,      # Usa el número fijo formateado
                approved_credit_amount=form.approved_credit_amount.data,
                approved_credit_days=form.approved_credit_days.data,
                branch=form.branch.data,
                associated_seller=form.associated_seller.data
            )
            db.session.add(client)
            db.session.commit()
            flash('Cliente añadido con éxito', 'success')
            return redirect(url_for('main.clients'))
        except Exception as e:
            flash(f'Ocurrió un error al añadir el cliente: {e}', 'danger')
    
    return render_template('new_client.html', form=form)

@main.route("/client/edit/<int:client_id>", methods=['GET', 'POST'])
@login_required
@permission_required('edit_client')
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client)  # Cargar el formulario con los datos del cliente

    # Llamar a actualizar_comunas para establecer las opciones del campo comuna según la región actual
    if form.region.data:
        form.actualizar_comunas(form.region.data)
    
    # Si el formulario se envía correctamente
    if form.validate_on_submit():
        try:
            # Formatear los números de contacto
            formatted_mobile_number = format_chilean_phone_number(form.contact_number.data)
            formatted_landline_number = format_chilean_telephone_number(form.landline.data)

            # Actualizar los atributos del cliente
            client.company_name = form.company_name.data
            client.rut = form.rut.data
            client.legal_representative = form.legal_representative.data
            client.address = form.address.data
            client.commune = form.commune.data
            client.region = form.region.data
            client.contact_number = formatted_mobile_number  # Usa el número de contacto formateado
            client.landline = formatted_landline_number      # Usa el número fijo formateado
            client.approved_credit_amount = form.approved_credit_amount.data
            client.approved_credit_days = form.approved_credit_days.data
            client.branch = form.branch.data
            client.associated_seller = form.associated_seller.data
            
            # Guardar los cambios en la base de datos
            db.session.commit()
            flash('Cliente actualizado con éxito.', 'success')
            return redirect(url_for('main.clients'))
        except Exception as e:
            flash(f'Ocurrió un error al actualizar el cliente: {e}', 'danger')
    
    return render_template('edit_client.html', form=form, client=client)


# Ruta para eliminar un cliente
@main.route("/client/delete/<int:client_id>", methods=['POST'])
@login_required
@permission_required('delete_client')
def delete_client(client_id):
    try:
        client = Client.query.get_or_404(client_id)

        # Eliminar todas las transacciones asociadas a este cliente
        transactions = Transaction.query.filter_by(client_id=client_id).all()
        for transaction in transactions:
            db.session.delete(transaction)

        # Luego, eliminar el cliente
        db.session.delete(client)
        db.session.commit()
        flash('Cliente eliminado con éxito.', 'success')
    except Exception as e:
        flash(f'Ocurrió un error al eliminar el cliente: {e}', 'danger')
    
    return redirect(url_for('main.clients'))


# Ruta para importar clientes desde un archivo Excel
@main.route("/client/import", methods=['POST'])
@login_required
@permission_required('import_client')
def import_clients():
    if 'excel_file' not in request.files:
        flash('No se ha seleccionado ningún archivo.', 'danger')
        return redirect(url_for('main.clients'))
    
    file = request.files['excel_file']
    
    if file.filename == '':
        flash('No se ha seleccionado ningún archivo.', 'danger')
        return redirect(url_for('main.clients'))
    
    if file and allowed_file(file.filename, ['xlsx', 'xls']):
        try:
            # Leer el archivo Excel
            df = pd.read_excel(file)

            # Recorrer las filas y añadir los clientes a la base de datos
            for index, row in df.iterrows():
                client = Client(
                    company_name=row['Nombre Empresa'],
                    rut=row['RUT'],
                    legal_representative=row['Nombre del Representante Legal'],
                    address=row['Dirección'],
                    commune=row['Comuna'],
                    region=row['Región'],
                    contact_number=row['N° Contacto'],
                    landline=row['N° Fijo'],
                    approved_credit_amount=row['CRED. APROBADO (MONTO)'],
                    approved_credit_days=row['CRED. APROBADO (DIAS)'],
                    branch=row.get('Sucursal', None),
                    associated_seller=row.get('Vendedor Asociado', None)
                )
                db.session.add(client)
            
            db.session.commit()
            flash('Clientes importados con éxito.', 'success')
        except Exception as e:
            flash(f'Error al importar los clientes: {e}', 'danger')
    else:
        flash('Formato de archivo no permitido. Solo se permiten archivos Excel (.xlsx, .xls).', 'danger')
    
    return redirect(url_for('main.clients'))

# Ruta para obtener las comunas según la región seleccionada
@main.route('/get_comunas', methods=['POST'])
def get_comunas():
    region = request.form.get('region')
    comunas = obtener_comunas_por_region(region)
    return jsonify(comunas)

# ------------------------------------ FIN DEL CÓDIGO -------------------------------------------
#################################################################################################
#################################################################################################
#################################################################################################
# ----------------------------------- SECCION DE VENTAS -----------------------------------------

@main.route("/sales", methods=['GET'])
@login_required
@permission_required('view_sales')
def sales():
    # Obtener parámetros de filtro
    client_id = request.args.get('client_id')
    date = request.args.get('date')
    price_range = request.args.get('price_range')
    
    # Consulta inicial para obtener las transacciones (ventas)
    sales_query = Transaction.query.order_by(Transaction.date.desc())

    # Aplicar filtros según los parámetros proporcionados
    if client_id:
        sales_query = sales_query.filter_by(client_id=client_id)
    
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d')
            sales_query = sales_query.filter(func.date(Transaction.date) == filter_date)
        except ValueError:
            flash('Fecha no válida.', 'danger')
    
    if price_range:
        try:
            min_price, max_price = map(int, price_range.split('-'))
            sales_query = sales_query.filter(Transaction.total_price >= min_price, Transaction.total_price <= max_price)
        except ValueError:
            flash('Rango de precios no válido.', 'danger')

    # Paginación
    page = request.args.get('page', 1, type=int)
    pagination = sales_query.paginate(page=page, per_page=10, error_out=False)
    sales_list = pagination.items

    # Obtener lista de clientes para los filtros en el HTML
    clients = Client.query.all()

    return render_template('sales.html', sales=sales_list, clients=clients, pagination=pagination)


@main.route("/sale/new", methods=['GET', 'POST'])
@login_required
@permission_required('create_sale')
def new_sale():
    form = SaleForm()
    products = Product.query.all()
    clients = Client.query.all()

    if request.method == 'POST':
        print(request.form)
        try:
            # Obtener el cliente seleccionado
            client_id = request.form.get('client_id')
            if not client_id:
                flash('Debe seleccionar un cliente.', 'danger')
                return redirect(url_for('main.new_sale'))
            
            # Obtener el cliente de la base de datos
            client = Client.query.get(client_id)
            if not client:
                flash('Cliente no encontrado.', 'danger')
                return redirect(url_for('main.new_sale'))

            # Deserializar los productos enviados
            products_data = json.loads(request.form.get('products'))
            if not products_data:
                flash('Debe seleccionar al menos un producto.', 'danger')
                return redirect(url_for('main.new_sale'))

            sale_total = Decimal('0.00')  # Total general de la venta

            # Procesar cada producto
            for product_data in products_data:
                product_id = product_data['id']
                quantity = int(product_data['quantity'])
                discount = float(product_data['discount'])

                product = Product.query.get(product_id)
                if not product:
                    flash(f'Producto con ID {product_id} no encontrado.', 'danger')
                    return redirect(url_for('main.new_sale'))

                # Validar cantidad y descuento
                if quantity <= 0:
                    flash('La cantidad debe ser mayor a cero.', 'danger')
                    return redirect(url_for('main.new_sale'))
                if discount < 0 or discount > 100:
                    flash('El descuento debe estar entre 0 y 100.', 'danger')
                    return redirect(url_for('main.new_sale'))

                # Verificar stock
                if product.stock < quantity:
                    flash(f'No hay suficiente stock para el producto: {product.name}. Disponible: {product.stock}.', 'danger')
                    return redirect(url_for('main.new_sale'))

                # Calcular subtotal, descuento, IVA y total
                subtotal = round(Decimal(product.sale_price) * quantity, 0)
                discount_value = round(subtotal * (Decimal(discount) / 100), 0)
                total_with_discount = round(subtotal - discount_value, 0)
                iva_value = round(total_with_discount * Decimal('0.19'), 0)
                total_price = round(total_with_discount + iva_value, 0)

                sale_total += total_price

                # Crear la transacción
                transaction = Transaction(
                    user_id=current_user.id,
                    client_id=client_id,
                    product_id=product_id,
                    quantity=quantity,
                    total_price=total_price,
                    date=datetime.now(timezone.utc)
                )
                db.session.add(transaction)

                # Reducir el stock del producto
                product.stock -= quantity

            # Confirmar las transacciones en la base de datos
            db.session.commit()
            flash('Venta registrada con éxito.', 'success')
            return redirect(url_for('main.sales'))

        except Exception as e:
            db.session.rollback()
            print(f"Error al registrar la venta: {e}")
            flash(f'Error al registrar la venta: {e}', 'danger')
            return redirect(url_for('main.new_sale'))

    return render_template('new_sale.html', form=form, products=products, clients=clients, credit_days=CREDITOS_APROBADOS_DIAS)

@main.route("/sales/details/<int:sale_id>", methods=['GET'])
@login_required
def get_sale_details(sale_id):
    try:
        sale = Transaction.query.get_or_404(sale_id)
        sale_details = {
            "order_number": sale.id,
            "client_name": sale.client.company_name,
            "date": sale.date.strftime('%Y-%m-%d'),
            "products": [
                {
                    "name": sale.product.name,
                    "quantity": sale.quantity,
                    "price": sale.product.sale_price,
                    "subtotal": sale.quantity * sale.product.sale_price
                }
            ],
            "subtotal": sale.quantity * sale.product.sale_price,
            "discount_value": 0,
            "iva_value": (sale.quantity * sale.product.sale_price) * 0.19,
            "total": (sale.quantity * sale.product.sale_price) * 1.19
        }
        return jsonify(sale_details)
    except Exception as e:
        print(f"Error al obtener los detalles de la venta: {e}")
        return jsonify({"error": "Error al obtener los detalles de la venta"}), 500

# ------------------------------------ FIN DEL CÓDIGO -------------------------------------------
#################################################################################################
#################################################################################################
#################################################################################################
#------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------
# Configura pdfkit para que utilice wkhtmltopdf
config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

# Ruta para guardar el código QR temporalmente
QR_FOLDER = os.path.join('app', 'static', 'qr')

# Crear el directorio si no existe
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)

def clean_number(value):
    """Limpia y convierte un número formateado como string a float"""
    return float(value.replace('$', '').replace('.', '').replace(',', ''))

def generate_qr_code(data):
    """Genera un código QR y lo convierte a base64"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

@main.route("/create_proforma", methods=['POST'])
@login_required
def create_proforma():
    try:
        # Recibe datos del cliente y productos desde el frontend
        data = request.get_json()
        client_name = data.get('client_name')
        client_rut = data.get('client_rut', 'N/A')
        product_details = data.get('product_details', [])
        
        # Limpia los números antes de convertirlos
        subtotal = clean_number(data.get('subtotal', '0'))
        descuento = clean_number(data.get('descuento', '0'))
        iva = clean_number(data.get('iva', '0'))
        total = clean_number(data.get('total', '0'))

        # Fecha actual y número de orden
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        numero_orden = "0001"  # Aquí puedes generar el número dinámicamente si lo deseas

        # Generar el código QR con base en el número de orden y cliente
        qr_data = f"Orden de Compra: {numero_orden}, Cliente: {client_name}, Total: {total}"
        qr_code_base64 = generate_qr_code(qr_data)

        # Cargar el logo en base64
        logo_path = os.path.join('app', 'static', 'template', 'images', 'LOGO-WULKAN-ORIGINAL.png')
        with open(logo_path, "rb") as logo_file:
            logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')

        # Renderiza el HTML con los datos, incluyendo el QR y el logo en formato base64
        html_content = render_template('proforma_template.html', 
                                       cliente_nombre=client_name,
                                       cliente_rut=client_rut,
                                       fecha=fecha_actual,
                                       numero_orden=numero_orden,
                                       productos=product_details,
                                       subtotal=subtotal,
                                       descuento_total=descuento,
                                       iva=iva,
                                       total=total,
                                       logo_base64=logo_base64,
                                       qr_code_base64=qr_code_base64)

        # Genera el PDF usando pdfkit
        options = {
            'enable-local-file-access': True,
        }
        pdf = pdfkit.from_string(html_content, False, configuration=config, options=options)

        # Envía el PDF como archivo descargable
        return send_file(io.BytesIO(pdf), 
                         as_attachment=True, 
                         download_name="orden_de_compra.pdf", 
                         mimetype='application/pdf')
    except Exception as e:
        print(f"Error al crear el PDF: {e}")
        return jsonify({"error": "Error al crear el PDF"}), 500

# ------------------------------------------------------------------------------------------------------------
# Ruta para exportar las ventas a CSV
@main.route("/export_sales")
@login_required
def export_sales():
    sales = Transaction.query.all()

    # Crear el archivo CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Producto', 'Cantidad', 'Precio Total', 'Fecha'])
    for sale in sales:
        writer.writerow([sale.product.name, sale.quantity, sale.total_price, sale.date.strftime('%Y-%m-%d %H:%M:%S')])

    # Generar la respuesta como CSV
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=sales.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

# Ruta para ver y generar reportes de ventas
@main.route("/report_sales", methods=['GET', 'POST'])
@login_required
def report_sales():
    clients = Client.query.all()
    sales = Transaction.query

    # Filtrar por cliente y fecha
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Aplicar filtro de cliente si se selecciona uno
        if client_id:
            sales = sales.filter_by(client_id=client_id)

        # Aplicar filtro de fechas si se proporcionan
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            sales = sales.filter(Transaction.date.between(start_date, end_date))

    sales = sales.all()
    return render_template('report_sales.html', sales=sales, clients=clients)

# Ruta para exportar el reporte de ventas a CSV
@main.route("/export_filtered_sales")
@login_required
def export_filtered_sales():
    client_id = request.args.get('client_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    sales = Transaction.query

    # Filtrar por cliente si se selecciona uno
    if client_id:
        sales = sales.filter_by(client_id=client_id)

    # Filtrar por fechas si se proporcionan
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        sales = sales.filter(Transaction.date.between(start_date, end_date))

    sales = sales.all()

    # Crear el archivo CSV
    output = []
    output.append(['Producto', 'Cliente', 'Cantidad', 'Precio Total', 'Fecha'])
    for sale in sales:
        output.append([sale.product.name, sale.client.company_name, sale.quantity, sale.total_price, sale.date.strftime('%Y-%m-%d %H:%M:%S')])

    # Generar la respuesta como CSV
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerows(output)
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=filtered_sales_report.csv'
    response.headers['Content-type'] = 'text/csv'
    return response
#-------------------------------------------- MI PERFIL ----------------------------------------------------
@main.route("/profile", methods=['GET', 'POST'])
@login_required
@permission_required('edit_profile')
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        # Verificar si el correo electrónico ha cambiado
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('El correo electrónico ya está en uso por otro usuario.', 'danger')
                return redirect(url_for('main.profile'))

        # Actualizar información del usuario
        current_user.username = form.username.data
        current_user.email = form.email.data

        # Actualizar contraseña si se proporciona una nueva
        if form.password.data:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            current_user.password = hashed_password
        
        # Manejar la actualización de la foto de perfil
        if form.photo.data:
            # Asegúrate de tener una carpeta para guardar las imágenes
            upload_folder = os.path.join(current_app.root_path, 'static/uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Limpiar y guardar el nuevo nombre de archivo
            photo_filename = f"user_{clean_worker_filename(current_user.username)}.jpg"
            form.photo.data.save(os.path.join(upload_folder, photo_filename))
            current_user.photo = photo_filename  # Actualiza el campo de foto en el modelo de usuario

        db.session.commit()
        flash('Perfil actualizado con éxito.', 'success')
        return redirect(url_for('main.profile'))

    # Prellenar los campos con la información del usuario actual
    form.username.data = current_user.username
    form.email.data = current_user.email

    return render_template('profile.html', form=form)

#----------------------------------------- FIN DEL CODIGO ---------------------------------------
