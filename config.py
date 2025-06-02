import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
    return database_url or 'postgresql://casinoupdb_owner:npg_uCPmjwl73vAb@ep-lively-lake-a2f6rrwz-pooler.eu-central-1.aws.neon.tech/casinoupdb?sslmode=require'

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-12345')
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки для Railway
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Настройки администратора
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password') 