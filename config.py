import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'rahasia'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ThirdWay.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
