import os
import logging
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from bson.objectid import ObjectId
from datetime import datetime

from routes.auth_routes import register_auth_routes
from routes.admin_routes import register_admin_routes
from routes.film_routes import register_film_routes
from routes.error_handlers import register_error_handlers
from routes.user_routes import register_user_routes
from routes.favorite_film import favorite_bp

# Try to import database utility
try:
    from utils.db import get_mongo_client, get_db_name, init_mongo_indexes, migrate_users_without_id
except ImportError:
    def get_mongo_client():
        logging.warning("MongoDB client utility not found.")
        return None
    def get_db_name():
        return "film-users"
    def init_mongo_indexes(db):
        logging.warning("MongoDB indexes utility not found.")
    def migrate_users_without_id(db):
        logging.warning("MongoDB user ID migration utility not found.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', mode='a', encoding='utf-8', delay=True),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# MongoDB connection function
def get_db_connection():
    """Get MongoDB database connection"""
    try:
        from pymongo import MongoClient
        uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
        dbname = os.environ.get('MONGO_DBNAME', "film-users")
        
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=50,
            ssl=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=True
        )
        db = client[dbname]
        return client, db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None, None

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'default-dev-key')
    
    # Register routes directly (without blueprints)
    register_auth_routes(app)
    register_admin_routes(app)
    register_film_routes(app)
    register_error_handlers(app)
    register_user_routes(app)
    app.register_blueprint(favorite_bp)
    # User account page with favorites
    @app.route('/account')
    def account():
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để xem trang này', 'error')
            return redirect(url_for('login'))
        
        client, db = get_db_connection()
        favorites = []
        user_data = {
            'username': session.get('username', 'User'),
            'email': session.get('email','User'),
            'user_id':session.get('user_id','User'),
            'registerDate': datetime.now()
        }
        
        try:
            user_id = session.get('user_id')
            
            # First get user profile data
            try:
                # Try as ObjectId
                user = db.users.find_one({'_id': ObjectId(user_id)})
            except:
                try:
                    # Try as numeric ID
                    user_id_int = int(user_id)
                    user = db.users.find_one({'id': user_id_int})
                except:
                    user = None
            
            if user:
                user_data = {
                    'username': user.get('username', 'User'),
                    'email': user.get('email', ''),
                    'id': str(user.get('_id')),
                    'fullName': user.get('fullName', ''),
                    'registerDate': user.get('registerDate', datetime.now())
                }
            
            # Try to import models
            try:
                from models.models import Favorite, Film
                
                # Use the model
                favorites_data = Favorite.get_user_favorites(str(user_id))
                film_ids = [fav.get('film_id') for fav in favorites_data]
                
                for film_id in film_ids:
                    film = Film.get_by_id(film_id)
                    if film:
                        favorites.append(film)
            except ImportError:
                # Direct database access
                user_favorites = list(db.favorites.find({"user_id": user_id}))
                film_ids = [fav.get('film_id') for fav in user_favorites]
                
                for film_id in film_ids:
                    try:
                        # Try different formats of ID
                        film = None
                        try:
                            film_id_int = int(film_id)
                            film = db.films.find_one({"id": film_id_int})
                        except:
                            try:
                                film = db.films.find_one({"_id": ObjectId(film_id)})
                            except:
                                film = db.films.find_one({"id": film_id})
                        
                        if film:
                            if '_id' in film:
                                film['_id'] = str(film['_id'])
                            favorites.append(film)
                    except Exception as e:
                        logger.error(f"Error getting film {film_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting account data: {str(e)}")
        finally:
            if client:
                client.close()
        
        return render_template('account.html', favorites=favorites, user=user_data)
    
    # All favorites page
    @app.route('/favorites')
    def favorites():
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để xem trang này', 'error')
            return redirect(url_for('login'))
        
        client, db = get_db_connection()
        favorites = []
        
        try:
            user_id = session.get('user_id')
            
            # Try to import models
            try:
                from models.models import Favorite, Film
                
                # Use the model
                favorites_data = Favorite.get_user_favorites(str(user_id))
                film_ids = [fav.get('film_id') for fav in favorites_data]
                
                for film_id in film_ids:
                    film = Film.get_by_id(film_id)
                    if film:
                        favorites.append(film)
            except ImportError:
                # Direct database access
                user_favorites = list(db.favorites.find({"user_id": user_id}))
                film_ids = [fav.get('film_id') for fav in user_favorites]
                
                for film_id in film_ids:
                    try:
                        # Try different formats of ID
                        film = None
                        try:
                            film_id_int = int(film_id)
                            film = db.films.find_one({"id": film_id_int})
                        except:
                            try:
                                film = db.films.find_one({"_id": ObjectId(film_id)})
                            except:
                                film = db.films.find_one({"id": film_id})
                        
                        if film:
                            if '_id' in film:
                                film['_id'] = str(film['_id'])
                            favorites.append(film)
                    except Exception as e:
                        logger.error(f"Error getting film {film_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting favorites: {str(e)}")
        finally:
            if client:
                client.close()
        
        return render_template('favorites.html', favorites=favorites)
    
    # API to check if a film is in user favorites
    @app.route('/user/favorites/check/<film_id>')
    def check_favorite(film_id):
        if 'user_id' not in session:
            return jsonify({"isFavorite": False})
        
        client, db = get_db_connection()
        if db is None:
            return jsonify({"isFavorite": False})
        
        try:
            user_id = session.get('user_id')
            
            # Try to import models
            try:
                from models.models import Favorite
                user_id_str = str(user_id)
                is_favorite = Favorite.is_favorite(user_id_str, film_id)
                return jsonify({"isFavorite": is_favorite})
            except ImportError:
                # Convert ObjectId if needed
                try:
                    user_id_obj = ObjectId(user_id)
                except:
                    user_id_obj = user_id
                    
                # Try to find a favorite with this user and film
                favorite = db.favorites.find_one({
                    "user_id": user_id_obj,
                    "film_id": film_id
                })
                
                return jsonify({"isFavorite": favorite is not None})
        except Exception as e:
            logger.error(f"Error checking favorite: {str(e)}")
            return jsonify({"isFavorite": False})
        finally:
            if client:
                client.close()
    
    # API to toggle favorite status
    @app.route('/user/favorites/toggle/<film_id>', methods=['POST'])
    def toggle_favorite(film_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        client, db = get_db_connection()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            user_id = session.get('user_id')
            
            # Check if film exists
            film = None
            try:
                # Try numeric ID first
                try:
                    film_id_int = int(film_id)
                    film = db.films.find_one({'id': film_id_int})
                    if film:
                        film_id = film_id_int  # Use numeric ID if found
                except:
                    # Then try ObjectId
                    try:
                        film = db.films.find_one({'_id': ObjectId(film_id)})
                        if film:
                            film_id = str(film['_id'])  # Use string ID if found
                    except:
                        pass
            except Exception as e:
                logger.error(f"Error checking film {film_id}: {str(e)}")
            
            if not film:
                return jsonify({'message': 'Phim không tồn tại'}), 404
                
            # Check if this film is already in favorites
            try:
                user_id_obj = ObjectId(user_id)
            except:
                user_id_obj = user_id
                
            favorite = db.favorites.find_one({
                "user_id": user_id_obj,
                "film_id": film_id
            })
            
            # If it exists, remove it
            if favorite:
                db.favorites.delete_one({"_id": favorite["_id"]})
                action = 'removed'
            else:
                # If not, add it
                db.favorites.insert_one({
                    "user_id": user_id_obj,
                    "film_id": film_id,
                    "added_at": datetime.now()
                })
                action = 'added'
            
            return jsonify({'message': f'Phim đã được {action}', 'action': action})
                
        except Exception as e:
            logger.error(f"Error toggling favorite: {str(e)}")
            return jsonify({'message': str(e)}), 500
        finally:
            if client:
                client.close()
    
    # Get all user favorites as JSON
    @app.route('/user/favorites')
    def get_favorites_json():
        if 'user_id' not in session:
            return jsonify([])
        
        client, db = get_db_connection()
        if db is None:
            return jsonify([])
        
        try:
            user_id = session.get('user_id')
            
            # Try to import models
            try:
                from models.models import Favorite, Film
                
                # Use the model
                user_id_str = str(user_id)
                favorites_data = Favorite.get_user_favorites(user_id_str)
                
                film_ids = [fav.get('film_id') for fav in favorites_data]
                
                # Get film details for each favorite
                films = []
                for film_id in film_ids:
                    film = Film.get_by_id(film_id)
                    if film:
                        films.append(film)
                
                return jsonify(films)
            except ImportError:
                # Direct database access (legacy code)
                # Find favorites for this user
                favorites = list(db.favorites.find({"user_id": user_id}))
                
                if not favorites:
                    return jsonify([])
                
                # Get film IDs from favorites
                film_ids = [fav.get('film_id') for fav in favorites]
                
                # Fetch films by those IDs
                films = []
                for film_id in film_ids:
                    try:
                        # Try numerical ID first
                        try:
                            film_id_int = int(film_id)
                            film = db.films.find_one({"id": film_id_int})
                        except:
                            # Then try ObjectId
                            try:
                                film = db.films.find_one({"_id": ObjectId(film_id)})
                            except:
                                continue
                        
                        if film:
                            # Convert ObjectId to string
                            if '_id' in film:
                                film['_id'] = str(film['_id'])
                            films.append(film)
                    except Exception as e:
                        logger.error(f"Error getting film {film_id}: {str(e)}")
                        continue
                
                return jsonify(films)
        except Exception as e:
            logger.error(f"Error getting favorites: {str(e)}")
            return jsonify([])
        finally:
            if client:
                client.close()
    
    # Import debug routes in development environment
    if app.config.get('ENV') == 'development':
        from routes.debug_routes import register_debug_routes
        register_debug_routes(app)
    
    # Initialize MongoDB connection and indexes
    try:
        # Get MongoDB client
        client = get_mongo_client()
        if client is not None:
            # Get database
            db_name = get_db_name()
            db = client[db_name]
            
            # Migrate user IDs to sequential numbers before initializing indexes
            migrate_users_without_id(db)
            
            # Initialize indexes
            init_mongo_indexes(db)
            
            # Create favorites index
            try:
                db.favorites.create_index([("user_id", 1), ("film_id", 1)], unique=True)
                db.favorites.create_index("user_id")
                db.favorites.create_index("film_id")
                logger.info("Favorites indexes created successfully")
            except Exception as e:
                logger.error(f"Error creating favorites indexes: {str(e)}")
            
            # Close connection
            client.close()
            logger.info(f"MongoDB connection initialized for database: {db_name}")
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {str(e)}")
    
    return app

if __name__ == '__main__':
    # Create necessary directories
    try:
        os.makedirs('static/uploads', exist_ok=True)
        os.makedirs('static/images', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating directories: {str(e)}")
    
    app = create_app()
    app.run(debug=True)
