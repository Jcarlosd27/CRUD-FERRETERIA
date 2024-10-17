from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import HiddenField, SelectMultipleField, StringField, PasswordField, SubmitField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, NumberRange, Length, Optional
from app.datos_comunas import COMUNAS_CHILE, obtener_comunas_por_region
from .creditos_dias import CREDITOS_APROBADOS_DIAS

# Formulario para eliminar (sin contenido específico)
class DeleteForm(FlaskForm):
    submit = SubmitField('Eliminar')  # Botón de envío para eliminar

class RoleForm(FlaskForm):
    name = StringField('Nombre del Rol', validators=[DataRequired()])
    permissions = SelectMultipleField('Permisos', coerce=str)
    submit = SubmitField('Actualizar Rol')

class UserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[Optional()])
    role_id = SelectField('Rol', coerce=int, validators=[DataRequired()])  # Asignar rol
    photo = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes jpg, jpeg y png.')])  # Campo para la foto
    submit = SubmitField('Guardar Usuario')

# Formulario de inicio de sesión
class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

# Formulario de registro
class RegistrationForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    role_id = SelectField('Rol', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Registrar Usuario')

# Formulario para actualizar el perfil
class UpdateProfileForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Nueva Contraseña (dejar en blanco para no cambiar)')
    photo = FileField('Actualizar Foto de Perfil')  # Agregar este campo
    submit = SubmitField('Actualizar')

class ProductForm(FlaskForm):
    name = StringField('Nombre del Producto', validators=[DataRequired()])
    sku = StringField('SKU', validators=[DataRequired()])  # SKU para productos
    stock = IntegerField('Stock Actual', validators=[DataRequired()])
    min_stock = IntegerField('Stock Mínimo', validators=[DataRequired()])
    sale_price = FloatField('Precio de Venta', validators=[DataRequired()])
    bulk_price = FloatField('Precio por Mayor', validators=[DataRequired()])
    bulk_quantity = IntegerField(
        'Cantidad Mínima para Precio por Mayor', 
        validators=[DataRequired(message='Especifique la cantidad mínima para aplicar el precio por mayor')]
    )  # Nuevo campo
    image = FileField('Imagen', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes.')] )
    pdf = FileField('PDF', validators=[FileAllowed(['pdf'], 'Solo se permiten archivos PDF.')])
    submit = SubmitField('Añadir Producto')

# Formulario para clientes
class ClientForm(FlaskForm):
    company_name = StringField('Nombre Empresa', validators=[DataRequired()])
    rut = StringField('RUT', validators=[DataRequired()])
    legal_representative = StringField('Nombre del Representante Legal', validators=[DataRequired()])
    address = StringField('Dirección', validators=[DataRequired()])

    # SelectFields para región y comuna
    region = SelectField(
        'Región',
        choices=[(key, key) for key in COMUNAS_CHILE.keys()],
        validators=[DataRequired()]
    )
    commune = SelectField(
        'Comuna',
        choices=[],  # Opciones llenadas dinámicamente
        validators=[DataRequired()]
    )

    contact_number = StringField('N° Contacto', validators=[DataRequired()])
    landline = StringField('N° Fijo')
    approved_credit_amount = FloatField('CRED. APROBADO (MONTO)', validators=[DataRequired()])
    approved_credit_days = SelectField('CRED. APROBADO (DÍAS)', choices=CREDITOS_APROBADOS_DIAS, validators=[DataRequired()])
    branch = StringField('Sucursal')
    associated_seller = StringField('Vendedor Asociado')
    submit = SubmitField('Añadir Cliente')

    # Método para actualizar las opciones de comunas según la región seleccionada
    def actualizar_comunas(self, region_seleccionada):
        self.commune.choices = obtener_comunas_por_region(region_seleccionada)

# Formulario para importar clientes desde Excel
class ClientImportForm(FlaskForm):
    excel_file = FileField('Archivo Excel', validators=[FileAllowed(['xlsx', 'xls'], 'Solo se permiten archivos Excel.')])
    submit = SubmitField('Importar')

# Formulario para registrar ventas
class SaleForm(FlaskForm):
    product_id = SelectField('Producto', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1, message="La cantidad debe ser al menos 1")])
    submit = SubmitField('Registrar Venta')

# Formulario para trabajadores
class WorkerForm(FlaskForm):
    name = StringField('Nombre del Trabajador', validators=[DataRequired(), Length(min=2, max=100)])
    position = StringField('Cargo', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Teléfono', validators=[Optional(), Length(min=8, max=15)])  # Teléfono no obligatorio
    email = StringField('Correo Electrónico', validators=[Optional(), Email(), Length(max=120)])
    photo = FileField('Foto del Trabajador', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes jpg, jpeg y png.')])  # Campo para cargar imagen
    submit = SubmitField('Guardar')

# Formulario para eliminar (sin contenido específico)
class DeleteForm(FlaskForm):
    pass

class DeleteRoleForm(FlaskForm):
    submit = SubmitField('Eliminar')