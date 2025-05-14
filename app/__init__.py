from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        from . import models  # pastikan models sudah didefinisikan
        db.create_all()

    return app
