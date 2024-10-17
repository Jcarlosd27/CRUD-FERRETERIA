from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from .config import Config
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configurar la carpeta de subida de archivos
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')

    # Inicializar las extensiones
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Registrar los blueprints
    from .routes import main
    app.register_blueprint(main)

    # Activar el modo de depuración
    app.config['DEBUG'] = True
    
     # Filtro para formatear los números con separadores de miles
    @app.template_filter()
    def format_thousands(value):
        return "{:,.0f}".format(value).replace(",", ".")

    # Registrar el filtro en Jinja
    app.jinja_env.filters['format_thousands'] = format_thousands
    
    return app
