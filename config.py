import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'rahasia'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:pAPqAfzaZAzKvQBUJnCXjAgPgQNimRaF@hopper.proxy.rlwy.net:55845/railway'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
