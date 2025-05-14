from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class BiayaTetap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    jumlah = db.Column(db.Float)

class BiayaVariabel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    jumlah = db.Column(db.Float)

class Pendapatan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sumber = db.Column(db.String(100))
    jumlah = db.Column(db.Float)
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    namalengkap= db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)