from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import pytz

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Import utils setelah app dibuat untuk menghindari circular import
    from .utils import utc_to_local, format_datetime

    # Tambahkan timezone ke context processor agar tersedia di semua template
    @app.context_processor
    def inject_timezone():
        return {
            'TIMEZONE': pytz.timezone(app.config['TIMEZONE']),
            'TIMEZONE_OFFSET': app.config['TIMEZONE_OFFSET'],
            'utc_to_local': utc_to_local,
            'format_datetime': format_datetime
        }

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        from . import models  # pastikan models sudah didefinisikan
        db.create_all()

    return app
