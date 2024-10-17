from datetime import datetime, timezone
from app import db, login_manager
from flask_login import UserMixin

# Cargar usuario para la autenticación
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modelo de rol
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    permissions = db.Column(db.String, nullable=False)  # Asegúrate de que sea un String

# Modelo de usuario con roles y permisos
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    permissions = db.Column(db.String(200), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True)  # Define la relación con el rol
    photo = db.Column(db.String(120), nullable=True)

    role = db.relationship('Role', backref='users')  # Relación inversa

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role_id}', '{self.permissions}', '{self.photo}')"

# Modelo de producto
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False, name='uq_product_sku')  # SKU único
    image = db.Column(db.String(120), nullable=True)
    stock = db.Column(db.Integer, nullable=False)
    sale_price = db.Column(db.Float, nullable=False)
    bulk_price = db.Column(db.Float, nullable=False)
    bulk_quantity = db.Column(db.Integer, nullable=False, default=1)
    pdf = db.Column(db.String(120), nullable=True)
    min_stock = db.Column(db.Integer, nullable=False, default=0)  # Stock mínimo

    def __repr__(self):
        return f'<Product {self.name}>'

# Modelo de cliente
class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)  # Nombre de la empresa
    rut = db.Column(db.String(50), nullable=False)  # RUT
    legal_representative = db.Column(db.String(150), nullable=False)  # Representante legal
    address = db.Column(db.String(200), nullable=False)  # Dirección
    region = db.Column(db.String(100), nullable=False)  # Región
    commune = db.Column(db.String(100), nullable=False)  # Comuna
    contact_number = db.Column(db.String(50), nullable=False)  # Número de contacto
    landline = db.Column(db.String(50), nullable=True)  # Teléfono fijo (opcional)
    approved_credit_amount = db.Column(db.Float, nullable=False)  # Crédito aprobado
    approved_credit_days = db.Column(db.Integer, nullable=False)  # Días de crédito aprobado
    branch = db.Column(db.String(100), nullable=True)  # Sucursal (opcional)
    associated_seller = db.Column(db.String(100), nullable=True)  # Vendedor asociado (opcional)

    def __repr__(self):
        return f'<Client {self.company_name}>'

# Modelo de transacción
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_transaction_user'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', name='fk_transaction_product'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='fk_transaction_client'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

    # Relaciones con productos y clientes
    product = db.relationship('Product', backref='transactions', lazy=True)
    client = db.relationship('Client', backref='transactions', lazy=True)

    def __repr__(self):
        return f"Transaction('{self.product_id}', '{self.client_id}', '{self.quantity}', '{self.total_price}')"

# Modelo de trabajador
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    photo = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<Worker {self.name}>'

