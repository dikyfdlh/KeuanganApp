import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'rahasia'
    # Database Lama
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:pAPqAfzaZAzKvQBUJnCXjAgPgQNimRaF@hopper.proxy.rlwy.net:55845/railway'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:GBLqgutqGFGAEpKJWVvnWuXSxIRTXkAx@shuttle.proxy.rlwy.net:26962/railway'
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///ThirdWay.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Konfigurasi timezone untuk Indonesia/Jakarta (GMT+7)
    TIMEZONE = 'Asia/Jakarta'
    TIMEZONE_OFFSET = timedelta(hours=7)  # GMT+7