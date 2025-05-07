from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime

# MongoDB connection function
def get_db():
    """Get MongoDB database connection"""
    try:
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
        print(f"Database connection error: {str(e)}")
        return None, None

# Helper function to find film by ID
def find_film_by_id(db, film_id):
    try:
        # Try numeric ID first
        try:
            film_id_int = int(film_id)
            film = db.films.find_one({"id": film_id_int})
            if film:
                return film, film_id_int
        except:
            pass
            
        # Try ObjectId
        try:
            film = db.films.find_one({"_id": ObjectId(film_id)})
            if film:
                return film, str(film['_id'])
        except:
            pass
            
        # Try string ID as is
        film = db.films.find_one({"id": film_id})
        if film:
            return film, film_id
            
        return None, None
    except Exception as e:
        print(f"Error finding film {film_id}: {str(e)}")
        return None, None

# Helper function to serialize ObjectId to string
def serialize_id(obj):
    if isinstance(obj, dict) and '_id' in obj and isinstance(obj['_id'], ObjectId):
        obj['_id'] = str(obj['_id'])
    return obj

class Favorite:
    @staticmethod
    def add_favorite(user_id, film_id):
        """Add a film to user's favorites"""
        client, db = get_db()
        if db is None:
            return {"success": False, "error": "Database connection failed"}
            
        try:
            # Try to convert user_id to ObjectId if needed
            try:
                user_id_obj = ObjectId(user_id)
            except:
                user_id_obj = user_id
                
            # Check if film exists
            film, valid_film_id = find_film_by_id(db, film_id)
            if not film:
                return {"success": False, "message": "Film not found"}
                
            # Check if already exists
            existing = db.favorites.find_one({
                "user_id": user_id_obj,
                "film_id": valid_film_id
            })
            
            if existing:
                return {"success": False, "message": "Film already in favorites"}
            
            # Create new favorite record
            result = db.favorites.insert_one({
                "user_id": user_id_obj,
                "film_id": valid_film_id,
                "added_at": datetime.now()
            })
            
            return {"success": True, "id": str(result.inserted_id)}
        except Exception as e:
            print(f"Error adding favorite: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            if client:
                client.close()
    
    @staticmethod
    def remove_favorite(user_id, film_id):
        """Remove a film from user's favorites"""
        client, db = get_db()
        if db is None:
            return {"success": False, "error": "Database connection failed"}
            
        try:
            # Try to convert user_id to ObjectId if needed
            try:
                user_id_obj = ObjectId(user_id)
            except:
                user_id_obj = user_id
                
            # Check if film exists and get valid film_id
            film, valid_film_id = find_film_by_id(db, film_id)
            if not film:
                return {"success": False, "message": "Film not found"}
                
            result = db.favorites.delete_one({
                "user_id": user_id_obj,
                "film_id": valid_film_id
            })
            
            if result.deleted_count == 0:
                return {"success": False, "message": "Favorite not found"}
            
            return {"success": True, "message": "Favorite removed successfully"}
        except Exception as e:
            print(f"Error removing favorite: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            if client:
                client.close()
    
    @staticmethod
    def get_user_favorites(user_id):
        """Get all favorites for a user"""
        client, db = get_db()
        if db is None:
            return []
            
        try:
            # Try to convert user_id to ObjectId if needed
            try:
                user_id_obj = ObjectId(user_id)
            except:
                user_id_obj = user_id
                
            favorites = list(db.favorites.find({"user_id": user_id_obj}))
            return [serialize_id(fav) for fav in favorites]
        except Exception as e:
            print(f"Error getting user favorites: {str(e)}")
            return []
        finally:
            if client:
                client.close()
    
    @staticmethod
    def get_user_favorite_films(user_id):
        """Get all favorite films for a user"""
        client, db = get_db()
        if db is None:
            return []
            
        try:
            # Try to convert user_id to ObjectId if needed
            try:
                user_id_obj = ObjectId(user_id)
            except:
                user_id_obj = user_id
                
            favorites = list(db.favorites.find({"user_id": user_id_obj}))
            
            # Get film IDs from favorites
            film_ids = [fav.get("film_id") for fav in favorites]
            
            # Fetch films by those IDs
            films = []
            for film_id in film_ids:
                film, _ = find_film_by_id(db, film_id)
                if film:
                    # Convert ObjectId to string
                    films.append(serialize_id(film))
            
            return films
        except Exception as e:
            print(f"Error getting user favorite films: {str(e)}")
            return []
        finally:
            if client:
                client.close()
    
    @staticmethod
    def is_favorite(user_id, film_id):
        """Check if a film is in user's favorites"""
        client, db = get_db()
        if db is None:
            return False
            
        try:
            # Try to convert user_id to ObjectId if needed
            try:
                user_id_obj = ObjectId(user_id)
            except:
                user_id_obj = user_id
                
            # Check if film exists and get valid film_id
            film, valid_film_id = find_film_by_id(db, film_id)
            if not film:
                return False
                
            favorite = db.favorites.find_one({
                "user_id": user_id_obj,
                "film_id": valid_film_id
            })
            
            return favorite is not None
        except Exception as e:
            print(f"Error checking favorite status: {str(e)}")
            return False
        finally:
            if client:
                client.close()
    
    @staticmethod
    def toggle_favorite(user_id, film_id):
        """Toggle favorite status for a film"""
        client, db = get_db()
        if db is None:
            return {"success": False, "error": "Database connection failed"}, 500
            
        try:
            # Try to convert user_id to ObjectId if needed
            try:
                user_id_obj = ObjectId(user_id)
            except:
                user_id_obj = user_id
                
            # Check if film exists
            film, valid_film_id = find_film_by_id(db, film_id)
            if not film:
                return {"success": False, "message": "Film not found"}, 404
                
            # Check if this film is already in favorites
            favorite = db.favorites.find_one({
                "user_id": user_id_obj,
                "film_id": valid_film_id
            })
            
            # If it exists, remove it
            if favorite:
                db.favorites.delete_one({"_id": favorite["_id"]})
                action = 'removed'
            else:
                # If not, add it
                db.favorites.insert_one({
                    "user_id": user_id_obj,
                    "film_id": valid_film_id,
                    "added_at": datetime.now()
                })
                action = 'added'
            
            return {"success": True, "message": f"Film {action}", "action": action}, 200
        except Exception as e:
            print(f"Error toggling favorite: {str(e)}")
            return {"success": False, "message": str(e)}, 500
        finally:
            if client:
                client.close()
    
    @staticmethod
    def create_indexes(db=None):
        """Create necessary indexes for favorites collection"""
        if db is None:
            client, db = get_db()
            if db is None:
                return False
            close_client = True
        else:
            close_client = False
            client = None
            
    
