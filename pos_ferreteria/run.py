from app import create_app, db
from flask_migrate import Migrate

app = create_app()  # Inicializar la aplicación Flask
migrate = Migrate(app, db)  # Inicializar Flask-Migrate

if __name__ == '__main__':
    app.run(debug=True)
