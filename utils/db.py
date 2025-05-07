import os
from pymongo import MongoClient
import ssl
import functools
import time
from datetime import datetime, timedelta

# Connection pool - global client to reuse connections
_mongo_client = None

def get_db_name():
    """Get the database name from environment variables or use default"""
    # Always use the Atlas database name
    return os.environ.get('MONGO_DBNAME', "film-users")

def get_mongo_client():
    """Get MongoDB client for Atlas connection with connection pooling"""
    global _mongo_client
    
    # Return existing client if already connected
    if _mongo_client is not None:
        try:
            # Verify connection is still alive
            _mongo_client.admin.command('ping')
            return _mongo_client
        except Exception:
            # Connection lost, reset client to reconnect
            _mongo_client = None
    
    try:
        # Only use cloud connection with optimized settings
        uri = os.environ.get('MONGO_URI', 
              "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
        
        # Improved connection settings for better performance
        _mongo_client = MongoClient(
            uri,
            serverSelectionTimeoutMS=3000,  # Reduced timeout for faster failure detection
            connectTimeoutMS=3000,          # Timeout for connection establishment
            socketTimeoutMS=10000,
            maxPoolSize=20,                 # Optimal pool size for typical web traffic
            minPoolSize=5,                  # Keep minimum connections in pool
            maxIdleTimeMS=30000,            # Close idle connections after 30 seconds
            ssl=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=True,
            appname="phim-neu-app",
            waitQueueTimeoutMS=1000         # Fast failure if queue wait is too long
        )
        
        # Test connection
        _mongo_client.admin.command('ping')
        print("Connected to MongoDB Atlas")
        return _mongo_client
    except Exception as e:
        print(f"MongoDB Atlas connection error: {str(e)}")
        
        # As a fallback, create a minimal client that won't crash the application
        class MinimalClient:
            def __getitem__(self, key):
                return MinimalDB()
            def close(self):
                pass
            def admin(self):
                class Admin:
                    def command(self, cmd):
                        return {"ok": 1}
                return Admin()
            
        class MinimalDB:
            def __getattr__(self, name):
                return MinimalCollection()
                
        class MinimalCollection:
            def find_one(self, *args, **kwargs): return None
            def find(self, *args, **kwargs): 
                class MinimalCursor:
                    def sort(self, *args): return self
                    def limit(self, *args): return []
                    def skip(self, *args): return self
                    def projection(self, *args): return self
                return MinimalCursor()
            def count_documents(self, *args, **kwargs): return 0
            def insert_one(self, *args, **kwargs): return type('obj', (object,), {'inserted_id': 'dummy_id'})
            def update_one(self, *args, **kwargs): return None
            def delete_one(self, *args, **kwargs): return None
            def create_index(self, *args, **kwargs): return None
            
        return MinimalClient()

# Simple cache implementation
_cache = {}
_cache_ttl = {}

def cache_data(key, data, ttl_seconds=300):
    """Cache data with expiration time"""
    _cache[key] = data
    _cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)

def get_cached_data(key):
    """Get data from cache if valid"""
    if key in _cache and key in _cache_ttl:
        if datetime.now() < _cache_ttl[key]:
            return _cache[key]
        else:
            # Expired, remove from cache
            del _cache[key]
            del _cache_ttl[key]
    return None

def clear_cache():
    """Clear all cached data"""
    _cache.clear()
    _cache_ttl.clear()

def cached_query(ttl_seconds=300):
    """Decorator for caching MongoDB query results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = get_cached_data(key)
            if cached_result is not None:
                return cached_result
            
            # Execute query and cache result
            result = func(*args, **kwargs)
            cache_data(key, result, ttl_seconds)
            return result
        return wrapper
    return decorator

def migrate_users_without_id(db):
    """Reassign all user IDs to be sequential natural numbers (1, 2, 3, ...)"""
    try:
        # Quick check if migration is needed - faster than retrieving all documents
        count_users_without_id = db.users.count_documents({"id": {"$exists": False}})
        
        if count_users_without_id == 0:
            print("No users found without IDs")
            return True
            
        # Only retrieve the documents if necessary
        all_users = list(db.users.find(
            {"id": {"$exists": False}},  # Only migrate users without ID
            {"_id": 1, "registerDate": 1}  # Project only needed fields
        ).sort("registerDate", 1))  # Sort by registration date
        
        print(f"Reassigning sequential IDs to {len(all_users)} users...")
        
        # Find current highest ID
        highest_user = db.users.find_one(
            {"id": {"$exists": True}},
            sort=[("id", -1)]
        )
        
        start_id = (highest_user.get("id", 0) + 1) if highest_user else 1
        
        # Bulk update for better performance
        bulk_operations = []
        for i, user in enumerate(all_users, start=start_id):
            bulk_operations.append(
                {
                    "filter": {"_id": user["_id"]},
                    "update": {"$set": {"id": i}}
                }
            )
            
            # Process in batches of 500 to avoid memory issues
            if len(bulk_operations) >= 500:
                for op in bulk_operations:
                    db.users.update_one(op["filter"], op["update"])
                bulk_operations = []
                
        # Process any remaining updates
        for op in bulk_operations:
            db.users.update_one(op["filter"], op["update"])
            
        print(f"✅ Successfully reassigned IDs for {len(all_users)} users")
        return True
    except Exception as e:
        print(f"Error during user ID migration: {str(e)}")
        return False  # Explicitly return False on error
