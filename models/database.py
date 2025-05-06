from flask import Flask
import socket
import threading

def init_database(app):
    """Initialize MongoDB database with direct database access from film-users database"""
    try:
        from . import films_collection, genres_collection, users_collection
        from .genre import Genre
        from .film import Film
        
        print("Checking film-users database collections...")
        
        # Create necessary indexes
        try:
            # Film indexes
            films_collection.create_index("id", unique=True)
            films_collection.create_index("title")
            films_collection.create_index([("title", "text"), ("description", "text")])
            
            # Genre indexes
            genres_collection.create_index("slug", unique=True)
            genres_collection.create_index("id", unique=True)
            
            # User indexes
            users_collection.create_index("username", unique=True)
            
            print("MongoDB indexes created successfully")
        except Exception as e:
            print(f"Error creating indexes: {str(e)}")
        
        # Load genres directly from database
        if not Genre.get_all():
            Genre.create_default_genres()
        
        # Load films directly from database    
        Film.load_films_from_database()
        
        # Check for duplicate film IDs
        duplicate_ids = Film.find_duplicate_ids()
        if duplicate_ids:
            print(f"WARNING: Found {len(duplicate_ids)} films with duplicate IDs in film-users database")
            
        print("film-users database initialized successfully.")
        return True
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        return False

def create_api_app():
    api_app = Flask(__name__)
    api_app.config['SECRET_KEY'] = 'your-secret-key'
    return api_app

def create_web_app():
    web_app = Flask(__name__)
    web_app.config['SECRET_KEY'] = 'your-secret-key'
    return web_app

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except socket.error:
        print(f"Port {port} is already in use. Please free the port and try again.")
        return False
