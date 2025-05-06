from flask import Flask, jsonify, request, render_template, session, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import socket
from datetime import datetime
import threading
import ssl

# Connect directly to MongoDB Atlas film-users database
try:
    # Use only MongoDB Atlas with simplified connection
    uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
    dbname = "film-users"  # Explicitly use film-users database
    
    # Create MongoDB client with improved connection settings and explicit SSL context
    mongo_client = MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        maxPoolSize=50,
        retryWrites=True,
        ssl=True,
        tlsAllowInvalidCertificates=True  # Updated from ssl_cert_reqs=ssl.CERT_NONE
    )
    
    # Test connection immediately
    mongo_client.admin.command('ping')
    print("[SUCCESS] MongoDB Atlas connection successful!")
except Exception as e:
    print(f"[ERROR] MongoDB Atlas connection error: {str(e)}")
    # Create dummy collections to prevent errors
    class DummyCollection:
        def find_one(self, *args, **kwargs): 
            return None
            
        def find(self, *args, **kwargs): 
            class DummyCursor:
                def __init__(self):
                    self.data = []
                    
                def sort(self, *args): 
                    return self
                    
                def limit(self, *args): 
                    return self
                    
                def skip(self, *args): 
                    return self
                    
                # Make cursor iterable
                def __iter__(self):
                    return iter(self.data)
                    
                # Make cursor list-like
                def __getitem__(self, key):
                    return self.data[key] if 0 <= key < len(self.data) else None
                    
                # Add length method
                def __len__(self):
                    return 0
            
            return DummyCursor()
            
        def count_documents(self, *args, **kwargs): 
            return 0
            
        def insert_one(self, *args, **kwargs): 
            class DummyResult:
                @property
                def inserted_id(self):
                    return 'dummy_id'
            return DummyResult()
            
        def update_one(self, *args, **kwargs): 
            return None
            
        def delete_one(self, *args, **kwargs): 
            return None
            
        def create_index(self, *args, **kwargs): 
            return None
    
    # Create empty dummy client and db
    mongo_client = None
    db = None
    films_collection = DummyCollection()
    genres_collection = DummyCollection()
    users_collection = DummyCollection()
    favorites_collection = DummyCollection()

# Get database and collections
try:
    # Get film-users database
    db = mongo_client["film-users"]
    
    # Define collections
    films_collection = db.films
    genres_collection = db.genres
    users_collection = db.users
    favorites_collection = db.favorites
    
    print(f"[INFO] Connected to collections: films ({films_collection.count_documents({})} documents), "
          f"genres ({genres_collection.count_documents({})} documents), "
          f"users ({users_collection.count_documents({})} documents), "
          f"favorites ({favorites_collection.count_documents({})} documents)")
except Exception as e:
    print(f"[ERROR] Failed to access MongoDB collections: {str(e)}")
    # Create dummy instances
    db = None
    films_collection = DummyCollection()
    genres_collection = DummyCollection()
    users_collection = DummyCollection()
    favorites_collection = DummyCollection()

# Helper function to serialize ObjectId to string
def serialize_id(obj):
    if isinstance(obj, dict) and '_id' in obj and isinstance(obj['_id'], ObjectId):
        obj['_id'] = str(obj['_id'])
    return obj

# Film model functions
class Film:
    @staticmethod
    def get_all():
        try:
            # Handle possible generator/iterator errors
            results = list(films_collection.find())
            return [serialize_id(film) for film in results]
        except Exception as e:
            print(f"Error in Film.get_all(): {str(e)}")
            return []  # Return empty list on error
    
    @staticmethod
    def get_by_id(film_id):
        if isinstance(film_id, int):
            film = films_collection.find_one({"id": film_id})
        else:
            try:
                film = films_collection.find_one({"_id": ObjectId(film_id)})
            except:
                film = None
        return serialize_id(film) if film else None
    
    @staticmethod
    def get_by_genre(genre_id):
        try:
            films = films_collection.find({"genre_ids": genre_id})
            return [serialize_id(film) for film in films]
        except Exception as e:
            print(f"Error in Film.get_by_genre(): {str(e)}")
            return []
    
    @staticmethod
    def create(data):
        # Generate a new id if not provided
        if 'id' not in data:
            max_id = films_collection.find_one(sort=[("id", -1)])
            data['id'] = 1 if max_id is None else max_id.get('id', 0) + 1
            
        result = films_collection.insert_one(data)
        return serialize_id({**data, "_id": result.inserted_id})
    
    @staticmethod
    def update(film_id, data):
        if isinstance(film_id, int):
            films_collection.update_one({"id": film_id}, {"$set": data})
            return Film.get_by_id(film_id)
        else:
            try:
                films_collection.update_one({"_id": ObjectId(film_id)}, {"$set": data})
                return Film.get_by_id(film_id)
            except:
                return None
    
    @staticmethod
    def delete(film_id):
        if isinstance(film_id, int):
            films_collection.delete_one({"id": film_id})
        else:
            try:
                films_collection.delete_one({"_id": ObjectId(film_id)})
            except:
                pass
    
    @staticmethod
    def search(query):
        try:
            films = films_collection.find({"title": {"$regex": query, "$options": "i"}})
            return [serialize_id(film) for film in films]
        except Exception as e:
            print(f"Error in Film.search(): {str(e)}")
            return []
    
    @staticmethod
    def get_featured():
        try:
            # Handle possible generator/iterator errors
            results = list(films_collection.find({"featured": True}))
            return [serialize_id(film) for film in results]
        except Exception as e:
            print(f"Error in Film.get_featured(): {str(e)}")
            return []  # Return empty list on error
    
    @staticmethod
    def get_top_rated(limit=10):
        try:
            # Handle possible generator/iterator errors
            results = list(films_collection.find().sort("rating", -1).limit(limit))
            return [serialize_id(film) for film in results]
        except Exception as e:
            print(f"Error in Film.get_top_rated(): {str(e)}")
            return []  # Return empty list on error
    
    @staticmethod
    def paginate(page=1, per_page=10, filters=None):
        try:
            skip = (page - 1) * per_page
            
            # Apply filters if provided
            query = filters if filters else {}
            
            # Get total count for pagination
            total_count = films_collection.count_documents(query)
            total_pages = (total_count + per_page - 1) // per_page
            
            # Get paginated results
            films = films_collection.find(query).skip(skip).limit(per_page)
            
            return {
                "films": [serialize_id(film) for film in films],
                "total_pages": total_pages,
                "total_count": total_count,
                "current_page": page
            }
        except Exception as e:
            print(f"Error in Film.paginate(): {str(e)}")
            return {
                "films": [],
                "total_pages": 1,
                "total_count": 0,
                "current_page": page
            }
    
    @staticmethod
    def load_films_from_database():
        """Get films directly from MongoDB film-users database"""
        try:
            # Check if films exist in the database
            films_count = films_collection.count_documents({})
            if films_count > 0:
                print(f"Found {films_count} films in film-users database.")
                return True
                
            print("No films found in film-users database. Please populate the database.")
            return False
        except Exception as e:
            print(f"Error loading films from database: {str(e)}")
            return False
    
    @staticmethod
    def create_indexes():
        """Create necessary indexes for films collection"""
        try:
            films_collection.create_index("id", unique=True)
            films_collection.create_index("title")
            films_collection.create_index([("title", "text"), ("description", "text")])
            print("[SUCCESS] Film indexes created successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Error creating film indexes: {str(e)}")
            return False
            
    @staticmethod
    def find_duplicate_ids():
        """Find films with duplicate IDs"""
        try:
            pipeline = [
                {"$group": {"_id": "$id", "count": {"$sum": 1}, "titles": {"$push": "$title"}}},
                {"$match": {"count": {"$gt": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            duplicate_ids = list(films_collection.aggregate(pipeline))
            return duplicate_ids
        except Exception as e:
            print(f"Error finding duplicate IDs: {str(e)}")
            return []
    
    @staticmethod
    def fix_duplicate_ids():
        """Fix films with duplicate IDs by assigning new IDs to duplicates"""
        try:
            duplicate_ids = Film.find_duplicate_ids()
            changes_made = 0
            
            for dup in duplicate_ids:
                dup_id = dup['_id']
                films = list(films_collection.find({"id": dup_id}))
                
                # Keep first film, update others with new IDs
                for i, film in enumerate(films[1:], 1):
                    highest_id_doc = films_collection.find_one(sort=[("id", -1)])
                    new_id = highest_id_doc['id'] + 1 if highest_id_doc else 1
                    
                    films_collection.update_one({"_id": film['_id']}, {"$set": {"id": new_id}})
                    changes_made += 1
            
            return {"success": True, "duplicates_fixed": changes_made}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Genre model functions
class Genre:
    @staticmethod
    def get_all():
        try:
            # Handle possible generator/iterator errors
            results = list(genres_collection.find())
            return [serialize_id(genre) for genre in results]
        except Exception as e:
            print(f"Error in Genre.get_all(): {str(e)}")
            return []  # Return empty list on error
    
    @staticmethod
    def get_by_id(genre_id):
        try:
            if isinstance(genre_id, int):
                genre = genres_collection.find_one({"id": genre_id})
            else:
                try:
                    genre = genres_collection.find_one({"_id": ObjectId(genre_id)})
                except:
                    genre = None
            return serialize_id(genre) if genre else None
        except Exception as e:
            print(f"Error in Genre.get_by_id(): {str(e)}")
            return None
    
    @staticmethod
    def get_by_slug(slug):
        try:
            genre = genres_collection.find_one({"slug": slug})
            return serialize_id(genre) if genre else None
        except Exception as e:
            print(f"Error in Genre.get_by_slug(): {str(e)}")
            return None
    
    @staticmethod
    def get_by_name(name):
        try:
            genre = genres_collection.find_one({"name": name})
            return serialize_id(genre) if genre else None
        except Exception as e:
            print(f"Error in Genre.get_by_name(): {str(e)}")
            return None
    
    @staticmethod
    def create(data):
        # Generate a new id if not provided
        if 'id' not in data:
            max_id = genres_collection.find_one(sort=[("id", -1)])
            data['id'] = 1 if max_id is None else max_id.get('id', 0) + 1
            
        result = genres_collection.insert_one(data)
        return serialize_id({**data, "_id": result.inserted_id})
    
    @staticmethod
    def get_films(genre_id):
        return Film.get_by_genre(genre_id)
    
    @staticmethod
    def load_genres_from_database():
        """Get genres directly from MongoDB film-users database"""
        try:
            # Check if genres exist in the database
            genres_count = genres_collection.count_documents({})
            if genres_count > 0:
                print(f"Found {genres_count} genres in film-users database.")
                return True
                
            print("No genres found in film-users database. Creating default genres...")
            # Create some default genres if none exist
            return Genre.create_default_genres()
        except Exception as e:
            print(f"Error loading genres from database: {str(e)}")
            return False
    
    @staticmethod
    def create_default_genres():
        """Create default genres if none exist in the database"""
        try:
            default_genres = [
                {"name": "Hành động", "slug": "hanh-dong", "description": "Phim hành động"},
                {"name": "Tình cảm", "slug": "tinh-cam", "description": "Phim tình cảm"},
                {"name": "Kinh dị", "slug": "kinh-di", "description": "Phim kinh dị"},
                {"name": "Hài hước", "slug": "hai-huoc", "description": "Phim hài hước"},
                {"name": "Anime", "slug": "anime", "description": "Phim hoạt hình Nhật Bản"},
                {"name": "Viễn tưởng", "slug": "vien-tuong", "description": "Phim viễn tưởng"},
                {"name": "Tâm lý", "slug": "tam-ly", "description": "Phim tâm lý"},
                {"name": "Lịch sử", "slug": "lich-su", "description": "Phim lịch sử"},
                {"name": "Chiến tranh", "slug": "chien-tranh", "description": "Phim chiến tranh"},
                {"name": "Võ thuật", "slug": "vo-thuat", "description": "Phim võ thuật"},
                {"name": "Cổ trang", "slug": "co-trang", "description": "Phim cổ trang"},
                {"name": "Thần thoại", "slug": "than-thoai", "description": "Phim thần thoại"},
                {"name": "Phiêu lưu", "slug": "phieu-luu", "description": "Phim phiêu lưu"},
                {"name": "Gia đình", "slug": "gia-dinh", "description": "Phim gia đình"},
                {"name": "Hình sự", "slug": "hinh-su", "description": "Phim hình sự"},
                {"name": "Trinh thám", "slug": "trinh-tham", "description": "Phim trinh thám"}
            ]
            
            for i, genre in enumerate(default_genres, 1):
                genre["id"] = i
                genres_collection.insert_one(genre)
                
            genres_collection.create_index("slug", unique=True)
            genres_collection.create_index("name")
            
            print(f"[SUCCESS] Created {len(default_genres)} default genres in film-users database")
            return True
        except Exception as e:
            print(f"Error creating default genres: {str(e)}")
            return False
    
    @staticmethod
    def find_duplicate_ids():
        """Find genres with duplicate IDs"""
        try:
            pipeline = [
                {"$group": {"_id": "$id", "count": {"$sum": 1}, "names": {"$push": "$name"}}},
                {"$match": {"count": {"$gt": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            duplicate_ids = list(genres_collection.aggregate(pipeline))
            return duplicate_ids
        except Exception as e:
            print(f"Error finding duplicate genre IDs: {str(e)}")
            return []

# Favorites model functions
class Favorite:
    @staticmethod
    def add_favorite(user_id, film_id):
        """Add a film to user's favorites"""
        try:
            # Check if already exists
            existing = favorites_collection.find_one({
                "user_id": user_id,
                "film_id": film_id
            })
            
            if existing:
                return {"success": False, "message": "Film already in favorites"}
            
            # Create new favorite record
            result = favorites_collection.insert_one({
                "user_id": user_id,
                "film_id": film_id,
                "added_at": datetime.now()
            })
            
            return {"success": True, "id": str(result.inserted_id)}
        except Exception as e:
            print(f"Error adding favorite: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def remove_favorite(user_id, film_id):
        """Remove a film from user's favorites"""
        try:
            result = favorites_collection.delete_one({
                "user_id": user_id,
                "film_id": film_id
            })
            
            if result.deleted_count == 0:
                return {"success": False, "message": "Favorite not found"}
            
            return {"success": True}
        except Exception as e:
            print(f"Error removing favorite: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_favorites(user_id):
        """Get all favorites for a user"""
        try:
            favorites = list(favorites_collection.find({"user_id": user_id}))
            return [serialize_id(fav) for fav in favorites]
        except Exception as e:
            print(f"Error getting user favorites: {str(e)}")
            return []
    
    @staticmethod
    def is_favorite(user_id, film_id):
        """Check if a film is in user's favorites"""
        try:
            favorite = favorites_collection.find_one({
                "user_id": user_id,
                "film_id": film_id
            })
            return favorite is not None
        except Exception as e:
            print(f"Error checking favorite status: {str(e)}")
            return False
    
    @staticmethod
    def create_indexes():
        """Create necessary indexes for favorites collection"""
        try:
            favorites_collection.create_index([("user_id", 1), ("film_id", 1)], unique=True)
            favorites_collection.create_index("user_id")
            favorites_collection.create_index("film_id")
            print("[SUCCESS] Favorites indexes created successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Error creating favorites indexes: {str(e)}")
            return False

# User model functions
class User:
    @staticmethod
    def get_by_username(username):
        user = users_collection.find_one({"username": username})
        return serialize_id(user) if user else None
    
    @staticmethod
    def get_by_id(user_id):
        try:
            # Try as ObjectId
            if isinstance(user_id, str) and len(user_id) == 24:
                user = users_collection.find_one({"_id": ObjectId(user_id)})
            # Try as numeric ID
            elif isinstance(user_id, (int, str)):
                try:
                    user_id_int = int(user_id)
                    user = users_collection.find_one({"id": user_id_int})
                except (ValueError, TypeError):
                    user = None
            else:
                user = None
                
            return serialize_id(user) if user else None
        except Exception as e:
            print(f"Error in User.get_by_id(): {str(e)}")
            return None
    
    @staticmethod
    def create(data):
        # Add registerDate if not present
        if 'registerDate' not in data:
            data['registerDate'] = datetime.now()
        
        # Maintain backward compatibility with created_at
        data['created_at'] = data.get('registerDate', datetime.now())
        
        result = users_collection.insert_one(data)
        return serialize_id({**data, "_id": result.inserted_id})
    
    @staticmethod
    def update_password(user_id, current_password, new_password):
        """Update user password if current password matches"""
        user = User.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "User not found"}
            
        if user.get('password') != current_password:
            return {"success": False, "message": "Current password is incorrect"}
            
        try:
            if isinstance(user_id, str) and len(user_id) == 24:
                result = users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"password": new_password, "updatedAt": datetime.now()}}
                )
            else:
                try:
                    user_id_int = int(user_id)
                    result = users_collection.update_one(
                        {"id": user_id_int},
                        {"$set": {"password": new_password, "updatedAt": datetime.now()}}
                    )
                except:
                    return {"success": False, "message": "Invalid user ID format"}
                
            return {"success": True, "message": "Password updated successfully"}
        except Exception as e:
            print(f"Error updating password: {str(e)}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    def update_profile(user_id, data):
        """Update user profile data"""
        try:
            update_data = {
                "updatedAt": datetime.now()
            }
            
            # Add fields to update if they exist in data
            if 'email' in data and data['email']:
                update_data['email'] = data['email']
            if 'fullName' in data and data['fullName']:
                update_data['fullName'] = data['fullName']
                
            # Try to update by ObjectId first
            try:
                result = users_collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': update_data}
                )
            except:
                # If not a valid ObjectId, try as a numeric ID
                try:
                    user_id_int = int(user_id)
                    result = users_collection.update_one(
                        {'id': user_id_int},
                        {'$set': update_data}
                    )
                except:
                    return {"success": False, "message": "Invalid user ID format"}
            
            if result and result.matched_count > 0:
                return {"success": True, "message": "Profile updated successfully"}
            else:
                return {"success": False, "message": "User not found"}
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    def authenticate(username, password):
        user = User.get_by_username(username)
        if user and user.get('password') == password:
            return user
        return None

# Initialize the database
def init_database(app):
    """Initialize MongoDB database with direct database access from film-users database"""
    try:
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
            
            # Favorites indexes
            Favorite.create_indexes()
            
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

# API and Web app creation functions
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

if __name__ == '__main__':
    basedir = os.path.abspath(os.path.dirname(__file__))
    if not check_port(5000) or not check_port(5001):
        exit(1)
    api_app = create_api_app()
    web_app = create_web_app()
    init_database(api_app)
    print("Starting API on http://127.0.0.1:5000")
    print("Starting Web on http://127.0.0.1:5001")
    api_thread = threading.Thread(target=lambda: api_app.run(debug=True, port=5000, use_reloader=False))
    web_thread = threading.Thread(target=lambda: web_app.run(debug=True, port=5001, use_reloader=False))
    api_thread.start()
    web_thread.start()
    api_thread.join()
    web_thread.join()

# Ensure that Film class and other models are properly defined and exported
__all__ = ['Film', 'Genre', 'User', 'Favorite', 'init_database', 'create_api_app', 'create_web_app']