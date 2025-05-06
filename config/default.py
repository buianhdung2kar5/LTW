import os

class DefaultConfig:
    """Default configuration for Flask app"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
    DEBUG = True
    
    # MongoDB settings - only database is 'film-users'
    MONGO_URI = "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority"
    MONGO_DBNAME = "film-users"
