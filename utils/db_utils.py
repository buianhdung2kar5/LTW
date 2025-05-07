from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import logging
from functools import lru_cache
import time
import threading

logger = logging.getLogger(__name__)

# MongoDB connection settings
MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
MONGO_DBNAME = os.environ.get('MONGO_DBNAME', "film-users")

# Global MongoDB client for connection pooling with lock for thread safety
_client = None
_client_lock = threading.Lock()

def get_db_connection():
    """Get MongoDB database connection using optimized connection pooling"""
    global _client
    
    # Fast path with existing connection
    if _client is not None:
        try:
            # Verify connection is still alive with fast timeout
            _client.admin.command('ping', serverSelectionTimeoutMS=1000)
            return _client, _client[MONGO_DBNAME]
        except Exception:
            # Connection lost, we'll recreate it below
            with _client_lock:
                _client = None
    
    # Need to create a new connection with thread safety
    with _client_lock:
        # Double-check in case another thread created the connection
        if _client is not None:
            return _client, _client[MONGO_DBNAME]
            
        try:
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=3000,   # Reduced timeout for faster failure detection
                connectTimeoutMS=3000,           # Reduced timeout
                socketTimeoutMS=10000,
                maxPoolSize=20,                  # Optimal pool size for web traffic
                minPoolSize=5,                   # Keep minimum connections in pool
                maxIdleTimeMS=60000,             # Close idle connections after 60 seconds
                ssl=True,
                tlsAllowInvalidCertificates=True,
                retryWrites=True,
                appname="phim-neu-app",
                waitQueueTimeoutMS=1000,         # Fast failure if queue wait is too long
            )
            
            # Lighter ping test with timeout
            _client.admin.command('ping', serverSelectionTimeoutMS=2000)
            logger.info("MongoDB connection established successfully")
            return _client, _client[MONGO_DBNAME]
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            _client = None
            return None, None

# Optimize serialization with larger cache
@lru_cache(maxsize=2048)
def serialize_id(obj):
    """Convert MongoDB ObjectId to string for JSON serialization with improved caching"""
    if isinstance(obj, dict) and '_id' in obj and isinstance(obj['_id'], ObjectId):
        obj = dict(obj)  # Create a copy to avoid modifying the original
        obj['_id'] = str(obj['_id'])
    return obj

# Improved film finding function with performance optimizations
def find_film_by_id(collection, id_value, projection=None):
    """Find film by ID with optimized query approach"""
    # Default projection - only return necessary fields
    if projection is None:
        projection = {
            "_id": 1, "id": 1, "title": 1, "poster_path": 1, 
            "description": 1, "rating": 1, "genre_ids": 1, 
            "release_year": 1, "video_url": 1, "source_film": 1, "length": 1
        }
    
    film = None
    
    # Try as numeric ID first (most common case)
    if isinstance(id_value, (int, str)) and str(id_value).isdigit():
        film = collection.find_one({"id": int(id_value)}, projection)
        if film:
            return film
    
    # Then try as ObjectId 
    try:
        if isinstance(id_value, str) and len(id_value) == 24:
            film = collection.find_one({"_id": ObjectId(id_value)}, projection)
            if film:
                return film
    except:
        pass
    
    # Last try as string ID
    return collection.find_one({"id": id_value}, projection)

# User finding function with caching
@lru_cache(maxsize=512)
def find_user_by_id(collection, user_id):
    """Find user by ID with cache for frequently accessed users"""
    # Try ObjectId first
    try:
        if isinstance(user_id, str) and len(user_id) == 24:
            user = collection.find_one({'_id': ObjectId(user_id)})
            if user:
                return serialize_id(user)
    except:
        pass
        
    # Try numeric ID
    try:
        if isinstance(user_id, (int, str)) and str(user_id).isdigit():
            user_id_int = int(user_id)
            user = collection.find_one({'id': user_id_int})
            if user:
                return serialize_id(user)
    except:
        pass
        
    return None

# Cache for genres - rarely changes
_genres_cache = None
_genres_cache_time = 0
_genres_cache_lock = threading.Lock()

def get_all_genres(collection, max_age_seconds=3600):
    """Get all genres with efficient caching strategy"""
    global _genres_cache, _genres_cache_time
    
    current_time = time.time()
    
    # Check if cache is still valid
    if _genres_cache is not None and (current_time - _genres_cache_time) < max_age_seconds:
        return _genres_cache
    
    # Need to refresh cache with thread safety
    with _genres_cache_lock:
        # Double-check in case another thread updated the cache
        if _genres_cache is not None and (current_time - _genres_cache_time) < max_age_seconds:
            return _genres_cache
            
        try:
            _genres_cache = list(collection.find().sort("name", 1))
            _genres_cache_time = current_time
            return _genres_cache
        except Exception as e:
            logger.error(f"Error fetching genres: {e}")
            # Return empty list or current cache if available
            return _genres_cache or []

# Cache for top films - changes occasionally
_top_films_cache = None
_top_films_cache_time = 0
_top_films_cache_lock = threading.Lock()

def get_top_films(collection, limit=10, max_age_seconds=900):
    """Get top rated films with efficient caching"""
    global _top_films_cache, _top_films_cache_time
    
    current_time = time.time()
    
    # Check if cache is still valid
    if _top_films_cache is not None and (current_time - _top_films_cache_time) < max_age_seconds:
        return _top_films_cache[:limit]  # Return requested limit from cache
    
    # Need to refresh cache with thread safety
    with _top_films_cache_lock:
        # Double-check in case another thread updated the cache
        if _top_films_cache is not None and (current_time - _top_films_cache_time) < max_age_seconds:
            return _top_films_cache[:limit]
            
        try:
            # Fetch more than needed for cache efficiency
            max_cache_size = max(20, limit * 2)
            
            # Use projection to limit fields - much faster
            projection = {
                "id": 1, "title": 1, "poster_path": 1, "rating": 1, 
                "release_year": 1, "description": 1, "genre_ids": 1
            }
            
            _top_films_cache = list(collection.find({}, projection).sort("rating", -1).limit(max_cache_size))
            _top_films_cache_time = current_time
            
            # Return just what was requested
            return _top_films_cache[:limit]
        except Exception as e:
            logger.error(f"Error fetching top films: {e}")
            # Return empty list or current cache if available
            return (_top_films_cache or [])[:limit]
