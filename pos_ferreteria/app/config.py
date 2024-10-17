import os

class Config:
    SECRET_KEY = 'Sidney19'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pos_ferreteria.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración para subida de archivos
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de 16 MB para archivos subidos

    # Habilitar protección CSRF
    WTF_CSRF_ENABLED = True
